import os
from datetime import datetime
import uuid

BASE_DIR = "/srv/pytorch/data/raw"

def save_batch(lines: list[str]) -> str:
    """Save NDJSON batch to correct directory structure: /srv/pytorch/data/raw/YYYY/MM/DD/HH/"""
    if not lines:
        return None

    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    hour = now.strftime("%H")

    # Directory path example: /srv/pytorch/data/raw/2025/09/14/20/
    dir_path = os.path.join(BASE_DIR, year, month, day, hour)
    os.makedirs(dir_path, exist_ok=True)

    # File name example: batch-20251012T091903Z-5nqe7l.ndjson
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    rand = uuid.uuid4().hex[:6]
    filename = f"batch-{timestamp}-{rand}.ndjson"

    file_path = os.path.join(dir_path, filename)

    # Write NDJSON lines
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return file_path
