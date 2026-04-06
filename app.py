from flask import Flask, request, jsonify
from agent import run_redteam_agent
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "RedTeam-AI is live. POST to /scan with {target}"

@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    target = data.get("target", "http://testphp.vulnweb.com")
    key = os.getenv("OPENAI_API_KEY", None)
    report = run_redteam_agent(target=target, openai_api_key=key)
    return jsonify(report)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)