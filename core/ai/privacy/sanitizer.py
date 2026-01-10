import re

class Sanitizer:
    def __init__(self):
        # The "Red Cards" list - things that must NEVER leave your laptop
        self.patterns = {
            "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "ip_v4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "auth_header": r"(Authorization: )([^\r\n]+)",
            "cookie": r"(Cookie: )([^\r\n]+)"
        }

    def clean(self, text: str) -> str:
        """Strips sensitive info from logs."""
        if not text: return ""
        
        for key, pattern in self.patterns.items():
            # Replace the sensitive part with <REDACTED>
            # For auth/cookie, we keep the header name but hide the value
            if key in ["auth_header", "cookie"]:
                text = re.sub(pattern, r"\1<HIDDEN_SECRET>", text)
            else:
                text = re.sub(pattern, f"<{key.upper()}_REDACTED>", text)
        return text
    

#The "CDM" (The Sanitizer) This is your Casemiro. It stops attacks before they happen. We build this first.