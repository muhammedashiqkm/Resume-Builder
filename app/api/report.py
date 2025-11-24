# app/api/report.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.report import StudentPortfolioInput, ReportURLResponse
from app.services.llm_service import generate_ai_content
from app.services.pdf_service import generate_portfolio_pdf_async
from app.core.security import verify_token

router = APIRouter()

@router.post("/generate", response_model=ReportURLResponse)
async def generate_report(
    request_data: List[StudentPortfolioInput], # Expecting a List based on your JSON sample
    username: str = Depends(verify_token)
):
    """
    Generates a PDF Portfolio. 
    Note: Input is a LIST of students, but we process the first one for this example.
    """
    if not request_data:
        raise HTTPException(status_code=400, detail="Input list is empty")
    
    student = request_data[0] # Taking the first student

    # 1. Generate AI Content (Objective & Summary)
    ai_content = await generate_ai_content(student)

    # 2. Generate PDF
    report_url = await generate_portfolio_pdf_async(student, ai_content)

    return {"filename": f"{student.StudentName}_Portfolio.pdf", "report_url": report_url}