# Google Home → Claude Bridge

Connect your Google Home to Claude for an AI-powered voice assistant.

## Quick Start

### 1. Install dependencies
```bash
pip install flask anthropic python-dotenv
```

### 2. Set up your API key
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### 3. Run the server
```bash
python server.py
```

### 4. Expose to the internet
Use ngrok, Cloudflare Tunnel, or deploy to a VPS:
```bash
# ngrok example
ngrok http 5000
```

## Connecting Google Home

### Option A: IFTTT (Easiest)

1. Create an IFTTT account and connect Google Assistant
2. Create a new Applet:
   - **If This:** Google Assistant → "Say a phrase with a text ingredient"
   - **Phrase:** "Ask Claude $" (where $ is your query)
   - **Then That:** Webhooks → Make a web request
     - URL: `https://your-server.com/ask`
     - Method: POST
     - Content-Type: application/json
     - Body: `{"query": "{{TextField}}"}`

### Option B: Home Assistant

If you use Home Assistant, add a REST command:

```yaml
# configuration.yaml
rest_command:
  ask_claude:
    url: "http://localhost:5000/ask"
    method: POST
    content_type: "application/json"
    payload: '{"query": "{{ query }}"}'

# automations.yaml  
automation:
  - alias: "Ask Claude via voice"
    trigger:
      - platform: conversation
        command:
          - "ask claude {query}"
    action:
      - service: rest_command.ask_claude
        data:
          query: "{{ trigger.slots.query }}"
```

### Option C: Custom Google Action (Advanced)

Google has deprecated new conversational Actions, but you can still use Dialogflow CX with a webhook fulfillment pointing to this server.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Send query to Claude API |
| `/ask-cli` | POST | Send query through Claude Code CLI |
| `/clear` | POST | Clear conversation history |
| `/health` | GET | Health check |

### Example Request
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather like today?"}'
```

## Tips

- Keep `max_tokens` low (300-500) for snappy voice responses
- Use `session_id` to maintain separate conversations per device/user
- The `/ask-cli` endpoint can leverage Claude Code's file/tool capabilities

## Security

⚠️ Add authentication before exposing publicly:
- API key header validation
- Rate limiting
- IP allowlisting

```python
# Example: Add to server.py
API_KEY = os.environ.get('WEBHOOK_API_KEY')

@app.before_request
def check_api_key():
    if request.endpoint not in ['health']:
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
```
