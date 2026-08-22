from pathlib import Path
import shutil
import subprocess
import tempfile
import pymupdf
from docx import Document

class DocumentLoader:
    supported_extensions = {".txt", ".pdf", ".doc", ".docx"}

    def load(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Файл не найден: {path}")
        loaders = {".txt": self._load_txt, ".pdf": self._load_pdf,
                   ".docx": self._load_docx, ".doc": self._load_doc}
        try:
            text = loaders[path.suffix.lower()](path)
        except KeyError as exc:
            raise ValueError(f"Неподдерживаемый формат: {path.suffix.lower()}") from exc
        if not text.strip():
            raise ValueError(f"В документе не найден текст: {path}")
        return text

    @staticmethod
    def _load_txt(path: Path) -> str:
        for encoding in ("utf-8-sig", "cp1251", "utf-16"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                pass
        raise ValueError(f"Не удалось определить кодировку: {path}")

    @staticmethod
    def _load_pdf(path: Path) -> str:
        with pymupdf.open(path) as document:
            return "\n\n".join(page.get_text("text") for page in document)

    @staticmethod
    def _load_docx(path: Path) -> str:
        document = Document(path)
        parts = [p.text for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            parts.extend(" | ".join(c.text.strip() for c in row.cells) for row in table.rows)
        return "\n".join(parts)

    def _load_doc(self, path: Path) -> str:
        executable = shutil.which("soffice") or shutil.which("libreoffice")
        if not executable:
            raise RuntimeError("Для .doc установите LibreOffice и добавьте soffice в PATH")
        with tempfile.TemporaryDirectory() as output_dir:
            result = subprocess.run([executable, "--headless", "--convert-to", "docx",
                                     "--outdir", output_dir, str(path)], capture_output=True,
                                    text=True, timeout=120, check=False)
            converted = Path(output_dir) / f"{path.stem}.docx"
            if result.returncode != 0 or not converted.exists():
                raise RuntimeError(f"Не удалось преобразовать .doc: {result.stderr.strip()}")
            return self._load_docx(converted)
