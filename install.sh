#!/bin/bash
# Nanobanana Installer
# One-button install for the Claude Code skill

set -e

SKILL_DIR="$HOME/.claude/skills/nanobanana"
REPO_URL="https://raw.githubusercontent.com/johnpsasser/nanobanana/main"

echo "Installing Nanobanana skill for Claude Code..."
echo ""

# Create skill directory
mkdir -p "$SKILL_DIR/scripts"

# Download skill files
echo "Downloading skill files..."
curl -sL "$REPO_URL/SKILL.md" -o "$SKILL_DIR/SKILL.md"
curl -sL "$REPO_URL/requirements.txt" -o "$SKILL_DIR/requirements.txt"
curl -sL "$REPO_URL/scripts/generate.py" -o "$SKILL_DIR/scripts/generate.py"
chmod +x "$SKILL_DIR/scripts/generate.py"

# Install Python dependencies (works in externally-managed environments too).
# This is best-effort — the script also auto-installs on first run if needed.
echo "Installing Python dependencies..."
PY="$(command -v python3 || command -v python)"
if ! "$PY" -m pip install -q -r "$SKILL_DIR/requirements.txt" 2>/dev/null \
  && ! "$PY" -m pip install -q --user -r "$SKILL_DIR/requirements.txt" 2>/dev/null \
  && ! "$PY" -m pip install -q --break-system-packages -r "$SKILL_DIR/requirements.txt" 2>/dev/null; then
    echo "  (Could not pre-install dependencies — the skill will install them on first run.)"
fi

# Check for API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo ""
    echo "---"
    echo "Almost done! You need to set your Gemini API key."
    echo ""
    echo "1. Get your API key at: https://aistudio.google.com/apikey"
    echo ""
    echo "2. Add this line to your ~/.zshrc or ~/.bashrc:"
    echo "   export GEMINI_API_KEY=\"your-api-key-here\""
    echo ""
    echo "3. Then run: source ~/.zshrc"
    echo "---"
else
    echo "GEMINI_API_KEY is already set."
fi

echo ""
echo "Installation complete!"
echo "Restart Claude Code to use the /nanobanana skill."
