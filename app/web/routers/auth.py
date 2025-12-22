from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Point to the root templates folder
templates = Jinja2Templates(directory="templates")

# include_in_schema=False hides this from the API Docs
router = APIRouter(include_in_schema=False)

@router.get("/")
async def login_view(request: Request):
   
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/demo")
async def demo_view(request: Request):
    
    return templates.TemplateResponse("auth/demo.html", {"request": request})

@router.get("/forgot-password")
async def forgot_password_view(request: Request):
    """
    Renders the Forgot Password Page.
    File location: templates/auth/forgot_password.html
    """
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request})