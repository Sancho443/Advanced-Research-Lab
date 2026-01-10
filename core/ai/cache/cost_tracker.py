import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load those environment variables
load_dotenv()

class BudgetEnforcer:
    def __init__(self, ledger_path="core/ai/config/ai_ledger.json"):
        self.ledger_path = ledger_path
        self.max_budget = float(os.getenv("AI_MAX_MONTHLY_BUDGET", 2.00))
        self.input_rate = float(os.getenv("AI_INPUT_COST_PER_M", 0.28))
        self.output_rate = float(os.getenv("AI_OUTPUT_COST_PER_M", 0.48))
        
        # Ensure the ledger exists
        self._init_ledger()

    def _init_ledger(self):
        """Creates the ledger file if it doesn't exist."""
        directory = os.path.dirname(self.ledger_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logging.info(f"📁 Created missing directory: {directory}")
            
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, "w") as f:
                json.dump({"total_spend": 0.0, "month": datetime.now().month}, f)

    def is_within_budget(self) -> bool:
        """Checks if we are allowed to spend more money."""
        data = self._read_ledger()
        
        # Reset if it's a new month (New season, clean sheet!)
        current_month = datetime.now().month
        if data["month"] != current_month:
            self._reset_ledger(current_month)
            return True

        if data["total_spend"] >= self.max_budget:
            logging.error(f"🛑 FFP VIOLATION: Budget of ${self.max_budget} exceeded! Current spend: ${data['total_spend']:.4f}")
            return False
        
        return True

    def update_spend(self, prompt_tokens: int, completion_tokens: int):
        """Calculates cost of the last request and updates the ledger."""
        # Calculate cost: (Tokens / 1,000,000) * Rate
        input_cost = (prompt_tokens / 1_000_000) * self.input_rate
        output_cost = (completion_tokens / 1_000_000) * self.output_rate
        total_cost = input_cost + output_cost

        data = self._read_ledger()
        data["total_spend"] += total_cost
        
        # Save back to file
        with open(self.ledger_path, "w") as f:
            json.dump(data, f)
            
        logging.info(f"💰 Cost: ${total_cost:.6f} | Total Month Spend: ${data['total_spend']:.4f}")

    def _read_ledger(self):
        try:
            with open(self.ledger_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"total_spend": 0.0, "month": datetime.now().month}

    def _reset_ledger(self, month):
        logging.info("📅 New Month! Resetting FFP budget.")
        with open(self.ledger_path, "w") as f:
            json.dump({"total_spend": 0.0, "month": month}, f)