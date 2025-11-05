
from flask import Flask, request, jsonify
import os, requests

app = Flask(__name__)

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT")  # e.g., https://<name>.cognitiveservices.azure.com
AZURE_API_KEY = os.environ.get("AZURE_API_KEY")
API_VERSION = os.environ.get("AZURE_API_VERSION", "2024-11-05-preview")
DEFAULT_LANG = os.environ.get("DEFAULT_LANGUAGE", "he")
REDACTION_POLICY = os.environ.get("REDACTION_POLICY", "MaskWithCharacter")  # MaskWithCharacter|MaskWithEntityType|DoNotRedact
REDACTION_CHAR = os.environ.get("REDACTION_CHAR", "*")

@app.get("/health")
def health():
    ok = bool(AZURE_ENDPOINT and (AZURE_API_KEY) and API_VERSION)
    return jsonify(status="ok" if ok else "misconfigured",
                   endpoint=AZURE_ENDPOINT,
                   api_version=API_VERSION,
                   policy=REDACTION_POLICY,
                   char=REDACTION_CHAR)

@app.post("/api/redact-pii")
def redact_pii():
    try:
        data = request.get_json(force=True) or {}
        text = data.get("text", "")
        language = data.get("language", DEFAULT_LANG)

        if not AZURE_ENDPOINT or not AZURE_API_KEY:
            return jsonify(error="Server missing AZURE_ENDPOINT/AZURE_API_KEY"), 500
        if not text:
            return jsonify(error="Missing 'text'"), 400

        body = {
            "kind": "PiiEntityRecognition",
            "parameters": {
                "loggingOptOut": True,
            },
            "analysisInput": {
                "documents": [ { "id": "1", "language": language, "text": text } ]
            }
        }

        # Try preview redaction policy (if supported in region/api-version)
        if REDACTION_POLICY and REDACTION_POLICY != "DoNotRedact":
            body["parameters"]["redactionPolicy"] = {
                "policyKind": REDACTION_POLICY,
                "redactionCharacter": REDACTION_CHAR
            }
        elif REDACTION_POLICY == "DoNotRedact":
            body["parameters"]["redactionPolicy"] = {"policyKind": "DoNotRedact"}

        url = f"{AZURE_ENDPOINT}/language/:analyze-text?api-version={API_VERSION}"
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": AZURE_API_KEY
        }
        r = requests.post(url, headers=headers, json=body, timeout=30)

        # Fallback: if preview params invalid, retry GA without policy
        if r.status_code == 400 and "redactionPolicy" in r.text:
            fallback_body = {
                "kind": "PiiEntityRecognition",
                "parameters": {
                    "loggingOptOut": True,
                },
                "analysisInput": {
                    "documents": [ { "id": "1", "language": language, "text": text } ]
                }
            }
            r = requests.post(url, headers=headers, json=fallback_body, timeout=30)

        r.raise_for_status()
        data = r.json()
        redacted = (data.get("results", {})
                        .get("documents", [{}])[0]
                        .get("redactedText", ""))
        return jsonify({"redactedText": redacted})
    except requests.RequestException as e:
        return jsonify(error=f"Upstream error: {e}"), 502
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
