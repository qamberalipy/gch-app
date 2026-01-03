from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

user_view = APIRouter(include_in_schema=False)

@user_view.get("/dashboard")
async def dashboard_view(request: Request):
    """
    Renders the Main Dashboard (Stats/Charts).
    File location: templates/dashboard.html
    """
    # You need to create a simple dashboard.html or point this to user.html if that's your home
    return templates.TemplateResponse("dashboard.html", {"request": request}) 

@user_view.get("/users")
async def users_list_view(request: Request):
    """
    Renders the User List / Expense Table.
    File location: templates/user.html (Based on your previous shared code)
    """
    return templates.TemplateResponse("user.html", {"request": request})

@user_view.get("/profile")
async def profile_view(request: Request):
    """
    Renders the User Profile Settings.
    File location: templates/profile.html
    """
    # Ensure you create a profile.html file
    return templates.TemplateResponse("profile.html", {"request": request})

@user_view.get("/settings",response_class=HTMLResponse)
async def settings_view(request: Request):
    """
    Renders the General Application Settings.
    File location: templates/settings.html
    """
    # Ensure you create a settings.html file
    return templates.TemplateResponse("settings.html", {"request": request})

@user_view.get("/about")
async def about_view(request: Request):
    """
    Renders the About Page.
    File location: templates/about.html
    """
    return templates.TemplateResponse("about.html", {"request": request})