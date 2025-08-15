from typing import List, Literal
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    openai_chat_model: str = Field("gpt-4o", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field("text-embedding-3-large", alias="OPENAI_EMBEDDING_MODEL")

    # Embeddings backend
    embedding_backend: Literal["openai", "local"] = Field("local", alias="EMBEDDING_BACKEND")
    local_embedding_model: str = Field(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        alias="LOCAL_EMBEDDING_MODEL",
    )

    # RAG / crawling
    user_agent: str = Field("EORA-RAG-Bot/1.0 (+https://example.org)", alias="USER_AGENT")
    chunk_size: int = Field(400, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(80, alias="CHUNK_OVERLAP")
    top_k: int = Field(6, alias="TOP_K")
    max_context_chars: int = Field(12000, alias="MAX_CONTEXT_CHARS")
    timeout_seconds: int = Field(30, alias="TIMEOUT_SECONDS")

    # DB
    sqlite_path: str = Field("rag.db", alias="SQLITE_PATH")

    # Links
    seed_links_file: str | None = Field(None, alias="SEED_LINKS_FILE")

    # Fallback seed
    seed_links: List[AnyHttpUrl] = [
        "https://eora.ru/cases/promyshlennaya-bezopasnost",
        "https://eora.ru/cases/lamoda-systema-segmentacii-i-poiska-po-pohozhey-odezhde",
        "https://eora.ru/cases/navyki-dlya-golosovyh-assistentov/karas-golosovoy-assistent",
        "https://eora.ru/cases/assistenty-dlya-gorodov",
        "https://eora.ru/cases/avtomatizaciya-v-promyshlennosti/chemrar-raspoznovanie-molekul",
        "https://eora.ru/cases/zeptolab-skazki-pro-amnyama-dlya-sberbox",
        "https://eora.ru/cases/goosegaming-algoritm-dlya-ocenki-igrokov",
        "https://eora.ru/cases/dodo-pizza-robot-analitik-otzyvov",
        "https://eora.ru/cases/ifarm-nejroset-dlya-ferm",
        "https://eora.ru/cases/zhivibezstraha-navyk-dlya-proverki-rodinok",
        "https://eora.ru/cases/sportrecs-nejroset-operator-sportivnyh-translyacij",
        "https://eora.ru/cases/avon-chat-bot-dlya-zhenshchin",
        "https://eora.ru/cases/navyki-dlya-golosovyh-assistentov/navyk-dlya-proverki-loterejnyh-biletov",
        "https://eora.ru/cases/computer-vision/iss-analiz-foto-avtomobilej",
        "https://eora.ru/cases/purina-master-bot",
        "https://eora.ru/cases/skinclub-algoritm-dlya-ocenki-veroyatnostej",
        "https://eora.ru/cases/skolkovo-chat-bot-dlya-startapov-i-investorov",
        "https://eora.ru/cases/purina-podbor-korma-dlya-sobaki",
        "https://eora.ru/cases/purina-navyk-viktorina",
        "https://eora.ru/cases/dodo-pizza-pilot-po-avtomatizacii-kontakt-centra",
        "https://eora.ru/cases/dodo-pizza-avtomatizaciya-kontakt-centra",
        "https://eora.ru/cases/icl-bot-sufler-dlya-kontakt-centra",
        "https://eora.ru/cases/s7-navyk-dlya-podbora-aviabiletov",
        "https://eora.ru/cases/workeat-whatsapp-bot",
        "https://eora.ru/cases/absolyut-strahovanie-navyk-dlya-raschyota-strahovki",
        "https://eora.ru/cases/kazanexpress-poisk-tovarov-po-foto",
        "https://eora.ru/cases/kazanexpress-sistema-rekomendacij-na-sajte",
        "https://eora.ru/cases/intels-proverka-logotipa-na-plagiat",
        "https://eora.ru/cases/karcher-viktorina-s-voprosami-pro-uborku",
        "https://eora.ru/cases/chat-boty/purina-friskies-chat-bot-na-sajte",
        "https://eora.ru/cases/nejroset-segmentaciya-video",
        "https://eora.ru/cases/chat-boty/essa-nejroset-dlya-generacii-rolikov",
        "https://eora.ru/cases/qiwi-poisk-anomalij",
        "https://eora.ru/cases/frisbi-nejroset-dlya-raspoznavaniya-pokazanij-schetchikov",
        "https://eora.ru/cases/skazki-dlya-gugl-assistenta",
        "https://eora.ru/cases/chat-boty/hr-bot-dlya-magnit-kotoriy-priglashaet-na-sobesedovanie",
    ]


settings = Settings()
