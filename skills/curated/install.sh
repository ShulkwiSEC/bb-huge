#!/bin/sh
# bb-huge Curated Skills Installer
# Cross-platform POSIX-compliant installer for security skills

set -e

# --- Default Config ---
TARGET_DIR="$HOME/.opencode/skills"
SOURCE_DIR="./skills/curated"
DRY_RUN=0
FORCE=0

# --- Help Text ---
show_help() {
    cat << EOF
Usage: install.sh [OPTIONS] [TARGET_DIR]

Options:
  -h, --help      Show this help message
  -l, --list      List all available skills in the curated collection
  -n, --dry-run   Show what would be installed without making changes
  -f, --force     Overwrite existing skill directories in target
  --source DIR    Specify source directory (default: $SOURCE_DIR)

Arguments:
  TARGET_DIR      Directory to install skills to (default: $TARGET_DIR)
EOF
}

# --- Parse Args ---
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) show_help; exit 0 ;;
        -l|--list)
            ls -1 "$SOURCE_DIR" | grep -v "MANIFEST.md" | grep -v "install.sh"
            exit 0
            ;;
        -n|--dry-run) DRY_RUN=1; shift ;;
        -f|--force) FORCE=1; shift ;;
        --source) SOURCE_DIR="$2"; shift 2 ;;
        -*) echo "Unknown option: $1"; show_help; exit 1 ;;
        *) TARGET_DIR="$1"; shift ;;
    esac
done

# --- Validation ---
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found."
    exit 1
fi

# --- Main Logic ---
echo "Installing bb-huge curated skills..."
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"

if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$TARGET_DIR"
fi

SKILL_COUNT=0
for skill_path in "$SOURCE_DIR"/*; do
    if [ ! -d "$skill_path" ]; then
        continue
    fi
    
    skill_name=$(basename "$skill_path")
    dest_path="$TARGET_DIR/$skill_name"
    
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "[DRY-RUN] Would install skill: $skill_name"
    else
        if [ -d "$dest_path" ]; then
            if [ "$FORCE" -eq 1 ]; then
                echo "Overwriting existing skill: $skill_name"
                rm -rf "$dest_path"
                cp -R "$skill_path" "$dest_path"
            else
                echo "Skipping existing skill: $skill_name (use -f to force)"
                continue
            fi
        else
            echo "Installing skill: $skill_name"
            cp -R "$skill_path" "$dest_path"
        fi
    fi
    SKILL_COUNT=$((SKILL_COUNT + 1))
done

if [ "$DRY_RUN" -eq 1 ]; then
    echo "Dry run complete. $SKILL_COUNT skills would be installed."
else
    echo "Installation complete. $SKILL_COUNT skills installed to $TARGET_DIR"
    echo "Note: You may need to restart your AI agent to discover new skills."
fi
