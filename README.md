# EORA RAG Assistant (FastAPI) - краткая инструкция (подробный отчет в README_DETAILED)

## Возможности
- Индексация ссылок (кейсы EORA) → чанки → эмбеддинги → SQLite.
- Поиск релевантных фрагментов (RAG).
- Два режима ответа:
  - **extractive** (офлайн): конспект из релевантных цитат.
  - **inline / sources / simple** (онлайн): генерация связного ответа OpenAI.

## Требования
- Python 3.11+
- Активный OpenAI API ключ с квотой/доступом к выбранным моделям.

## Установка
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env

## Запуск
uvicorn app.main:app --reload
откройте http://localhost:8000/ui/

## Режимы
- Offline: EMBEDDING_BACKEND=local; генерация — extractive (без OpenAI).
- Hybrid: EMBEDDING_BACKEND=local, но при наличии OPENAI_API_KEY — inline/sources/simple.
- Online: EMBEDDING_BACKEND=openai (нужен доступ к text-embedding-3-large или -3-small) + любая чат-модель (например, gpt-4o).

## Диагностика ключа
python tools/diagnose.py

## CLI
Remove-Item .\rag.db -Force
python cli.py ingest
python cli.py ask -q "Что вы можете сделать для ритейлеров?" --mode inline --out-md answer.md

## Как пользоваться UI (кратко)

1) Откройте `http://localhost:8000/ui/`.  
2) В блоке **Индексация** при желании укажите кастомные URL, выберите `Embedding backend`, при онлайн-режиме вставьте `OPENAI_API_KEY`, либо загрузите `links.txt`, нажмите **Индексировать**.  
3) В **Задать вопрос** введите запрос, выберите **режим** (simple/sources/inline/extractive), при необходимости укажите модели и ключ — **Ответить**.  
4) Секция **Ответ**: текст с inline-ссылками (для сложного режима) и список **Источников**. Кнопка **Скачать .md** — выгрузит файл.
