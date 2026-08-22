# Corporate RAG — CPU MVP

RAG-система для базы примерно в 300 000 слов. Поддерживает TXT, PDF, DOCX и DOC,
работает на CPU (4 ядра, 8–16 ГБ RAM), хранит векторы в Qdrant и предоставляет
HTTP API. Видеокарта для базового режима не требуется.

## 1. Установка (Windows PowerShell)

Требования: Python 3.12, Docker Desktop с WSL2. Для старых `.doc` также нужен
LibreOffice, команда `soffice` должна быть доступна в `PATH`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d
```

Python 3.12 выбран намеренно: ML-библиотеки на Windows обычно стабильнее работают
с ним, чем с Python 3.13.

## 2. Запуск API

```powershell
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Документация появится на `http://127.0.0.1:8000/docs`, Qdrant — на
`http://127.0.0.1:6333/dashboard`.

Первый запуск загрузит `intfloat/multilingual-e5-small` (около 470 МБ). После
этого модель берётся из локального кэша.

## 3. Индексация документов

Положите документы, например, в `data/raw`, затем вызовите:

```powershell
$body = @{ path = (Resolve-Path "data/raw").Path; recursive = $true } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ingest/directory `
  -ContentType application/json -Body $body
```

Повторная индексация безопасна: старые чанки этого документа удаляются, поэтому
дубли и остатки старой версии не накапливаются. Ошибка одного файла не останавливает
обработку остальных и возвращается в массиве `errors`.

PDF должен содержать текстовый слой. Для сканов позже потребуется отдельный OCR.

## 4. Поиск и вопрос

```powershell
$body = @{ query = "Сколько дней отпуска положено сотруднику?"; limit = 5 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/search `
  -ContentType application/json -Body $body
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask `
  -ContentType application/json -Body $body
```

Без настройки LLM `/search` полностью работает, а `/ask` возвращает найденные
источники без сгенерированного ответа.

## 5. Подключение генерации без Ollama

Подойдёт любой сервер с OpenAI-compatible endpoint `/chat/completions`: внешний
API или локальный сервер llama.cpp. Заполните `.env`:

```dotenv
LLM_BASE_URL=https://example.org/v1
LLM_API_KEY=your-key
LLM_MODEL=model-name
```

Ключ храните только в `.env`; этот файл исключён из Git.

## Настройки производительности

- `CHUNK_SIZE=900`, `CHUNK_OVERLAP=150` — размер в символах.
- `EMBEDDING_BATCH_SIZE=32` — при нехватке RAM уменьшите до 16.
- `ENABLE_RERANKER=false` — включение повышает качество, но расходует больше RAM/CPU.
- `SCORE_THRESHOLD=0.35` — минимальная косинусная близость.

Для текущего объёма отдельные PostgreSQL, Kubernetes и GPU не нужны. При переносе
на GPU интерфейсы API и Qdrant сохраняются; меняются embedding/LLM runtime и размер
батча.

## Проверка

```powershell
pytest -q
```

По умолчанию запускаются автономные unit-тесты. Старые сценарии `test_rag*.py`,
`test_ingestion.py` и `test_retriev*.py` оставлены как ручные интеграционные
проверки: для них предварительно нужны запущенный Qdrant и проиндексированные
тестовые документы.
