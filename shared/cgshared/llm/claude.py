import anthropic
from cgshared.config.settings import get_anthropic_key, CLAUDE_MODEL

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_anthropic_key())
    return _client


def chat(
    messages: list[dict],
    system: str = "",
    max_tokens: int = 300,
    model: str = CLAUDE_MODEL,
) -> str:
    response = get_client().messages.create(
        model=model,
        system=system,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.content[0].text.strip()
