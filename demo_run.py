"""
demo_run.py — Standalone demo (no LangChain/OpenAI needed)
==========================================================
Simulates the full agent reasoning trace and produces the
JSON report. Use this to understand the flow before installing deps.

Run with: python demo_run.py
"""

import json
import time

# ── Import our tool functions directly ────────────────────────────
from agent import nmap_scanner, sql_injection_tester, weak_auth_checker, calculate_risk

TARGET = "http://testphp.vulnweb.com"

# ANSI colors for terminal output
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def print_step(step: int, thought: str, action: str, action_input: str, observation: dict):
    print(f"\n{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}[Step {step}]{RESET}")
    print(f"{YELLOW}Thought:{RESET}  {thought}")
    print(f"{YELLOW}Action:{RESET}   {action}")
    print(f"{YELLOW}Input:{RESET}    {action_input}")
    print(f"{GREEN}Observation:{RESET}")
    print(json.dumps(observation, indent=4))
    time.sleep(0.4)  # Slight delay for readability

def main():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{RED}{BOLD}  🔴 RedTeam-AI — Autonomous Penetration Testing Agent{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  Target: {TARGET}\n")

    all_vulnerabilities = []
    open_ports = []

    # ── STEP 1: Nmap Scan ──────────────────────────────────────────
    nmap_result = json.loads(nmap_scanner(TARGET))
    open_ports = nmap_result["open_ports"]
    print_step(
        step=1,
        thought="I should start by discovering the attack surface. Let me scan open ports and services.",
        action="NmapScanner",
        action_input=TARGET,
        observation=nmap_result
    )

    # ── STEP 2: SQL Injection ──────────────────────────────────────
    sqli_result = json.loads(sql_injection_tester(TARGET + "?id=1"))
    if sqli_result.get("status") == "VULNERABLE":
        all_vulnerabilities.extend(sqli_result.get("findings", []))
    print_step(
        step=2,
        thought="HTTP is running on port 80. The URL pattern suggests dynamic pages. Let me test for SQL injection.",
        action="SQLInjectionTester",
        action_input=TARGET + "?id=1",
        observation=sqli_result
    )

    # ── STEP 3: Auth Check ─────────────────────────────────────────
    auth_result = json.loads(weak_auth_checker(TARGET))
    all_vulnerabilities.extend(auth_result.get("findings", []))
    print_step(
        step=3,
        thought="SQL injection confirmed. Now let me check for weak credentials and misconfigurations.",
        action="WeakAuthChecker",
        action_input=TARGET,
        observation=auth_result
    )

    # ── FINAL REPORT ───────────────────────────────────────────────
    risk = calculate_risk(all_vulnerabilities)
    report = {
        "target": TARGET,
        "open_ports": open_ports,
        "vulnerabilities": all_vulnerabilities,
        "risk_level": risk
    }

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{RED}{BOLD}  📋 FINAL SECURITY REPORT{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(json.dumps(report, indent=2))

    with open("report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n{GREEN}✅ Report saved to report.json{RESET}")

if __name__ == "__main__":
    main()
