# app/core/menu.py
MENU = {
    "admin": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Users", "icon": "ri-user-line", "path": "/admin_users", "children": []},
        {"label": "Task Assigner", "icon": "ri-task-line", "path": "/task_assigner", "children": []},
        {"label": "Signature Assigner", "icon": "ri-file-text-line", "path": "/signature_assigner", "children": []},
    ],
    "manager": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Users", "icon": "ri-user-line", "path": "/manager_users", "children": []},
        {"label": "Task Assigner", "icon": "ri-task-line", "path": "/task_assigner", "children": []},
        {"label": "Signature Assigner", "icon": "ri-file-text-line", "path": "/signature_assigner", "children": []},
    ],
    "team_member": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Task Assigner", "icon": "ri-task-line", "path": "/task_assigner", "children": []},
        {"label": "Signature Assigner", "icon": "ri-file-text-line", "path": "/signature_assigner", "children": []},
    ],
    "digital_creator": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Task Submission", "icon": "ri-file-upload-line", "path": "/task_submission", "children": []},
        {"label": "Signature Signer", "icon": "ri-file-text-line", "path": "/signature_signer", "children": []},
    ],
    "default": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
    ]
}
