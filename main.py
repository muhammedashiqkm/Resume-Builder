# main.py
from fastapi import FastAPI
from app.api import auth, report # Import the new report router

app = FastAPI(
    title="AI Student Report Generator",
    description="An API to generate PDF reports from student data using AI.",
    version="2.0.0"
)

# Include the routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(report.router, prefix="/api/v1/report", tags=["Reports"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the AI Student Report Generator API"}