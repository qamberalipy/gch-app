# app/upload/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from app.user.user import get_current_user 
from app.user.models import User
# This import now works because we created service.py in the same folder
import app.upload.service as _upload_service 

router = APIRouter()

MAX_FILE_SIZE = 15 * 1024 * 1024 
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]

@router.post("/general-upload", status_code=status.HTTP_201_CREATED)
async def upload_general_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user) 
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # This calls the function in service.py
    file_url = await _upload_service.upload_file_to_r2(file, folder="images/profiles")

    if not file_url:
        raise HTTPException(status_code=500, detail="Upload failed")

    return {
        "status": "success",
        "url": file_url,
        "filename": file.filename
    }