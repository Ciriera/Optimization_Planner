"""
Basit test uygulaması
"""
from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"} 