![TABLICA](https://github.com/user-attachments/assets/bc54746e-1b9e-4839-b0c1-6716cfbebc46)
# INFOBoard

**INFOBoard** is a Django-based web application that enables users to create, edit, and collaborate on digital boards (powered by Excalidraw) in real time. The project is designed for educational and team collaboration purposes and includes features like real-time collaboration, logging of board events, user and group management, and multi-architecture Docker deployments.

## Features

- **Board Creation & Editing:** Create and edit digital boards collaboratively.
- **Read-Only Mode:** View boards without editing permissions.
- **Collaboration Logging:** Track board events such as full syncs and element changes.
- **Custom User Management:** Uses a custom UUID-based user model for enhanced privacy and user aliasing.
- **Group Access Control:** Organize boards into groups (via the `BoardGroups` model) for structured access.
- **File Handling:** Manage board-associated files using the `ExcalidrawFile` model.
- **Multi-Architecture Docker Build:** Build and push Docker images for multiple architectures using GitHub Actions.

## Requirements

- Python 3.8 or later
- Django 3.2+ (or a compatible version)
- A database (e.g., PostgreSQL, SQLite, etc.)
- Docker (optional, for containerized deployment)
