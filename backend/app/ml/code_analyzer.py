"""Code analyzer - inspects source code for malicious patterns."""

from __future__ import annotations

import ast
import re
from typing import Any

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.models.analysis import DetectionResult
from app.utils.constants import SUSPICIOUS_CODE_PATTERNS

logger = setup_logger(__name__)


PATTERN_RISK = {
    r"\beval\s*\(": ("Dynamic code execution", 15),
    r"\bexec\s*\(": ("Shell command execution", 20),
    r"\bsubprocess\.\w+\s*\(": ("Subprocess invocation", 20),
    r"\bos\.system\s*\(": ("OS command execution", 20),
    r"\bos\.popen\s*\(": ("OS pipe execution", 18),
    r"\bbase64\.b64decode\s*\(": ("Base64 decoding (obfuscation)", 12),
    r"\batob\s*\(": ("Base64 decode (JS)", 10),
    r"\brequests\.\w+\s*\(": ("HTTP request (exfiltration risk)", 8),
    r"\burllib\.request\.\w+\s*\(": ("HTTP request via urllib", 8),
    r"\bhttp\.get\s*\(": ("HTTP GET request", 6),
    r"\bhttp\.request\s*\(": ("HTTP request", 6),
    r"\bfetch\s*\(": ("Fetch API call", 5),
    r"\b__import__\s*\(": ("Dynamic import", 15),
    r"\bimportlib\.import_module\s*\(": ("Dynamic module import", 15),
    r"\bfs\.writeFileSync\s*\(": ("Synchronous file write", 12),
    r"\bchild_process\.\w+\s*\(": ("Child process creation", 20),
}

# Additional high-signal patterns not in the constants file
EXTRA_PATTERNS = {
    r"curl\s+.*\|\s*sh": ("Pipe-to-shell command", 25),
    r"wget\s+.*\|\s*sh": ("Wget pipe-to-shell", 25),
    r"crypto\.createCipher": ("Cryptographic operations", 10),
    r"socket\.connect": ("Socket connection", 12),
    r"\.env": ("Environment file access", 8),
    r"process\.env": ("Environment variable access", 5),
    r"npm\s+publish": ("npm publish in code", 15),
}

PYTHON_AST_RISK = {
    "eval": ("python_eval_call", 20),
    "exec": ("python_exec_call", 20),
    "os.system": ("python_os_system", 20),
    "os.popen": ("python_os_popen", 18),
    "subprocess.run": ("python_subprocess_run", 20),
    "subprocess.Popen": ("python_subprocess_popen", 22),
    "__import__": ("python_dynamic_import", 15),
    "importlib.import_module": ("python_importlib_dynamic", 15),
    "requests.get": ("python_network_request", 8),
    "requests.post": ("python_network_request", 8),
    "urllib.request.urlopen": ("python_urlopen", 8),
}

PYTHON_IMPORT_RISK = {
    "subprocess": ("python_subprocess_import", 12),
    "socket": ("python_socket_import", 10),
    "requests": ("python_requests_import", 6),
    "importlib": ("python_importlib_import", 6),
}

JS_STRUCTURAL_PATTERNS = [
    (re.compile(r"require\(['\"]child_process['\"]\)", re.I), "js_child_process_require", 20),
    (re.compile(r"import\s+.*from\s+['\"]child_process['\"]", re.I), "js_child_process_import", 20),
    (re.compile(r"new\s+Function\s*\(", re.I), "js_dynamic_function_ctor", 15),
    (re.compile(r"XMLHttpRequest\s*\(", re.I), "js_xhr_usage", 8),
]


