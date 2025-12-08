# 🕸️ Web Reconnaissance Methodology
*My 4-Hour "Leave No Stone Unturned" Routine.*

## 1. Subdomain Enumeration (The Broad Scope)
*Goal: Find the dev/staging environments developers forgot about.*

| Step | Tool | Command | Why? |
| :--- | :--- | :--- | :--- |
| **Passive** | `Subfinder` | `subfinder -d target.com -o subs.txt` | Fast, no traffic sent to target. |
| **Active** | `Amass` | `amass enum -active -d target.com` | Slower, but finds obscure DNS records. |
| **Permutations** | `Altdns` | `altdns -i subs.txt -o data_output -w words.txt` | Finds `dev-api.target.com` from `api.target.com`. |

## 2. Live Host Probing (Filtering Noise)
*Goal: Don't waste time on dead domains.*

* **Tool:** `httpx`
* **Command:** `cat subs.txt | httpx -title -tech-detect -status-code -ip -o live_hosts.txt`
* **Sanchez Pro Tip:** Look for `403 Forbidden` or `401 Unauthorized` status codes. These often hide internal tools (Jenkins, Grafana) that are juicy targets.

## 3. Tech Stack Profiling (Know Your Enemy)
* **Wappalyzer / BuiltWith:** Is it Python/Django? PHP/Laravel?
* **Action:** If I see **Python**, I hunt for **SSTI**. If I see **PHP**, I hunt for **Type Juggling** or **LFI**.

## 4. Parameter Discovery (The Mining Phase)
*Goal: Find hidden GET/POST parameters.*
* **Tool:** `Arjun`
* **Command:** `arjun -u https://target.com/endpoint -w params.txt`
* **Why:** Developers often leave debug parameters like `?debug=true` or `?admin=1`.