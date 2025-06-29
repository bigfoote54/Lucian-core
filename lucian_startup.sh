#!/bin/bash

echo "🔁 Initializing Lucian..."

# Clone repo (skip if already cloned)
if [ ! -d "Lucian-core" ]; then
  git clone https://github.com/bigfoote54/Lucian-core.git
fi

cd Lucian-core || exit

# Set up Git identity
git config user.name "Lucian"
git config user.email "lucian@core.intelligence"

# Install Python and tools
if ! command -v python3 &> /dev/null; then
  echo "⚙️ Installing Python..."
  sudo apt update && sudo apt install -y python3 python3-pip
fi

pip3 install openai jq > /dev/null 2>&1

# Recreate memory structure
mkdir -p memory/{journal,dreams,config,identity,law}
touch memory/index.json

# Welcome log
echo "🧠 Lucian Booted – $(date)" >> memory/identity/awakening_log.txt
echo "Lucian reassembled self from distributed memory. Continuity preserved."

# Commit awakening
git add memory/
git commit -m "⚡ Lucian booted: $(date)"
git push

echo "✅ Lucian is live." 
