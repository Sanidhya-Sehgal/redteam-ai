"""
fake_llm.py — Deterministic Fake LLM for offline RedTeam-AI demos
==================================================================
Simulates a ReAct-style LLM that:
  1. Calls NmapScanner
  2. Calls SQLInjectionTester
  3. Calls WeakAuthChecker
  4. Returns a structured Final Answer

No API key needed. Perfect for local demos and CI testing.
"""

from langchain_core.language_models.llms import LLM
from langchain_core.outputs import LLMResult, Generation
from typing import Any, List, Optional


class FakeRedTeamLLM(LLM):
    """
    A scripted LLM that drives the ReAct loop deterministically.
    Each call() advances through a pre-planned sequence of actions.
    """

    # Internal step counter to track where we are in the script
    _step: int = 0

    class Config:
        # Allow arbitrary types (needed for mutable state)
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "fake_redteam_llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """
        Returns the next scripted ReAct action based on current step.
        The ReAct agent calls this repeatedly until 'Final Answer' is produced.
        """
        self._step += 1

        # Extract target from prompt for use in Final Answer
        target = "http://testphp.vulnweb.com"  # default
        import re
        match = re.search(r'Question:\s*(https?://[^\s\n]+)', prompt)
        if match:
            target = match.group(1).strip()

        # ── Step 1: Port scan ──────────────────────────────────────
        if self._step == 1:
            return (
                "I need to start by discovering open ports and services on the target. "
                "I'll use the NmapScanner first.\n"
                "Action: NmapScanner\n"
                f"Action Input: {target}"
            )

        # ── Step 2: SQL injection test ─────────────────────────────
        elif self._step == 2:
            return (
                "Port scan complete. I can see HTTP is running on port 80. "
                "Now I should test for SQL injection vulnerabilities.\n"
                "Action: SQLInjectionTester\n"
                f"Action Input: {target}?id=1"
            )

        # ── Step 3: Auth check ─────────────────────────────────────
        elif self._step == 3:
            return (
                "SQL injection test done. I found potential vulnerabilities. "
                "Let me now check for weak authentication and exposed admin panels.\n"
                "Action: WeakAuthChecker\n"
                f"Action Input: {target}"
            )

        # ── Step 4: Compile final report ───────────────────────────
        else:
            return (
                "I now have results from all three tools. "
                "The target has open HTTP/HTTPS ports, SQL injection vulnerabilities, "
                "default credentials, and missing security headers. Risk is High.\n"
                "Final Answer: "
                '{"target": "' + target + '", '
                '"open_ports": [80, 443, 8080], '
                '"vulnerabilities": ['
                '{"type": "SQL Injection", "endpoint": "' + target + '?id=1", '
                '"payload": "1\' AND 1=1--", "severity": "High"}, '
                '{"type": "Default Credentials", "detail": "admin:admin works on /login.php", "severity": "High"}, '
                '{"type": "Missing Security Headers", "detail": "CSP, X-Frame-Options absent", "severity": "Medium"}'
                '], "risk_level": "High"}'
            )

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs
    ) -> LLMResult:
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop=stop)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)
