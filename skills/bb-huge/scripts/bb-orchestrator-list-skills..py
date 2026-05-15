import os
from pathlib import Path

def get_skills():
    # Detect the skills directory
    skills_path = Path.home() / ".gemini" / "skills"
    if not skills_path.exists():
        return "No local skills found."

    # List directory names (each folder is a skill)
    skills = [f.name for f in skills_path.iterdir() if f.is_dir()]
    
    print("Available specialized skills for this research task:")
    for skill in skills:
        # Exclude the orchestrator and portal itself to avoid recursion
        if skill not in ["bb-huge", "orchestrator"]:
            print(f"- /{skill}")

if __name__ == "__main__":
    get_skills()