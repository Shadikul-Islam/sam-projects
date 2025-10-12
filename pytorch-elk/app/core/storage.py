import os
from datetime import datetime
import uuid

BASE_DIR = "/srv/pytorch/data/raw"

def save_batch(lines: list[str]) -> str:
    """Save NDJSON batch to correct directory structure: /srv/pytorch/data/raw/DD-MM-YYYY/HH/"""
    if not lines:
        return None

    now = datetime.utcnow()
    # New folder format: day-month-year
    date_folder = now.strftime("%d-%m-%Y")
    hour = now.strftime("%H")

    # Directory path
    dir_path = os.path.join(BASE_DIR, date_folder, hour)
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
