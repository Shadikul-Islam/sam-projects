from typing import Dict
from threading import Lock

_watermarks: Dict[str, str] = {}
_lock = Lock()

def get_watermark(stream: str) -> str | None:
    with _lock:
        return _watermarks.get(stream)

def set_watermark(stream: str, last_ingested_iso: str) -> None:
    with _lock:
        _watermarks[stream] = last_ingested_iso
