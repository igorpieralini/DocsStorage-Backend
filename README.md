# 🖥️ DocsStorage Backend API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![JWT](https://img.shields.io/badge/JWT-Auth-red)

A modern RESTful API for document management with OAuth integration and cloud storage support.

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Database Migration](#-database-migration)
- [Developer](#-developer)

---

## ✨ Features

- 🔐 **Multi-Auth System**: Traditional login + OAuth (Google & Microsoft)
- 📁 **Document Management**: Upload, download, organize files and folders
- ☁️ **Cloud Integration**: Google Drive API integration
- 👤 **User Management**: Profile, storage quotas, permissions
- 🔒 **JWT Authentication**: Secure token-based authentication
- 📧 **Email Notifications**: SMTP integration for user notifications
- 🗄️ **Database**: MySQL with SQLAlchemy ORM
- 🌐 **CORS Support**: Cross-origin requests enabled
- 📊 **Storage Quotas**: Per-user and global storage limits

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.11+ | Programming language |
| **Flask** | 2.3.3 | Web framework |
| **SQLAlchemy** | 3.0.5 | ORM for database |
| **MySQL** | 8.0+ | Relational database |
| **PyMySQL** | 1.1.0 | MySQL connector |
| **Flask-JWT-Extended** | 4.5.2 | JWT authentication |
| **Flask-CORS** | 3.0.10 | CORS support |
| **Google API Client** | 2.108.0 | Google Drive integration |
| **Requests** | 2.31.0 | HTTP library for OAuth |

---

## 🏗️ Architecture

```
backend/
├── app/
│   ├── __init__.py    
│   ├── config.py           
│   ├── extensions.py  
│   ├── models.py            
│   ├── routes/               
│   │   ├── auth_routes.py    
│   │   ├── file_routes.py    
│   │   └── google_drive_routes.py  
│   └── services/             
│       ├── auth_login_service.py
│       ├── auth_register_service.py
│       ├── email_service.py
│       └── storage_service.py
├── app.py                  
├── requirements.txt        
└── .env.example             
```

### Design Patterns

- **Factory Pattern**: Flask app creation with `create_app()`
- **Blueprint Pattern**: Modular route organization
- **Service Layer**: Business logic separated from routes
- **Repository Pattern**: Data access through SQLAlchemy models

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/DocsStorage.git
   cd DocsStorage/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

6. **Create database**
   ```sql
   CREATE DATABASE docsstorage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

7. **Run migrations**
   ```bash
   python -c "from app import create_app; from app.extensions import db; app=create_app(); app.app_context().__enter__(); db.create_all()"
   ```

8. **Run the server**
   ```bash
   python app.py
   ```

   Server will start at: **http://127.0.0.1:5000**

---

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | ❌ |
| POST | `/api/auth/login` | Login with credentials | ❌ |
| POST | `/api/auth/google-callback` | Google OAuth callback | ❌ |
| POST | `/api/auth/microsoft/callback` | Microsoft OAuth callback | ❌ |

### File Management Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/files/` | List user files | ✅ |
| POST | `/api/files/upload` | Upload file | ✅ |
| GET | `/api/files/download/:filename` | Download file | ✅ |
| GET | `/api/files/download-by-path` | Download by path | ✅ |
| POST | `/api/files/mkdir` | Create folder | ✅ |
| POST | `/api/files/create` | Create empty file | ✅ |
| DELETE | `/api/files/delete/:filename` | Delete file | ✅ |
| POST | `/api/files/move` | Move file | ✅ |
| GET | `/api/files/storage-info` | Get storage info | ✅ |

### Google Drive Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/google-drive/files` | List Google Drive files | ✅ |
| GET | `/api/google-drive/file/:id` | Get file metadata | ✅ |

### Example Request

```bash
# Login
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Upload file (with JWT token)
curl -X POST http://127.0.0.1:5000/api/files/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"
```

---

## ⚙️ Configuration

### Database Configuration

Edit `app/config.py`:

```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:password@localhost:3306/docsstorage"
```

### Storage Configuration

```python
STORAGE_PATH = Path("C:/Users/YourUser/Documents/Storage")
MAX_STORAGE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB total
MAX_USER_STORAGE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB per user
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
```

### OAuth Configuration

1. **Google OAuth**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create project and enable Google Drive API
   - Create OAuth 2.0 credentials
   - Add to `.env`: `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Add redirect URI: `http://localhost:4200/oauth/callback`

2. **Microsoft OAuth**
   - Visit [Azure Portal](https://portal.azure.com/)
   - Register application
   - Add API permissions: `User.Read`, `Files.ReadWrite.All`
   - Add to `.env`: `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID`

---

## 🗄️ Database Migration

### Add Google Drive Token Columns

```bash
python migrate_add_google_tokens.py
```

This will add `google_access_token` and `google_refresh_token` columns to the `users` table.

---

## 🧪 Testing

```bash
# Run tests (if available)
pytest

# Check API health
curl http://127.0.0.1:5000/
```

---

## 📦 Deployment

### Production Considerations

1. **Use a production WSGI server** (Gunicorn, uWSGI)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set environment variables** for production
3. **Use HTTPS** for secure communication
4. **Configure CORS** for your frontend domain
5. **Set strong JWT secrets**
6. **Enable database backups**
7. **Monitor logs and errors**

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Developer

**Developed with by Igor Pieralini**

---

<div align="center">
  <sub>Built with Flask, Python, and lots of ☕</sub>
</div>