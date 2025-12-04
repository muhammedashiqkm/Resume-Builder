from fastapi import APIRouter, HTTPException
import httpx
from app.models.report import PortfolioUrlRequest, StudentPortfolioInput, ReportURLResponse
from app.services.llm_service import generate_ai_content
from app.services.pdf_service import save_pdf_report
from app.core.logging_config import app_logger, error_logger

router = APIRouter()

@router.post("/generate", response_model=ReportURLResponse)
async def generate_report_from_url(request_data: PortfolioUrlRequest):
    """
    1. Receives URL + DriveData.
    2. Fetches student data from URL.
    3. Merges DriveData into StudentData.
    4. Generates PDF + Rating.
    """
    
    target_url = request_data.url.strip()
    if target_url.lower().startswith("url:"):
        target_url = target_url[4:].strip()

    app_logger.info(f"Fetching data from: {target_url}")
    fetched_data = {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(target_url, timeout=30.0)
            response.raise_for_status()
            fetched_data = response.json()
        except Exception as e:
            error_logger.error(f"Fetch error: {e}")
            raise HTTPException(status_code=502, detail=f"Failed to fetch student data: {e}")

    try:
        student_data = StudentPortfolioInput(**fetched_data)
        
        student_data.drive_data = request_data.drivedata

        ai_content = await generate_ai_content(student_data)
        
        pdf_url = save_pdf_report(student_data, ai_content)
        
        return ReportURLResponse(
            filename=pdf_url.split('/')[-1],
            report_url=pdf_url,
            rating=ai_content.rating 
        )

    except Exception as e:
        error_logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))