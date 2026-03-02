from groq import Groq

# 🔑 Hardcoded (move to env later)
client = Groq(
    api_key="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"
)

MODEL_NAME = "llama-3.3-70b-versatile"


def generate(prompt: str):
    """
    Returns:
        (response_text, token_usage)
    """

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=0.2,
    )

    text = completion.choices[0].message.content

    # ✅ token tracking (important for metrics)
    tokens = 0
    if hasattr(completion, "usage") and completion.usage:
        tokens = completion.usage.total_tokens

    return text, tokens