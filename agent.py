"""
RedTeam-AI: Autonomous Penetration Testing Agent
=================================================
Architecture:
  - LangChain ReAct Agent drives reasoning loop
  - 3 mock security tools: Nmap, SQLi tester, Auth checker
  - Structured JSON report generated at the end

Usage:
  python agent.py --target http://example.com
"""

import json
import re
import argparse
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# ─────────────────────────────────────────────
# TOOL 1: Nmap Port Scanner (simulated)
# ─────────────────────────────────────────────
def nmap_scanner(target: str) -> str:
    """
    Simulates an Nmap scan against a target.
    In a real scenario, this would shell out to:
        subprocess.run(["nmap", "-sV", target], capture_output=True)
    Returns a JSON string describing open ports & services.
    """
    # Mock results keyed by domain keyword for demo realism
    mock_results = {
        "testphp.vulnweb.com": {"open_ports": [80, 443, 8080], "services": {"80": "HTTP/Apache 2.4", "443": "HTTPS", "8080": "HTTP-Proxy"}},
        "dvwa":                {"open_ports": [80, 3306],       "services": {"80": "HTTP/Apache", "3306": "MySQL 5.7"}},
        "localhost":           {"open_ports": [22, 80, 5432],   "services": {"22": "SSH/OpenSSH", "80": "HTTP/nginx", "5432": "PostgreSQL"}},
    }

    # Pick a matching mock or fall back to a generic result
    for key, data in mock_results.items():
        if key in target:
            return json.dumps(data)

    # Generic fallback
    return json.dumps({
        "open_ports": [80, 443],
        "services": {"80": "HTTP", "443": "HTTPS"}
    })


# ─────────────────────────────────────────────
# TOOL 2: SQL Injection Tester (mock heuristic)
# ─────────────────────────────────────────────
def sql_injection_tester(target: str) -> str:
    """
    Simulates basic SQL injection probing.
    In a real scenario this would use sqlmap or custom payloads:
        payloads = ["' OR '1'='1", "'; DROP TABLE users;--", '" OR 1=1--']
    Returns a JSON string with findings.
    """
    vulnerabilities = []

    # Heuristic: targets with query params or known-vuln domains are flagged
    if "?" in target or "id=" in target or "page=" in target:
        vulnerabilities.append({
            "type": "SQL Injection",
            "endpoint": target,
            "payload": "' OR '1'='1",
            "evidence": "Application returned unexpected data rows"
        })

    if "vulnweb" in target or "dvwa" in target or "testphp" in target:
        vulnerabilities.append({
            "type": "SQL Injection",
            "endpoint": target + "/artists.php?artist=1",
            "payload": "1' AND 1=1--",
            "evidence": "Error-based SQLi: MySQL syntax error exposed in response"
        })

    if not vulnerabilities:
        return json.dumps({"status": "No SQL injection vulnerabilities detected", "tested_payloads": 12})

    return json.dumps({"status": "VULNERABLE", "findings": vulnerabilities})


# ─────────────────────────────────────────────
# TOOL 3: Weak Authentication Checker
# ─────────────────────────────────────────────
def weak_auth_checker(target: str) -> str:
    """
    Checks for weak/default credentials and auth misconfigs.
    Real implementation would attempt logins with a credential wordlist
    and check for missing security headers.
    Returns a JSON string with auth findings.
    """
    findings = []

    # Simulate checking common admin panels
    common_paths = ["/admin", "/login", "/wp-admin", "/phpmyadmin"]
    exposed_panels = []

    if "vulnweb" in target or "dvwa" in target:
        exposed_panels = ["/login.php", "/admin/"]
        findings.append({
            "type": "Default Credentials",
            "detail": "Login succeeded with admin:admin on /login.php",
            "severity": "High"
        })

    # Simulate missing security headers check
    missing_headers = ["X-Frame-Options", "Content-Security-Policy", "X-XSS-Protection"]
    findings.append({
        "type": "Missing Security Headers",
        "detail": f"Headers absent: {', '.join(missing_headers)}",
        "severity": "Medium"
    })

    # Flag if SSH is likely on port 22 (from nmap hint in target)
    if "22" in target or "ssh" in target.lower():
        findings.append({
            "type": "SSH Password Auth Enabled",
            "detail": "SSH allows password-based login; brute-force risk",
            "severity": "Medium"
        })

    return json.dumps({
        "exposed_panels": exposed_panels,
        "findings": findings
    })


# ─────────────────────────────────────────────
# LANGCHAIN TOOL WRAPPERS
# ─────────────────────────────────────────────
tools = [
    Tool(
        name="NmapScanner",
        func=nmap_scanner,
        description=(
            "Scans a target URL/IP for open ports and running services. "
            "Input: target URL or IP address. "
            "Output: JSON with open_ports list and services dict."
        )
    ),
    Tool(
        name="SQLInjectionTester",
        func=sql_injection_tester,
        description=(
            "Tests a target URL for SQL injection vulnerabilities using common payloads. "
            "Input: target URL (include query params if any, e.g. http://site.com/page?id=1). "
            "Output: JSON with vulnerability findings or clean status."
        )
    ),
    Tool(
        name="WeakAuthChecker",
        func=weak_auth_checker,
        description=(
            "Checks for weak/default credentials, exposed admin panels, and missing security headers. "
            "Input: target URL. "
            "Output: JSON with authentication-related vulnerabilities."
        )
    ),
]


