from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from app.core.config import settings
from app.api import auth, report

app = FastAPI(
    title="AI Student Report Generator",
    version="2.1.0"
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

REPORTS_DIR = "static/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(report.router, prefix="/api/v1/report", tags=["Reports"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Student Report Generator API"}