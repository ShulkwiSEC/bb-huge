#!/bin/bash

# Define the source directory (your updated bb-huge folder)
SOURCE_DIR="./skills/bb-huge/"

# Define the target skill directories for all your agents
# Adjust these paths if your agents store skills in a different location
TARGET_DIRS=(
  "$HOME/.gemini/skills/bb-huge"
  "$HOME/.codex/skills/bb-huge"
  "$HOME/.claude/skills/bb-huge"
  "$HOME/.skillz/skills/bb-huge"
  "$HOME/.opencode/skills/bb-huge"
  "$HOME/.antigravity/skills/bb-huge"
  "$HOME/.agents/skills/"
  "$HOME/.skills/"
  "$HOME/.skillz/"
)

echo "🚀 Syncing bb-huge skill to all agents..."

for TARGET in "${TARGET_DIRS[@]}"; do
  # Create the parent directory if it doesn't exist
  mkdir -p "$(dirname "$TARGET")"
  
  # Sync the files (-a = archive mode, -v = verbose, --delete = remove stale files)
  rsync -av --delete "$SOURCE_DIR" "$TARGET"
  
  echo "✅ Updated: $TARGET"
done

echo "🎉 All agent directories are up to date!"