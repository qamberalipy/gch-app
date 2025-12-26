from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

# Point to the root templates folder
templates = Jinja2Templates(directory="templates")

# include_in_schema=False hides this from the API Docs
router = APIRouter(include_in_schema=False)

@router.get("/")
async def root_view(request: Request):
    """
    Redirects root to login page or renders login directly.
    File location: templates/auth/login.html
    """
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/login")
async def login_view(request: Request):
    """
    Explicit login route (needed for JS redirects).
    File location: templates/auth/login.html
    """
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/forgot-password")
async def forgot_password_view(request: Request):
    """
    Renders the Forgot Password Page.
    File location: templates/auth/forgot-password.html
    """
    return templates.TemplateResponse("auth/forgot-password.html", {"request": request})

@router.get("/reset-password")
async def reset_password_view(request: Request):
    """
    Renders the Reset Password Page (User lands here from Email Link or after OTP flow).
    File location: templates/auth/reset-password.html
    """
    return templates.TemplateResponse("auth/reset-password.html", {"request": request})

@router.get("/demo")
async def demo_view(request: Request):
    """
    Dashboard/Demo view after successful login.
    File location: templates/auth/demo.html
    """
    return templates.TemplateResponse("auth/demo.html", {"request": request})

@router.get("/dashboard")
async def dashboard_view(request: Request):
    """
    Main Dashboard view after successful login.
    File location: templates/dashboard.html
    """
    return templates.TemplateResponse("user.html", {"request": request})