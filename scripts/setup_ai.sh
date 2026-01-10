#!/bin/bash

# ==========================================
# RED TEAM ARSENAL - AI INTEGRATION SETUP
# "The Clean Sheet Edition"
# ==========================================

echo "⚽ Kickoff! Setting up the AI infrastructure for Sanchez..."

# --- STEP 1: DIRECTORIES ---
DIRECTORIES=(
    "core/ai/providers"
    "core/ai/cache"
    "core/ai/privacy"
    "core/ai/config"
    "core/ai/tools"
    "config"
    "logs/ai"
)

for dir in "${DIRECTORIES[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "✅ Created sector: $dir"
    else
        echo "⚠️  Sector exists (skipping): $dir"
    fi
    touch "$dir/__init__.py"
done

# --- STEP 2: DEPENDENCIES (The Fix) ---
echo "📦 Scouting players (dependencies)..."

# The players we need
DEPS=("openai>=1.0.0" "pydantic>=2.0.0" "python-dotenv" "tenacity" "tiktoken")

# Ensure requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    touch requirements.txt
    echo "📝 Created new requirements.txt"
fi

# Add players only if they aren't on the team sheet yet
for dep in "${DEPS[@]}"; do
    # Grep checks if the package name exists (ignores version numbers for safety)
    if grep -q "^${dep%%>*}" requirements.txt; then
        echo "⚠️  $dep is already in the squad (skipping)."
    else
        echo "$dep" >> requirements.txt
        echo "✅ Signed $dep to requirements.txt."
    fi
done

# --- STEP 3: INSTALLATION ---
if command -v pip3 &> /dev/null; then
    echo "⬇️  Training session: Installing dependencies..."
    # We just install from the main file now
    pip3 install -r requirements.txt
else
    echo "❌ VAR Check: pip3 not found. Please install Python/Pip."
fi

# --- STEP 4: CONFIG ---
if [ ! -f ".env" ]; then
    echo "📝 Drafting the contract (.env)..."
    cat <<EOT >> .env
# --- AI CONFIGURATION ---
DEEPSEEK_API_KEY=sk-placeholder-key-change-me
AI_MAX_MONTHLY_BUDGET=2.00
AI_INPUT_COST_PER_M=0.14
AI_OUTPUT_COST_PER_M=0.28
AI_ENABLED=true
AI_CACHE_TTL=86400
EOT
    echo "✅ .env created. EDIT YOUR API KEY!"
else
    echo "ℹ️  .env already exists. Check it manually."
fi

# --- STEP 5: FILES ---
touch core/ai/privacy/sanitizer.py
touch core/ai/providers/unified_client.py
touch core/ai/cache/cost_tracker.py
touch core/ai/config/prompts.json

echo "----------------------------------------------------"
echo "🏆 Full Time! Setup Complete."
echo "👉 Next Step: 'source .env' and start coding."
echo "----------------------------------------------------"