import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class _DiagSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-4o"

S = _DiagSettings()

def main():
    try:
        from openai import OpenAI
    except Exception as e:
        print("[ERR] openai SDK не установлен:", e)
        sys.exit(1)

    if not S.OPENAI_API_KEY:
        print("[INFO] OPENAI_API_KEY не задан — онлайн-генерация отключена. Оффлайн режим работает без ключа.")
        sys.exit(0)

    client = OpenAI(api_key=S.OPENAI_API_KEY)

    try:
        resp = client.chat.completions.create(
            model=S.OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Reply with one short sentence in Russian."},
                {"role": "user", "content": "Скажи, что это тестовый запрос для диагностики API."}
            ],
            temperature=0.2
        )
        print("[OK] chat.completions:", resp.choices[0].message.content.strip())
    except Exception as e:
        msg = str(e)
        if "insufficient_quota" in msg or "You exceeded your current quota" in msg:
            print("[ERR] Недостаточно квоты. Проверь Billing и Usage limits в проекте OpenAI.", file=sys.stderr)
        elif "model_not_found" in msg or "does not have access" in msg:
            print("[ERR] У проекта нет доступа к этой модели. Поставь другую (например, gpt-4o) или включи доступ.", file=sys.stderr)
        elif "invalid_api_key" in msg or "Incorrect API key" in msg:
            print("[ERR] Неверный API-ключ. Проверь .env и проект, в котором создан ключ.", file=sys.stderr)
        else:
            print("[ERR] Ошибка при вызове модели:", msg, file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
