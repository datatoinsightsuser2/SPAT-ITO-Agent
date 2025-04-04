from pathlib import Path

def load_system_prompt() -> str:
    prompt_path = Path(__file__).parent / "system_prompt_content.txt"
    return prompt_path.read_text(encoding="utf-8")