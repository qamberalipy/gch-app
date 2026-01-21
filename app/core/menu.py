# app/core/menu.py
MENU = {
    "admin": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Users", "icon": "ri-user-line", "path": "/admin_users", "children": []},
        {"label": "Task Assigner", "icon": "ri-task-line", "path": "/task_assigner", "children": []},
        {"label": "Signature Assigner", "icon": "ri-file-text-line", "path": "/signature_assigner", "children": []},
        {"label": "Content Vault", "icon": "ri-folder-line", "path": "/content_vault", "children": []},
        {"label": "Announcements", "icon": "ri-discuss-line", "path": "/admin_feed", "children": []},
    ],
    "manager": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Users", "icon": "ri-user-line", "path": "/manager_users", "children": []},
        {"label": "Task Assigner", "icon": "ri-task-line", "path": "/task_assigner", "children": []},
        {"label": "Signature Assigner", "icon": "ri-file-text-line", "path": "/signature_assigner", "children": []},
        {"label": "Content Vault", "icon": "ri-folder-line", "path": "/content_vault", "children": []},
          {"label": "Announcements", "icon": "ri-announcement-line", "path": "/admin_feed", "children": []},
    ],
    "team_member": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Task Assigner", "icon": "ri-task-line", "path": "/task_assigner", "children": []},
        {"label": "Signature Assigner", "icon": "ri-file-text-line", "path": "/signature_assigner", "children": []},
        {"label": "Content Vault", "icon": "ri-folder-line", "path": "/content_vault", "children": []},
    ],
    "digital_creator": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
        {"label": "Task Submission", "icon": "ri-file-upload-line", "path": "/task_submission", "children": []},
        {"label": "Signature Signer", "icon": "ri-file-text-line", "path": "/signature_signer", "children": []},
        {"label": "Content Vault", "icon": "ri-folder-line", "path": "/content_vault", "children": []},
    ],
    "default": [
        {"label": "Dashboard", "icon": "ri-home-4-line", "path": "/dashboard", "children": []},
    ]
}
