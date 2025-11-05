# app/api/report.py
import io
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
from app.models.report import StudentReportInput
from app.services import llm_service, pdf_service
from app.core import security

router = APIRouter()

@router.post("/generate", response_class=StreamingResponse)
async def generate_ai_report_pdf(
    student_data: StudentReportInput = Body(...),
    current_user: str = Depends(security.verify_token)
):
    """
    Accepts raw student data, generates a full AI analysis using the model 
    specified in the request body, and returns the report as a downloadable PDF.
    """
    try:
        # Step 1: Pass the model name from the request body to the LLM service.
        # This now correctly uses 'student_data.model'
        ai_report_data = await llm_service.generate_report_from_llm(
            student_data=student_data, 
            model_name=student_data.model
        )
        
        # Step 2: Convert the AI data into a PDF
        pdf_bytes = pdf_service.generate_pdf_from_data(ai_report_data)
        
        # Step 3: Stream the PDF back to the client
        pdf_stream = io.BytesIO(pdf_bytes)
        headers = {
            'Content-Disposition': f'attachment; filename="{student_data.name}_report.pdf"'
        }
        
        return StreamingResponse(
            content=pdf_stream, 
            media_type='application/pdf', 
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred during report generation: {str(e)}"
        )