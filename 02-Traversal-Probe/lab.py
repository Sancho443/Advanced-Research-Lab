#!/usr/bin/env python3
# Module: Vulnerable Lab
# Author: Sanchez
# Purpose: A leaky server to test fuzzing()

from flask import Flask, request, send_file, abort
import os

app = Flask(__name__)

# We pretend this folder is the "Public" folder
# But we are going to break out of it.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def home():
    return "🏠 Vulnerable Lab is Live. Try /load?file=lab.py"

@app.route('/load')
def load_file():
    filename = request.args.get('file')
    
    if not filename:
        return "❌ Missing 'file' parameter", 400

    # 🚨 VULNERABILITY: No sanitization!
    # We just join the path and try to open it.
    # If the user sends "../", we go up directory levels.
    target_path = os.path.join(BASE_DIR, filename)
    
    print(f"👀 Server trying to open: {target_path}")

    if os.path.exists(target_path) and os.path.isfile(target_path):
        # We return the file content (LFI)
        return send_file(target_path)
    else:
        return "❌ File not found", 404

if __name__ == '__main__':
    print(f"🔥 Lab running on http://127.0.0.1:5000")
    print(f"📂 Serving files from: {BASE_DIR}")
    app.run(port=5000, debug=True)