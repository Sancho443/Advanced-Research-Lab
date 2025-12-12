#!/usr/bin/env python3
# Module: Vulnerable Lab v2.0 (Total Football Edition)
# Author: Sanchez (The Architect)
# Purpose: A leaky server to test GET, POST, Cookie LFI, and Log Poisoning.

from flask import Flask, request, send_file, make_response
import os

app = Flask(__name__)

# This is our "Root" folder.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "access.log")

def log_request():
    """Simulates a server logger. Writes User-Agent to a local file."""
    ua = request.headers.get('User-Agent', 'Unknown')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[LOG] Hit from UA: {ua}\n")

@app.before_request
def before_request():
    # Every request gets logged (Testing Ground for Scenario 3)
    log_request()

@app.route('/')
def home():
    return """
    <h1>🏟️ Sanchez Training Ground</h1>
    <ul>
        <li><b>GET LFI:</b> <a href="/load?file=lab.py">/load?file=...</a></li>
        <li><b>POST LFI:</b> /profile (param: 'avatar')</li>
        <li><b>Cookie LFI:</b> /settings (Cookie: 'lang')</li>
        <li><b>Wrapper RCE:</b> /vuln.php (php://input)</li>
        <li><b>Log File:</b> access.log (It exists locally!)</li>
    </ul>
    """

# ———— SCENARIO 1: Standard GET LFI ————
@app.route('/load')
def load_file():
    filename = request.args.get('file')
    if not filename:
        return "❌ Missing 'file' parameter", 400

    target_path = os.path.join(BASE_DIR, filename)
    print(f"🔍 [GET] Trying to load: {target_path}")

    if os.path.exists(target_path) and os.path.isfile(target_path):
        return send_file(target_path)
    return "❌ File not found", 404

# ———— SCENARIO 2: POST Parameter LFI ————
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        return "Send a POST request with 'avatar' parameter."
    
    # Vulnerable POST parameter
    filename = request.form.get('avatar')
    if not filename:
        return "❌ Missing 'avatar' POST parameter", 400

    target_path = os.path.join(BASE_DIR, filename)
    print(f"🔍 [POST] Trying to load: {target_path}")

    if os.path.exists(target_path) and os.path.isfile(target_path):
        return send_file(target_path)
    return "❌ File not found", 404

# ———— SCENARIO 3: Cookie LFI ————
@app.route('/settings')
def settings():
    # Vulnerable Cookie 'lang'
    lang = request.cookies.get('lang')
    if not lang:
        resp = make_response("❌ Set the 'lang' cookie to exploit me.")
        resp.set_cookie('lang', 'english')
        return resp

    target_path = os.path.join(BASE_DIR, lang)
    print(f"🔍 [COOKIE] Trying to load: {target_path}")

    if os.path.exists(target_path) and os.path.isfile(target_path):
        return send_file(target_path)
    return "❌ File not found (Cookie check failed)", 404

# ———— SCENARIO 4: Mock php://input (RCE) ————
@app.route('/vuln.php', methods=['GET', 'POST'])
def mock_php_input():
    # We simulate PHP's behavior. 
    # If the user sends "php://input" (which usually means they want to execute body)
    # AND the body contains our PHP shell...
    
    # Note: Flask can't actually run PHP, so we mock the SUCCESS response.
    if request.method == 'POST':
        data = request.data.decode('utf-8', errors='ignore')
        if "<?php" in data and "system('id')" in data:
            return "RCE_CONFIRMED_SANCHEZ\nuid=33(www-data) gid=33(www-data) groups=33(www-data)"
    
    return "Simulated PHP Engine. Send POST data to execute.", 200

if __name__ == '__main__':
    # Create a dummy log file if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write("--- Server Logs Started ---\n")
            
    print(f"🔥 Sanchez Training Ground running on http://127.0.0.1:5000")
    print(f"📂 Base Dir: {BASE_DIR}")
    print(f"📜 Log File: {LOG_FILE}")
    app.run(port=5000, debug=True)