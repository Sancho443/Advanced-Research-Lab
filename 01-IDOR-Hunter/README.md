# 🚩 IDOR HUNTER (Advanced-Research-Lab)

![Version](https://img.shields.io/badge/version-2.0.0--dev-blue?style=for-the-badge&logo=python)
![Developer](https://img.shields.io/badge/developer-SANCHEZ-red?style=for-the-badge)
![Tactics](https://img.shields.io/badge/tactics-TOTAL%20FOOTBALL-orange?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

> **"We don't guess. We test."** — Sanchez

---

## ⚡ Overview

**IDOR Hunter** is a modular, automated offensive security tool designed to detect **Insecure Direct Object References (IDOR)** with precision.

Unlike dumb fuzzers that spam random numbers, this tool uses a **"Total Football"** approach:
* **Context-Aware:** Understands the difference between Numeric IDs, UUIDs, and MongoDB ObjectIDs.
* **Fuzzy Logic:** Uses `difflib` to detect data leaks even when the server returns `200 OK` for everything.
* **Stealth:** Rotates User-Agents and handles Proxy routing (Burp Suite) automatically.

---

## 🏗️ The Squad (Architecture)

The tool is split into three specialized modules that work together like a world-class midfield.

### 1. 🔭 The Scout (`modules/detector.py`)
**Role:** Reconnaissance & Intelligence  
**Goal:** Find *where* the IDs are hiding.

* **Tactics:**
    * Crawls HTML, JSON, and JavaScript sources.
    * Auto-detects ID types: `Numeric`, `UUID`, `MongoDB`.
    * **Logic:**
        ```python
        if "user_id" in url or is_mongodb_id(segment):
            flag_candidate()
        ```

### 2. 🧠 The Playmaker (`modules/guesser.py`)
**Role:** Payload Generation  
**Goal:** Create the *smartest* possible inputs to trick the server.

* **Tactics:**
    * **Numeric:** Proximity testing (`100` -> `99`, `101`) + Boundaries (`0`, `-1`).
    * **MongoDB:** Timestamp manipulation to find users created *seconds* apart.
    * **Bypasses:** Wrapper attacks (`{"id":100}`, `id[]=100`) and format flipping (`.json`).

### 3. 🧱 The Finisher (`hunter.py`)
**Role:** Execution & Detection  
**Goal:** Fire the payloads and confirm the vulnerability (The VAR Check).

* **Tactics:**
    * **Auto-Refresh:** Wraps the request engine to handle session expiry (`401/403`) automatically.
    * **Fuzzy Matching:**
        * 🔴 **Ratio 1.0:** Ignored (Same as baseline).
        * 🟡 **Ratio < 0.6:** Ignored (Likely 404/Error).
        * 🟢 **Ratio 0.6 - 0.98:** **FLAG IT** (Structure matches, data differs -> **LEAK**).

---

## 🚀 Installation & Usage

### 📦 Prerequisites
```bash
pip install -r requirements.txt
# Requires: requests, httpx, colorama, urllib3
⚙️ Configuration (core/config.py)
Control your proxy and stealth settings here. Touch this file to control the entire arsenal.

Python

USE_PROXY = True
PROXY_URL = "[http://127.0.0.1:8080](http://127.0.0.1:8080)"  # Route traffic to Burp Suite
THREADS = 10                         # Speed of attack
⚔️ Attack Commands
1. Basic Attack (The Friendly Match)

Bash

python3 hunter.py --url "[https://target.com/api/user/100](https://target.com/api/user/100)" --cookie "sessionid=xyz123"
2. Advanced Attack (The Cup Final) With Auto-Refresh and Custom Headers

Bash

python3 hunter.py \
  --url "[https://portal.mmust.ac.ke/student/1500](https://portal.mmust.ac.ke/student/1500)" \
  --cookie "PHPSESSID=abc; token=123" \
  --refresh-url "[https://portal.mmust.ac.ke/api/refresh](https://portal.mmust.ac.ke/api/refresh)" \
  --threads 20
📊 Output Example
When the tool scores a goal, you'll see this in your console:

Plaintext

🔍 [DEBUG] Targeting 'user_id' (original: 100)
✅ [INFO]  Session refreshed successfully
🟢 [HIGH]  IDOR (Content Leak) -> [https://target.com/api/user/101](https://target.com/api/user/101)
    └── Evidence: Similarity Ratio 0.92 (Structure matches, content differs)
🟢 [HIGH]  IDOR (Bypass) -> [https://target.com/api/user/102](https://target.com/api/user/102)
    └── Evidence: Status 403 -> 200 OK
🚧 Roadmap (Season 2 Transfer Targets)
We aren't winning the league just yet. Here is the plan:

[ ] Blind IDOR Verification: Dual-User mode (Attacker vs. Victim) to detect invisible state changes.

[ ] WAF Evasion: IP Rotation via X-Forwarded-For headers.

[ ] Recursive Crawling: Deep spidering beyond depth=2.

[ ] HTML Reporting: Generate report.html for better visualization.

⚠️ Disclaimer
Developer: Sanchez

This tool is for educational purposes and authorized security research only. Do not use this against targets you do not have permission to test. I am not responsible if you get banned, arrested, or relegated to the Sunday League.