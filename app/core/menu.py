# app/core/menu.py
MENU = {
    "admin": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Users", "icon": "ri-user-line", "path": "/admin_users", "children": []},
    ],
    "manager": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
         {"label": "Users", "icon": "ri-user-line", "path": "/manager_users", "children": []},
    ],
    "team_member": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
    ],
    "digital_creator": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
    ],
    "default": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
    ]
}
