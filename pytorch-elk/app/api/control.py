from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from app.core.watermark import get_watermark, set_watermark
import os

router = APIRouter()

RECV_BEARER = os.getenv("AUTH_TOKEN")
if not RECV_BEARER:
    raise RuntimeError("AUTH_TOKEN not set in .env file")

class WatermarkUpdate(BaseModel):
    stream: str
    last_ingested_iso: str

@router.get("/control/watermark")
async def get_watermark_endpoint(stream: str = Query(...)):
    value = get_watermark(stream)
    if value is None:
        raise HTTPException(status_code=404, detail="Watermark not set")
    return {"last_ingested_iso": value}

@router.put("/control/watermark")
async def put_watermark_endpoint(update: WatermarkUpdate, authorization: str = Header(None)):
    if authorization != f"Bearer {RECV_BEARER}":
        raise HTTPException(status_code=401, detail="Invalid token")
    set_watermark(update.stream, update.last_ingested_iso)
    return {"ok": True}
