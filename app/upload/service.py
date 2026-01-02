# app/upload/service.py
import boto3
import os
import uuid
from dotenv import load_dotenv
from fastapi import UploadFile

load_dotenv(".env")

# --- Configuration ---
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN")

# --- Initialize R2 Client ---
s3_client = boto3.client(
    service_name='s3',
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

async def upload_file_to_r2(file: UploadFile, folder: str = "general") -> str:
    try:
        print("--- R2 DEBUG INFO ---")
        # print(f"Loading .env from: {env_path}")
        print(f"ACCOUNT_ID: {ACCOUNT_ID}")
        print(f"BUCKET_NAME: {BUCKET_NAME}") # <--- If this says None, that's the error
        print(f"ACCESS_KEY found: {'Yes' if ACCESS_KEY else 'No'}")
        print("---------------------")
        file_ext = file.filename.split(".")[-1]
        unique_filename = f"{folder}/{uuid.uuid4()}.{file_ext}"

        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            unique_filename,
            ExtraArgs={'ContentType': file.content_type}
        )

        if PUBLIC_DOMAIN:
            return f"{PUBLIC_DOMAIN}/{unique_filename}"
        else:
            return unique_filename

    except Exception as e:
        print(f"R2 Upload Error: {e}")
        return None
    
