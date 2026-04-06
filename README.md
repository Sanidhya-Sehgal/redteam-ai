# 🔴 RedTeam-AI — Autonomous Penetration Testing Agent

An **agentic AI** system built with LangChain's ReAct framework that autonomously performs penetration testing workflows.

---

## 🏗️ Architecture

```
User Input (target URL)
        │
        ▼
┌─────────────────────────────────────────┐
│         LangChain ReAct Agent           │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  LLM (GPT-4o-mini / FakeLLM)    │   │
│  │  Reasoning Engine                │   │
│  └──────────┬───────────────────────┘   │
│             │ Thought → Action loop     │
│  ┌──────────▼───────────────────────┐   │
│  │         Tool Dispatcher          │   │
│  └──┬──────────┬────────────────┬───┘   │
│     │          │                │       │
│     ▼          ▼                ▼       │
│ NmapScanner SQLiTester   AuthChecker    │
│  (ports)   (injection)  (credentials)  │
└─────────────────────┬───────────────────┘
                      │
                      ▼
             JSON Security Report
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **ReAct Agent** | `agent.py` | Drives the reasoning loop |
| **Nmap Tool** | `agent.py:nmap_scanner()` | Port discovery |
| **SQLi Tool** | `agent.py:sql_injection_tester()` | Injection testing |
| **Auth Tool** | `agent.py:weak_auth_checker()` | Credential auditing |
| **Fake LLM** | `fake_llm.py` | Offline demo without API key |
| **Demo Runner** | `demo_run.py` | Standalone walkthrough |

---

## 🚀 Quick Start

### Option A — Offline Demo (no API key needed)
```bash
pip install -r requirements.txt
python demo_run.py
```

### Option B — Full Agent with FakeLLM
```bash
python agent.py --target http://testphp.vulnweb.com
```

### Option C — Full Agent with OpenAI
```bash
python agent.py --target http://testphp.vulnweb.com --openai-key sk-...
```

---

## 📋 Sample Output

```json
{
  "target": "http://testphp.vulnweb.com",
  "open_ports": [80, 443, 8080],
  "vulnerabilities": [
    {
      "type": "SQL Injection",
      "endpoint": "http://testphp.vulnweb.com/artists.php?artist=1",
      "payload": "1' AND 1=1--",
      "evidence": "Error-based SQLi: MySQL syntax error exposed"
    },
    {
      "type": "Default Credentials",
      "detail": "Login succeeded with admin:admin on /login.php",
      "severity": "High"
    },
    {
      "type": "Missing Security Headers",
      "detail": "Headers absent: X-Frame-Options, Content-Security-Policy, X-XSS-Protection",
      "severity": "Medium"
    }
  ],
  "risk_level": "High"
}
```

---

## 🧠 How ReAct Works

**ReAct = Reasoning + Acting**

The agent alternates between:
1. **Thought** — "I need to check open ports first"
2. **Action** — Calls `NmapScanner` tool
3. **Observation** — Receives tool output
4. Repeats until enough info to write Final Answer

This loop is visible in verbose output when running `agent.py`.

---

## 🔧 Extending the Project

Add a new tool in 3 steps:

```python
# 1. Write the function
def xss_tester(target: str) -> str:
    # your logic
    return json.dumps({"findings": []})

# 2. Wrap it
Tool(name="XSSTester", func=xss_tester, description="Tests for XSS...")

# 3. Add to tools list
tools = [nmap_tool, sqli_tool, auth_tool, xss_tool]
```

---

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Only test systems you own or have explicit written permission to test.
