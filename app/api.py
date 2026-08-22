import secrets

import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, WithJsonSchema

from app.ingestion import DocumentIngestion
from app.rag import RAGPipeline
from app.retriever import Retriever
from app.config import ADMIN_API_KEY

BinaryUploadFile = Annotated[
    UploadFile,
    WithJsonSchema(
        {
            "type": "string",
            "format": "binary",
        }
    ),
]

app = FastAPI(title="Corporate RAG", version="1.0.0")

STATIC_DIRECTORY = Path(__file__).parent / "static"

DOCUMENT_DIRECTORY = Path("data/raw").resolve()
DOCUMENT_DIRECTORY.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 25 * 1024 * 1024

def require_admin(
    x_admin_key: Annotated[
        str | None,
        Header(),
    ] = None,
) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "Административный ключ "
                "не настроен."
            ),
        )

    if (
        not x_admin_key
        or not secrets.compare_digest(
            x_admin_key,
            ADMIN_API_KEY,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Неверный административный ключ."
            ),
        )

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="static",
)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(
        STATIC_DIRECTORY / "index.html"
    )

@lru_cache
def ingestion_service(): return DocumentIngestion()
@lru_cache
def retriever_service(): return Retriever()
@lru_cache
def rag_service(): return RAGPipeline(retriever=retriever_service())

class PathRequest(BaseModel):
    path: str
    recursive: bool = True
class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)

def safe_file_name(original_name: str | None) -> str:
    if not original_name:
        raise ValueError("Не указано имя файла.")

    file_name = Path(original_name).name
    file_name = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        file_name,
    ).strip(" .")

    if not file_name:
        raise ValueError("Некорректное имя файла.")

    extension = Path(file_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"Формат {extension or 'без расширения'} "
            f"не поддерживается. Разрешены: {allowed}"
        )

    return file_name


async def save_upload(
    uploaded_file: UploadFile,
    destination: Path,
) -> int:
    size = 0

    with destination.open("wb") as output:
        while chunk := await uploaded_file.read(1024 * 1024):
            size += len(chunk)

            if size > MAX_FILE_SIZE:
                output.close()
                destination.unlink(missing_ok=True)

                raise ValueError(
                    "Размер файла превышает 25 МБ."
                )

            output.write(chunk)

    if size == 0:
        destination.unlink(missing_ok=True)
        raise ValueError("Загружен пустой файл.")

    return size

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/upload")
async def upload_documents(
    files: list[BinaryUploadFile] = File(...),
    _: None = Depends(require_admin),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Не выбраны файлы.",
        )

    result = {
        "uploaded": 0,
        "skipped": 0,
        "chunks": 0,
        "documents": [],
        "errors": [],
    }

    for uploaded_file in files:
        try:
            file_name = safe_file_name(
                uploaded_file.filename
            )
            destination = DOCUMENT_DIRECTORY / file_name
            destination_existed = destination.exists()

            file_size = await save_upload(
                uploaded_file,
                destination,
            )

            ingestion_result = (
                ingestion_service().ingest_with_status(
                    str(destination)
                )
            )

            status = ingestion_result["status"]
            chunks = ingestion_result["chunks"]

            if status == "duplicate":
                result["skipped"] += 1

                existing_source = ingestion_result.get(
                    "existing_source"
                )

                if (
                    not destination_existed
                    and existing_source
                    and Path(existing_source).resolve()
                    != destination.resolve()
                ):
                    destination.unlink(missing_ok=True)

            else:
                result["uploaded"] += 1
                result["chunks"] += chunks

            result["documents"].append(
                {
                    "file_name": file_name,
                    "size": file_size,
                    "chunks": chunks,
                    "status": status,
                    "existing_source": (
                        ingestion_result.get(
                            "existing_source"
                        )
                    ),
                }
            )

        except Exception as exc:
            result["errors"].append(
                {
                    "file_name": (
                        uploaded_file.filename
                        or "Неизвестный файл"
                    ),
                    "error": str(exc),
                }
            )

        finally:
            await uploaded_file.close()

    return result

@app.get("/documents")
def list_documents():
    try:
        documents = (
            ingestion_service()
            .storage
            .list_documents()
        )

        return {
            "total": len(documents),
            "documents": documents,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    _: None = Depends(require_admin),
):
    try:
        deleted_document = (
            ingestion_service()
            .storage
            .delete_document(document_id)
        )

        if not deleted_document:
            raise HTTPException(
                status_code=404,
                detail="Документ не найден.",
            )

        return {
            "status": "removed",
            "document_id": document_id,
            "file_name": deleted_document.get(
                "file_name"
            ),
            "file_deleted": False,
            "message": (
                "Документ удалён из базы знаний. "
                "Исходный файл сохранён в data/raw."
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

@app.post("/ingest/file")
def ingest_file(
    request: PathRequest,
    _: None = Depends(require_admin),
):
    try: return {"chunks": ingestion_service().ingest(request.path)}
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.post("/ingest/directory")
def ingest_directory(
    request: PathRequest,
    _: None = Depends(require_admin),
):
    try: return ingestion_service().ingest_directory(request.path, request.recursive)
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.post("/search")
def search(
    request: QueryRequest,
    _: None = Depends(require_admin),
):
    try: return {"results": retriever_service().retrieve(request.query, request.limit)}
    except Exception as exc: raise HTTPException(500, str(exc)) from exc

@app.post("/ask")
def ask(request: QueryRequest):
    try:
        result = rag_service().answer(
            request.query,
            request.limit,
        )

        return {
            "answer": result["answer"],
            "sources": result["sources"],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post("/debug/ask")
def debug_ask(
    request: QueryRequest,
    _: None = Depends(require_admin),
):
    try:
        return rag_service().answer(
            request.query,
            request.limit,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc