"""
Code Analyzer — inspects raw source code for malicious patterns.

How it works (two-phase approach):
  Phase A: Regex-based pattern matching against known suspicious APIs
           (eval, exec, child_process, base64, crypto-mining, etc.)
  Phase B: Optional CodeBERT transformer model for deeper semantic
           analysis (only runs if the model weights are present).

The two phases are combined into a single score.  Phase A is always
available; Phase B gracefully degrades to a no-op when the model
hasn't been fine-tuned yet.

Classes:
    CodeAnalyzer(BaseDetector)

Usage:
    analyzer = CodeAnalyzer()
    result = await analyzer.run(code="const exec = require('child_process')...")
"""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.models.analysis import DetectionResult
from app.utils.constants import SUSPICIOUS_CODE_PATTERNS

logger = setup_logger(__name__)


# Weights assigned to each pattern category
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


class CodeAnalyzer(BaseDetector):
    """Scan source code for suspicious patterns and, optionally, run CodeBERT."""

    name = "code_analysis"
    version = "1.0.0"
    weight = 0.35

    def __init__(self) -> None:
        super().__init__()
        self._model = None
        self._tokenizer = None
        self._is_ready = True  # Pattern matching is always available
        self._compiled_patterns = self._compile_patterns()

    # ------------------------------------------------------------------
    # Pattern compilation
    # ------------------------------------------------------------------

    def _compile_patterns(self) -> list[tuple[re.Pattern, str, int]]:
        """Pre-compile all regex patterns for speed."""
        compiled = []
        all_patterns = {**PATTERN_RISK, **EXTRA_PATTERNS}
        for pattern, (desc, weight) in all_patterns.items():
            try:
                compiled.append((re.compile(pattern, re.IGNORECASE), desc, weight))
            except re.error as exc:
                logger.warning("Bad regex pattern %r: %s", pattern, exc)
        return compiled

    # ------------------------------------------------------------------
    # Model loading (optional CodeBERT)
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Try to load CodeBERT for semantic analysis. Not fatal if missing."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            from app.config import get_settings

            model_path = get_settings().codebert_model_path
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            self._model = AutoModelForSequenceClassification.from_pretrained(model_path)
            logger.info("CodeBERT model loaded from %s", model_path)
        except Exception as exc:
            logger.info(
                "CodeBERT not available (%s) — falling back to pattern matching only",
                exc,
            )
            self._model = None
            self._tokenizer = None

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        """
        Analyse source *code* for malicious indicators.

        Keyword Args:
            code (str): Raw source code to inspect.

        Returns:
            DetectionResult with score based on pattern matches.
        """
        code: str = kwargs.get("code", "")
        if not code or not code.strip():
            return DetectionResult(
                score=0.0,
                confidence=1.0,
                evidence={"note": "No code provided for analysis"},
            )

        # Phase A — Regex pattern matching
        findings = self._pattern_scan(code)
        pattern_score = self._calculate_pattern_score(findings)

        # Phase B — CodeBERT inference (if model is loaded)
        ml_score = 0.0
        ml_confidence = 0.0
        if self._model is not None and self._tokenizer is not None:
            ml_score, ml_confidence = self._run_codebert(code)

        # Combine: if ML is available use weighted blend, otherwise patterns only
        if self._model is not None:
            combined_score = pattern_score * 0.4 + ml_score * 0.6
            combined_confidence = ml_confidence
        else:
            combined_score = pattern_score
            # Confidence drops a bit without the ML model
            combined_confidence = 0.7 if findings else 0.9

        combined_score = min(combined_score, 100.0)

        return DetectionResult(
            score=round(combined_score, 2),
            confidence=round(combined_confidence, 3),
            evidence={
                "suspicious_patterns": findings,
                "total_findings": len(findings),
                "pattern_score": round(pattern_score, 2),
                "ml_score": round(ml_score, 2) if self._model else None,
                "model_available": self._model is not None,
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pattern_scan(self, code: str) -> list[dict[str, Any]]:
        """Run every compiled regex against the code, track line numbers."""
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
        """Sum risk weights, cap at 100."""
        if not findings:
            return 0.0
        total = sum(f["risk_weight"] for f in findings)
        return min(total, 100.0)

    def _run_codebert(self, code: str) -> tuple[float, float]:
        """
        Run inference through the loaded CodeBERT model.
        Returns (score_0_100, confidence_0_1).
        """
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
