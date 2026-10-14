import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from ebooklib import epub
    from bs4 import BeautifulSoup
except Exception:
    epub = None
    BeautifulSoup = None


class EbookReader:
    """Simple ebook manager supporting PDF and EPUB files.

    Stores uploaded files under `static/ebooks/` and exposes helpers to
    list files, extract text, and provide metadata for frontend consumption.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base = Path(base_dir or Path(__file__).parent.parent / "static" / "ebooks")
        self.audio_dir = self.base / "audio"
        os.makedirs(self.base, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)

    def _meta_path(self, eid: str) -> Path:
        return self.base / f"{eid}.json"

    def save_upload(self, filename: str, contents: bytes) -> Dict:
        ext = Path(filename).suffix.lower()
        if ext not in (".pdf", ".epub", ".txt"):
            raise ValueError("Unsupported ebook format")

        eid = uuid.uuid4().hex[:8]
        dest_name = f"{eid}{ext}"
        dest = self.base / dest_name
        with open(dest, "wb") as f:
            f.write(contents)

        meta = {
            "id": eid,
            "filename": filename,
            "stored_name": dest_name,
            "ext": ext,
            "path": f"/static/ebooks/{dest_name}",
            "size": dest.stat().st_size,
            "uploaded_at": datetime.now().isoformat(),
        }

        # Try to collect metadata
        try:
            m = self.get_metadata(eid)
            meta.update(m)
        except Exception:
            pass

        with open(self._meta_path(eid), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return meta

    def list_ebooks(self) -> Dict[str, Dict]:
        results = {}
        for p in self.base.glob("*"):
            if p.is_file() and p.suffix.lower() in (".pdf", ".epub", ".txt"):
                eid = p.stem
                meta_file = self._meta_path(eid)
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            results[eid] = json.load(f)
                    except Exception:
                        results[eid] = {"id": eid, "stored_name": p.name, "path": f"/static/ebooks/{p.name}", "ext": p.suffix.lower()}
                else:
                    results[eid] = {"id": eid, "stored_name": p.name, "path": f"/static/ebooks/{p.name}", "ext": p.suffix.lower()}
        return results

    def get_metadata(self, eid: str) -> Dict:
        # find actual file
        matches = list(self.base.glob(f"{eid}.*"))
        if not matches:
            raise FileNotFoundError("Ebook not found")
        path = matches[0]

        meta = {"id": eid, "stored_name": path.name, "path": f"/static/ebooks/{path.name}", "ext": path.suffix.lower()}

        if path.suffix.lower() == ".pdf" and fitz:
            try:
                doc = fitz.open(str(path))
                meta["pages"] = doc.page_count
                md = doc.metadata or {}
                meta["title"] = md.get("title")
                meta["author"] = md.get("author")
            except Exception:
                pass

        if path.suffix.lower() == ".epub" and epub:
            try:
                book = epub.read_epub(str(path))
                title = book.get_metadata('DC', 'title')
                author = book.get_metadata('DC', 'creator')
                meta["title"] = title[0][0] if title else None
                meta["author"] = author[0][0] if author else None
                # count document items as chapters
                items = [i for i in book.get_items() if i.get_type() == epub.ITEM_DOCUMENT]
                meta["chapters"] = len(items)
            except Exception:
                pass

        return meta

    def extract_text(self, eid: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> str:
        matches = list(self.base.glob(f"{eid}.*"))
        if not matches:
            raise FileNotFoundError("Ebook not found")
        path = matches[0]

        if path.suffix.lower() == ".pdf" and fitz:
            doc = fitz.open(str(path))
            pcount = doc.page_count
            s = start_page or 1
            e = end_page or s
            s = max(1, s)
            e = min(pcount, e)
            text_parts = []
            for pnum in range(s - 1, e):
                try:
                    page = doc.load_page(pnum)
                    text_parts.append(page.get_text("text"))
                except Exception:
                    continue
            return "\n\n".join(text_parts).strip()

        if path.suffix.lower() == ".epub" and epub and BeautifulSoup:
            book = epub.read_epub(str(path))
            docs = [i for i in book.get_items() if i.get_type() == epub.ITEM_DOCUMENT]
            s = (start_page - 1) if start_page else 0
            e = end_page if end_page else len(docs)
            s = max(0, s)
            e = min(len(docs), e)
            texts = []
            for item in docs[s:e]:
                try:
                    html = item.get_content().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')
                    texts.append(soup.get_text(separator=' ', strip=True))
                except Exception:
                    continue
            return "\n\n".join(texts).strip()

        # Plain text fallback
        if path.suffix.lower() == ".txt":
            with open(path, "r", encoding='utf-8', errors='ignore') as f:
                full = f.read()
                if start_page or end_page:
                    # treat pages as slices of ~2000 chars
                    chunk = 2000
                    s = (start_page - 1) * chunk if start_page else 0
                    e = end_page * chunk if end_page else s + chunk
                    return full[s:e]
                return full

        raise RuntimeError("Unsupported ebook format or missing parser libraries")
