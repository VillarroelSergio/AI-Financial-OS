from app.modules.ai.prompts.guardrails import sanitize_response


def test_sanitize_response_removes_emoji_and_preserves_plain_symbols():
    response = "Tu saldo es estable \U0001f4c8 y est\u00e1 protegido \u00a9."

    assert sanitize_response(response) == "Tu saldo es estable  y est\u00e1 protegido \u00a9."