# ─────────────────────────────────────────────
# REACT PROMPT TEMPLATE
# ─────────────────────────────────────────────
REACT_PROMPT = PromptTemplate.from_template("""
You are RedTeam-AI, an expert autonomous penetration testing agent.
Your goal is to perform a structured security assessment of the given target.

You have access to the following tools:
{tools}

Use the following format STRICTLY:

Question: the target URL to assess
Thought: think about what to do next
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to compile the final report
Final Answer: <JSON report>

Rules:
- Always start with NmapScanner to discover the attack surface
- Then run SQLInjectionTester and WeakAuthChecker
- Base risk_level on: High (critical vulns found), Medium (some issues), Low (clean)
- Final Answer MUST be valid JSON matching this schema:
  {{
    "target": "...",
    "open_ports": [...],
    "vulnerabilities": [...],
    "risk_level": "Low|Medium|High"
  }}

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")


# ─────────────────────────────────────────────
# REPORT RISK CALCULATOR
# ─────────────────────────────────────────────
def calculate_risk(vulnerabilities: list) -> str:
    """Determines overall risk level from vulnerability list."""
    if not vulnerabilities:
        return "Low"

    high_keywords = ["SQL Injection", "Default Credentials", "Remote Code"]
    medium_keywords = ["SSH", "Missing Security Headers", "Exposed Panel"]

    for v in vulnerabilities:
        v_str = json.dumps(v).lower()
        if any(k.lower() in v_str for k in high_keywords):
            return "High"

    for v in vulnerabilities:
        v_str = json.dumps(v).lower()
        if any(k.lower() in v_str for k in medium_keywords):
            return "Medium"

    return "Low"


# ─────────────────────────────────────────────
# REPORT BUILDER (fallback parser)
# ─────────────────────────────────────────────
def build_report_from_scratchpad(target: str, scratchpad: str) -> dict:
    """
    Fallback: if the LLM doesn't return clean JSON, we parse
    observations from the agent's scratchpad manually.
    """
    open_ports = []
    vulnerabilities = []

    # Extract port numbers from nmap observations
    ports_match = re.findall(r'"open_ports":\s*\[([^\]]+)\]', scratchpad)
    for match in ports_match:
        open_ports = [int(p.strip()) for p in match.split(",") if p.strip().isdigit()]
        break

    # Extract vulnerability objects from tool outputs
    findings_blocks = re.findall(r'"findings":\s*(\[[^\]]+\])', scratchpad, re.DOTALL)
    for block in findings_blocks:
        try:
            found = json.loads(block)
            vulnerabilities.extend(found)
        except Exception:
            pass

    sqli_blocks = re.findall(r'"findings":\s*(\[[^\]]+\])', scratchpad, re.DOTALL)
    for block in sqli_blocks:
        try:
            found = json.loads(block)
            for f in found:
                if f not in vulnerabilities:
                    vulnerabilities.append(f)
        except Exception:
            pass

    return {
        "target": target,
        "open_ports": open_ports,
        "vulnerabilities": vulnerabilities,
        "risk_level": calculate_risk(vulnerabilities)
    }


# ─────────────────────────────────────────────
# MAIN AGENT RUNNER
# ─────────────────────────────────────────────
def run_redteam_agent(target: str, openai_api_key: str = None) -> dict:
    """
    Initializes and runs the ReAct agent against the target.
    Returns a structured JSON report dict.
    """
    # LLM: use OpenAI if key provided, else use FakeLLM (see fake_llm.py)
    if openai_api_key:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=openai_api_key
        )
    else:
        # Import our deterministic fake LLM for offline demo
        from fake_llm import FakeRedTeamLLM
        llm = FakeRedTeamLLM()

    # Create the ReAct agent
    agent = create_react_agent(llm=llm, tools=tools, prompt=REACT_PROMPT)

    # Wrap with executor (handles the reasoning loop)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,           # Shows step-by-step reasoning trace
        max_iterations=10,      # Safety limit on reasoning steps
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    print(f"\n{'='*60}")
    print(f"  🎯 RedTeam-AI Starting Assessment")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    result = agent_executor.invoke({"input": target})

    # Try to parse Final Answer as JSON
    final_answer = result.get("output", "")
    report = None

    # Strip markdown fences if present
    clean = re.sub(r"```json|```", "", final_answer).strip()
    try:
        report = json.loads(clean)
    except Exception:
        # Fallback: construct report from intermediate steps
        scratchpad = str(result.get("intermediate_steps", ""))
        report = build_report_from_scratchpad(target, scratchpad)

    # Always ensure risk_level is computed correctly
    if "vulnerabilities" in report:
        report["risk_level"] = calculate_risk(report.get("vulnerabilities", []))
    report["target"] = target  # Ensure target is always set

    return report


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RedTeam-AI Penetration Testing Agent")
    parser.add_argument("--target", default="http://testphp.vulnweb.com", help="Target URL to assess")
    parser.add_argument("--openai-key", default=None, help="OpenAI API key (optional; uses FakeLLM if omitted)")
    parser.add_argument("--output", default="report.json", help="Output file for JSON report")
    args = parser.parse_args()

    # Run the agent
    report = run_redteam_agent(target=args.target, openai_api_key=args.openai_key)

    # Pretty print report
    print(f"\n{'='*60}")
    print("  📋 FINAL SECURITY REPORT")
    print(f"{'='*60}")
    print(json.dumps(report, indent=2))

    # Save to file
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Report saved to {args.output}")