class CodeAnalyzer(BaseDetector):
    """Scan source code for suspicious patterns and, optionally, run CodeBERT."""

    name = "code_analysis"
    version = "1.0.0"
    weight = 0.35

    def __init__(self) -> None:
        super().__init__()
        self._model = None
        self._tokenizer = None
        self._tokenizer_source = None
        self._is_ready = True
        self._compiled_patterns = self._compile_patterns()

    def _load_tokenizer_with_fallback(self, model_path: "Path"):
        from transformers import AutoTokenizer

        attempts = [
            (
                "local-fast",
                {
                    "pretrained_model_name_or_path": str(model_path),
                    "local_files_only": True,
                },
            ),
            (
                "local-slow",
                {
                    "pretrained_model_name_or_path": str(model_path),
                    "local_files_only": True,
                    "use_fast": False,
                },
            ),
            (
                "base-slow-cached",
                {
                    "pretrained_model_name_or_path": "microsoft/codebert-base",
                    "local_files_only": True,
                    "use_fast": False,
                },
            ),
            (
                "base-slow-download",
                {
                    "pretrained_model_name_or_path": "microsoft/codebert-base",
                    "local_files_only": False,
                    "use_fast": False,
                },
            ),
        ]

        last_error = None
        for source, kwargs in attempts:
            try:
                tokenizer = AutoTokenizer.from_pretrained(**kwargs)
                self._tokenizer_source = source
                return tokenizer
            except Exception as exc:
                last_error = exc

        raise RuntimeError(
            "No compatible tokenizer could be loaded for CodeBERT"
        ) from last_error

    def _compile_patterns(self) -> list[tuple[re.Pattern, str, int]]:
        compiled = []
        all_patterns = {**PATTERN_RISK, **EXTRA_PATTERNS}
        for pattern, (desc, weight) in all_patterns.items():
            try:
                compiled.append((re.compile(pattern, re.IGNORECASE), desc, weight))
            except re.error as exc:
                logger.warning("Bad regex pattern %r: %s", pattern, exc)
        return compiled

    def load_model(self) -> None:
        try:
            from pathlib import Path

            from transformers import AutoModelForSequenceClassification
            from app.config import get_settings

            model_path = Path(get_settings().codebert_model_path)
            if not model_path.exists():
                logger.info("CodeBERT path %s not found — using pattern + AST analysis", model_path)
                self._model = None
                self._tokenizer = None
                self._tokenizer_source = None
                return

            self._model = AutoModelForSequenceClassification.from_pretrained(str(model_path), local_files_only=True)
            self._tokenizer = self._load_tokenizer_with_fallback(model_path)
            self._model.eval()
            logger.info(
                "CodeBERT model loaded from %s (tokenizer source=%s)",
                model_path,
                self._tokenizer_source,
            )
        except Exception as exc:
            logger.info(
                "CodeBERT not available (%s) — falling back to pattern matching only",
                exc,
            )
            self._model = None
            self._tokenizer = None
            self._tokenizer_source = None

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        code: str = kwargs.get("code", "")
        if not code or not code.strip():
            return DetectionResult(
                score=0.0,
                confidence=1.0,
                evidence={"note": "No code provided for analysis"},
            )

        # regex pattern matching
        findings = self._pattern_scan(code)
        pattern_score = self._calculate_pattern_score(findings)
        ast_findings = self._ast_scan(code)
        ast_score = self._calculate_ast_score(ast_findings)

        static_score = min(pattern_score + ast_score, 100.0)

        # CodeBERT inference (if model is loaded)
        ml_score = 0.0
        ml_confidence = 0.0
        if self._model is not None and self._tokenizer is not None:
            ml_score, ml_confidence = self._run_codebert(code)

        # blend ML + patterns if model available
        if self._model is not None:
            combined_score = static_score * 0.4 + ml_score * 0.6
            combined_confidence = ml_confidence
        else:
            combined_score = static_score
            combined_confidence = 0.7 if findings or ast_findings else 0.9

        combined_score = min(combined_score, 100.0)

        return DetectionResult(
            score=round(combined_score, 2),
            confidence=round(combined_confidence, 3),
            evidence={
                "suspicious_patterns": findings,
                "ast_findings": ast_findings,
                "total_findings": len(findings),
                "ast_total_findings": len(ast_findings),
                "pattern_score": round(pattern_score, 2),
                "ast_score": round(ast_score, 2),
                "ml_score": round(ml_score, 2) if self._model else None,
                "model_available": self._model is not None,
            },
        )

    def _pattern_scan(self, code: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = code.split("\n")

        for lineno, line in enumerate(lines, start=1):
            for pattern, description, risk_weight in self._compiled_patterns:
                if pattern.search(line):
                    findings.append({
                        "line": lineno,
                        "pattern": description,
                        "risk_weight": risk_weight,
                        "matched_text": line.strip()[:120],
                    })

        return findings

    @staticmethod
    def _calculate_pattern_score(findings: list[dict[str, Any]]) -> float:
        if not findings:
            return 0.0
        total = sum(f["risk_weight"] for f in findings)
        return min(total, 100.0)

    @staticmethod
    def _calculate_ast_score(findings: list[dict[str, Any]]) -> float:
        if not findings:
            return 0.0
        total = sum(float(f.get("risk_weight", 0) or 0) for f in findings)
        return min(total, 100.0)

    def _ast_scan(self, code: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        findings.extend(self._ast_scan_python(code))
        findings.extend(self._ast_like_scan_javascript(code))
        return findings

    def _ast_scan_python(self, code: str) -> list[dict[str, Any]]:
        try:
            tree = ast.parse(code)
        except Exception:
            return []

        findings: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._resolve_python_call_name(node.func)
                if call_name in PYTHON_AST_RISK:
                    finding_type, risk_weight = PYTHON_AST_RISK[call_name]
                    findings.append({
                        "type": finding_type,
                        "line": getattr(node, "lineno", 0),
                        "risk_weight": risk_weight,
                        "detail": call_name,
                    })

            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = (alias.name or "").split(".")[0]
                    if module_name in PYTHON_IMPORT_RISK:
                        finding_type, risk_weight = PYTHON_IMPORT_RISK[module_name]
                        findings.append({
                            "type": finding_type,
                            "line": getattr(node, "lineno", 0),
                            "risk_weight": risk_weight,
                            "detail": module_name,
                        })

            if isinstance(node, ast.ImportFrom):
                module_name = (node.module or "").split(".")[0]
                if module_name in PYTHON_IMPORT_RISK:
                    finding_type, risk_weight = PYTHON_IMPORT_RISK[module_name]
                    findings.append({
                        "type": finding_type,
                        "line": getattr(node, "lineno", 0),
                        "risk_weight": risk_weight,
                        "detail": module_name,
                    })

        return findings

    def _ast_like_scan_javascript(self, code: str) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = code.split("\n")

        for lineno, line in enumerate(lines, start=1):
            for pattern, finding_type, risk_weight in JS_STRUCTURAL_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "type": finding_type,
                        "line": lineno,
                        "risk_weight": risk_weight,
                        "detail": line.strip()[:120],
                    })

        return findings

    def _resolve_python_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            left = self._resolve_python_call_name(node.value)
            if left:
                return f"{left}.{node.attr}"
            return node.attr

        return ""

    def _run_codebert(self, code: str) -> tuple[float, float]:
        try:
            import torch

            inputs = self._tokenizer(
                code[:512],  # CodeBERT has a 512-token limit
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                # Assume label 1 = malicious
                malicious_prob = probs[0][1].item()
                return malicious_prob * 100, malicious_prob
        except Exception as exc:
            logger.warning("CodeBERT inference failed: %s", exc)
            return 0.0, 0.0
