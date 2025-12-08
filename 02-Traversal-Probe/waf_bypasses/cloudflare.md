# CLOUDFLARE
# ☁️ Cloudflare WAF Bypass Tactics

*Cloudflare protects the domain name, not the server. If I find the Origin IP, the WAF is useless.*

## 1. The "Direct IP" Attack (The Golden Ticket) 🎫
*Goal: Bypass Cloudflare completely by talking to the backend server directly.*

Cloudflare works like this: `User -> Cloudflare IP -> Real Server IP`.
If we find the Real IP, we go: `User -> Real Server IP`. Game over.

### A. Historical DNS Records
Before they used Cloudflare, they had a real IP. Internet archives remember.
* **Tools:**
    * [SecurityTrails](https://securitytrails.com) (Look for "A" records history)
    * [ViewDNS.info](https://viewdns.info/iphistory/)
    * [CrimeFlare](http://crimeflare.org:82/) (Database of leaked IPs)

### B. SSL Certificate Hunting (Censys/Shodan)
Cloudflare issues SSL certs for the domain. But the *Real Server* also needs an SSL cert to talk to Cloudflare.
* **Search Query (Censys):** `services.tls.certificates.leaf_data.names: target.com`
* **Logic:** If an IP address (that isn't Cloudflare's) holds a certificate for `target.com`, that is likely the Origin Server.

### C. The "Email Header" Leak
* **Logic:** Register an account on the target site. Trigger a "Reset Password" email.
* **Check:** Look at the "Received-By" headers in the email source code.
* **Result:** The email comes from the *Real Server*, not Cloudflare. It often leaks the Origin IP.

---

## 2. Subdomain Enumeration (The Grey Clouds) ☁️
*Goal: Find a subdomain that the admin forgot to proxy.*

In Cloudflare settings:
* 🟧 **Orange Cloud:** Proxied (Protected).
* ⬜ **Grey Cloud:** DNS Only (Unprotected / Direct IP).

Developers often protect `www.target.com` but leave `dev.target.com` or `ftp.target.com` exposed.
* **Action:** Run `subfinder` or `amass`.
* **Check:** `ping dev.target.com`. If the IP is NOT a Cloudflare range, you found the backend.

---

## 3. Protocol Confusion (The Nutmeg) ⚽
*Goal: Trick the WAF using older/different protocols.*

Cloudflare is optimized for modern traffic. Sometimes it gets confused if you play like it's 1999.

### A. HTTP/1.0 Downgrade
Modern browsers send HTTP/1.1 or 2. Some WAF rules fail to trigger on 1.0.
```http
GET /admin HTTP/1.0
Host: target.com

### B. Transfer-Encoding: Chunked

Tell the WAF you are sending data in pieces, but send it all at once (or vice versa).

### HTTP Example
POST /admin HTTP/1.1
Host: target.com
Transfer-Encoding: chunked

0
[Malicious Payload Here]



---

## 4. Case Variation (Regex Evasion) 🔠

**Goal:** Bypass sloppy WAF rules.

Cloudflare is smart, but custom rules written by admins are often weak.

**Blocked:**
/etc/passwd


**Bypasses:**


/EtC/PaSsWd
/etc/./passwd
/etc//passwd


---

## 5. Header Spoofing (Identity Theft) 🎭

**Goal:** Pretend to be an internal Cloudflare server.

Sometimes the origin server only accepts traffic from Cloudflare. You can spoof headers to look like Cloudflare.

### HTTP Headers
X-Forwarded-For: 127.0.0.1
X-Originating-IP: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Remote-Addr: 127.0.0.1
CF-Connecting-IP: 127.0.0.1


---

## 🏆 The "Hosts File" Trick

Once you find the **real IP** (e.g., `1.2.3.4`), don’t paste it directly into the browser.  
The server might reject raw IP requests.

Map it inside your `/etc/hosts` file:

1.2.3.4 target.com


Now when you visit `target.com`, your computer skips Cloudflare entirely and goes straight to the real IP.  
You're basically walking through the back door of the building.

---

```md
Done.
