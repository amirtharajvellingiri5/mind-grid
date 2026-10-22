from openai import OpenAI

from app.config import settings

client = OpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)


def complete(system: str, user: str) -> tuple[str, str]:
    """Return (text, model that actually answered — routers like openrouter/free pick one per call)."""
    resp = client.chat.completions.create(
        model=settings.llm_model,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or "", resp.model or settings.llm_model