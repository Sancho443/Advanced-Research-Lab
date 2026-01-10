import os
import asyncio
from google import genai
from tenacity import retry, stop_after_attempt, wait_fixed
from core.ai.cache.cost_tracker import BudgetEnforcer

class AIClient:
    def __init__(self):
        # We default to Gemini
        self.provider = os.getenv("AI_PROVIDER", "gemini")
        self.budget_enforcer = BudgetEnforcer()
        
        if self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("❌ MISSING KEY: You need GEMINI_API_KEY in your .env file!")
            
            # ✅ NEW V1 SYNTAX: Use the new Client
            self.client = genai.Client(api_key=api_key)
            
            # ✅ MODEL SELECTION:
            # 'gemini-2.0-flash' gave you a Rate Limit (429) -> It exists but you were too fast.
            # 'gemini-1.5-flash' gave you a Not Found (404) -> Weird.
            # Let's use 'gemini-2.0-flash' again. If it says "Rate Limit", IT WORKS. Just wait.
            self.model_name = 'gemini-2.0-flash-lite' 

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def analyze_snippet(self, prompt: str, system_role="You are a Red Team Expert."):
        try:
            full_prompt = f"{system_role}\n\n=== CODE TO ANALYZE ===\n{prompt}"
            
            # ✅ NEW ASYNC SYNTAX (using .aio)
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            
            if not response.text:
                return "⚠️ The AI refused to answer (Safety Filter Triggered)."
                
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            # Handle the specific errors
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                return "🛑 RATE LIMIT HIT: The code works, but Google is cooling you down. Wait 60s."
            if "404" in error_msg:
                 return f"❌ Model Not Found: Google isn't letting you use '{self.model_name}' yet."
            return f"❌ Error: {error_msg}"