from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.report import StudentPortfolioInput, ReportURLResponse
from app.services.llm_service import generate_ai_content
from app.services.pdf_service import generate_portfolio_pdf_async
from app.core.security import verify_token
from app.core.config import settings 

router = APIRouter()

@router.post("/generate", response_model=ReportURLResponse)
async def generate_report(
    request_data: List[StudentPortfolioInput], 
    username: str = Depends(verify_token)
):
    """
    Generates a PDF Portfolio and returns a FULL URL based on BASE_URL env var.
    """
    if not request_data:
        raise HTTPException(status_code=400, detail="Input list is empty")
    
    student = request_data[0]

    ai_content = await generate_ai_content(student)

    relative_path = await generate_portfolio_pdf_async(student, ai_content)
    
    full_url = f"{settings.BASE_URL.rstrip('/')}/{relative_path}"

    return {
        "filename": f"{student.student_name}_Portfolio.pdf", 
        "report_url": full_url 
    }