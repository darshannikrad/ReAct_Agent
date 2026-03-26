import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")

client = Groq(api_key=api_key)

# ── Best accuracy model on Groq ──────────────────────────────────────
# llama-3.3-70b-specdec        → best speed + accuracy combo
# deepseek-r1-distill-llama-70b → best for reasoning/math (slower)
# llama3-70b-8192              → reliable fallback
MODEL_NAME = "llama-3.3-70b-versatile"


def generate(system_prompt: str, user_prompt: str = None):
    """
    Preferred: generate(system_prompt, user_prompt)
    Legacy:    generate(full_prompt)
    Returns:   (response_text, token_usage)
    """
    if user_prompt is None:
        messages = [{"role": "user", "content": system_prompt}]
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,   # deterministic = most accurate
        max_tokens=512,
    )

    text   = completion.choices[0].message.content.strip()
    tokens = 0
    if hasattr(completion, "usage") and completion.usage:
        tokens = completion.usage.total_tokens

    return text, tokens