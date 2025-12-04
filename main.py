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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = "media/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(report.router, prefix="/report", tags=["Reports"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Student Report Generator API"}