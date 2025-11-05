
# MCP Redactor Server (Azure App Service Ready)
Minimal Flask server that calls Azure AI Language PII (Analyze Text) and returns **redactedText** only.
Designed for Azure App Service (managed) and easy chaining from Custom GPT or MCP connector.

## Endpoints
- `POST /api/redact-pii` -> `{ "redactedText": "..." }`
- `GET /health` -> quick status

## Environment Variables (App Service → Configuration → Application settings)
- `AZURE_ENDPOINT` = `https://<your>.cognitiveservices.azure.com`
- `AZURE_API_KEY` = `<Key1 or Key2>` (or use Key Vault ref)
- `AZURE_API_VERSION` = `2024-11-05-preview` (fallback supported)
- `DEFAULT_LANGUAGE` = `he`
- `REDACTION_POLICY` = `MaskWithCharacter` | `MaskWithEntityType` | `DoNotRedact`
- `REDACTION_CHAR` = `*`

## Local run
```bash
pip install -r requirements.txt
export AZURE_ENDPOINT="..."
export AZURE_API_KEY="..."
export AZURE_API_VERSION="2024-11-05-preview"
python app.py
# or
PORT=8000 bash startup.sh
```

## Azure App Service deploy (via GitHub Actions)
1. Create App Service (Linux, Python 3.10/3.11).
2. In **Settings → Configuration → General settings** set **Startup Command** to:
```
bash startup.sh
```
3. In **Configuration → Application settings** add the env vars above.
4. Add your publish profile as a GitHub secret named `AZURE_WEBAPP_PUBLISH_PROFILE`.
   (App Service → Overview → Get publish profile)

5. Edit `.github/workflows/azure-webapp.yml`: set `app-name: <YOUR_APP_NAME>`.
6. Push to `main` → CI will build & deploy automatically.

## Test
```bash
curl -s -X POST "https://<YOUR_APP_NAME>.azurewebsites.net/api/redact-pii"   -H "Content-Type: application/json"   -d '{"text":"שלום, שמי דניאל והטלפון שלי 050-1234567"}'
```

Expected:
```json
{"redactedText":"שלום, שמי ****** והטלפון שלי ***********"}
```
