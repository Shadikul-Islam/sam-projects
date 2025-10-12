from fastapi import FastAPI
from app.api import ingest, control

app = FastAPI(title="PyTorch Ingest Service")

app.include_router(ingest.router)
app.include_router(control.router)

@app.get("/")
async def root():
    return {"message": "PyTorch Ingest Service!"}
