# BUG_BOUNTY_ROUTINE
# pytest tests/test_core.py -v 
# 🐞 The Sanchez Bug Bounty Routine v2.0
*Systematic intelligence gathering with surgical strikes*

## 🕵️ PHASE 0: Target Intelligence 
  **Subdomain Enumeration (Find the hidden grass):**
    * **Tool:** `subfinder -d target.com -silent | httpx -silent > alive_subs.txt`
    * **Action:** Look for weird names: `dev`, `staging`, `api`, `internal`, `uat`.
    * *Note:* The main site is usually secure. The `dev.target.com` subdomain is usually trash. Attack the trash.

  **Tech Stack ID (The Scouting Report):**
    * **Tool:** Wappalyzer (Browser) or `whatweb`.
    * **Check:**
        * PHP? -> Think LFI / Traversal.
        * Java/Spring? -> Think IDOR / SSRF.
        * Node.js? -> Think Prototype Pollution / NoSQLi.

---

## 🎯 PHASE 1: Surgical Recon 
1. **JS File Archaeology:**
   - Extract all JS files
   - Find hidden endpoints, API keys
   - Map authentication flows

2. **API Discovery:**
   - /api/, /graphql, /swagger, /openapi
   - API documentation = attack surface map

## ⚡ PHASE 2: Intelligent Automation
* **Tool:** `Red-Team-Arsenal/02-Traversal-Probe/probe.py`
    * **Target:** The `alive_subs.txt` list.
    * **Payloads:** `config_files.txt` or `swagger_endpoints.txt`.
    * **Goal:** Find `/.env`, `/openapi.json`, or `/actuator/health`.
    * *Win Condition:* If you find `openapi.json`, you skip straight to Phase 3.
1. **Context-Aware Scanning:**
   - Laravel? Check /_ignition, /telescope
   - Spring? Check /actuator, /h2-console
   - WordPress? Check /xmlrpc.php, /wp-json

2. **Low-Hanging Fruit Pipeline:**
   - 5-minute checks (.git, .env, robots.txt)
   - Subdomain takeover scan
   - S3 bucket misconfigurations

## 🧠 PHASE 3: Deep Manual Testing 
* **Action:** Try to break the rules.
    * *Coupon Codes:* Can I use the same code twice?
    * *Payments:* Can I change the price to 0.01 in the request body?
    * *Registration:* Can I sign up with `admin@target.com`?

## 🔗 PHASE 4: Vulnerability Chaining 
1. **Find connection points:**
   - Can XSS lead to CSRF token theft?
   - Can IDOR lead to admin access?
   - Can SSRF lead to cloud credentials?

2. **Impact amplification:**
   - Single bug → $500
   - Chained bugs → $5000

## 📊 PHASE 5: Professional Reporting 
1. **Executive Summary:** Business impact first
2. **Technical Details:** Reproducible steps
3. **Impact Quantification:** Numbers matter
4. **Remediation:** Specific fixes
5. **References:** CVEs, OWASP categories