from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import ValidationError
from app.models.ingest import NDJSONDocument
from app.core.storage import save_batch
from app.core.dedupe import is_duplicate  # use global dedupe tracker
import json
import os

router = APIRouter()

RECV_BEARER = os.getenv("AUTH_TOKEN")
if not RECV_BEARER:
    raise RuntimeError("AUTH_TOKEN not set in .env file")

@router.post("/ingest/batch")
async def ingest_batch(request: Request, authorization: str = Header(None)):
    # Auth check
    if authorization != f"Bearer {RECV_BEARER}":
        raise HTTPException(status_code=401, detail="Invalid token")

    # Read raw NDJSON body
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8").strip()
    if not body_text:
        raise HTTPException(status_code=400, detail="Empty body")

    received = 0
    written = 0
    skipped = 0
    lines_to_write = []

    lines = body_text.split("\n")
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        received += 1
        try:
            data = json.loads(line)
            doc = NDJSONDocument(**data)
            # Use global dedupe tracker
            if is_duplicate(doc.index, doc.id):
                skipped += 1
                continue
            written += 1
            lines_to_write.append(line)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail=f"Invalid JSON on line {line_num}")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation error on line {line_num}: {e}")

    # Save batch if there are new docs
    file_path = save_batch(lines_to_write) if lines_to_write else None

    return {
        "ok": True,
        "received": received,
        "written": written,
        "skipped": skipped,
        "file": file_path
    }
