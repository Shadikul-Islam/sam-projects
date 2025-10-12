from threading import Lock

_seen_docs = set()  # stores tuples (index, id)
_lock = Lock()

def is_duplicate(index: str, doc_id: str) -> bool:
    key = (index, doc_id)
    with _lock:
        if key in _seen_docs:
            return True
        _seen_docs.add(key)
        return False
