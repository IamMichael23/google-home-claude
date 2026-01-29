#!/usr/bin/env python3
"""
Google Home -> Claude Code Bridge
A simple webhook server that receives commands and routes them to Claude.

Setup:
1. Run this server (locally or on a VPS with public access)
2. Use IFTTT or Google Home routines to send webhooks
3. Expose with ngrok/cloudflare tunnel for external access

Requirements:
    pip install flask anthropic python-dotenv
"""

import os
import subprocess
from flask import Flask, request, jsonify
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Anthropic()  # Uses ANTHROPIC_API_KEY from env

# Store conversation history per session
conversations = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/ask', methods=['POST'])
def ask_claude():
    """
    Endpoint for Google Home webhooks.
    
    Expected JSON: {"query": "your question", "session_id": "optional"}
    
    For IFTTT: Use the "TextField" ingredient as the query
    """
    data = request.json or {}
    query = data.get('query') or data.get('text') or data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not query:
        return jsonify({"error": "No query provided", "response": "I didn't catch that."}), 400
    
    # Get or create conversation history
    if session_id not in conversations:
        conversations[session_id] = []
    
    conversations[session_id].append({
        "role": "user",
        "content": query
    })
    
    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,  # Keep responses concise for voice
            system="You are a helpful voice assistant connected to Google Home. Keep responses concise and conversational - they will be spoken aloud. Aim for 1-3 sentences unless more detail is specifically requested.",
            messages=conversations[session_id]
        )
        
        assistant_message = response.content[0].text
        
        # Store assistant response in history
        conversations[session_id].append({
            "role": "assistant", 
            "content": assistant_message
        })
        
        # Trim history to last 20 messages to prevent token overflow
        if len(conversations[session_id]) > 20:
            conversations[session_id] = conversations[session_id][-20:]
        
        return jsonify({
            "response": assistant_message,
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "response": "Sorry, I encountered an error processing that request."
        }), 500

@app.route('/ask-cli', methods=['POST'])
def ask_claude_cli():
    """
    Alternative: Route through Claude Code CLI instead of API.
    Useful if you want to leverage Claude Code's tool capabilities.
    """
    data = request.json or {}
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Run claude code CLI with the query
        result = subprocess.run(
            ['claude', '-p', query, '--no-input'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return jsonify({
            "response": result.stdout.strip() or result.stderr.strip(),
            "exit_code": result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"response": "Request timed out."}), 504
    except FileNotFoundError:
        return jsonify({"response": "Claude CLI not found. Make sure it's installed."}), 500

@app.route('/clear', methods=['POST'])
def clear_session():
    """Clear conversation history for a session."""
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    
    if session_id in conversations:
        del conversations[session_id]
    
    return jsonify({"status": "cleared", "session_id": session_id})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🏠 Google Home -> Claude bridge running on port {port}")
    print(f"   POST /ask     - Send queries to Claude API")
    print(f"   POST /ask-cli - Send queries to Claude Code CLI")
    print(f"   POST /clear   - Clear conversation history")
    app.run(host='0.0.0.0', port=port, debug=False)
