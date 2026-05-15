import os

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def load_prompt(agent_name: str, default: str = "") -> str:
    path = os.path.join(PROMPTS_DIR, f"{agent_name}.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return default


def save_prompt(agent_name: str, content: str) -> None:
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    path = os.path.join(PROMPTS_DIR, f"{agent_name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def list_prompts() -> dict[str, str]:
    if not os.path.exists(PROMPTS_DIR):
        return {}
    return {
        f[:-4]: open(os.path.join(PROMPTS_DIR, f), encoding="utf-8").read().strip()
        for f in os.listdir(PROMPTS_DIR)
        if f.endswith(".txt")
    }
