def load_initial_prompt() -> str:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def get_initial_prompt(nickname: str) -> str:
    return StaticVariables.INITIAL_PROMPT.replace("%nickname%", nickname)


class StaticVariables:
    INITIAL_PROMPT = load_initial_prompt()
