# 🖥️ DocsStorage Backend

API REST em Python/Flask para gerenciamento de documentos com autenticação JWT e integração OAuth.

## 🚀 Tecnologias
- Python 3.8+
- Flask + SQLAlchemy
- MySQL Database
- JWT Authentication
- CORS Support

## ⚡ Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
**Server:** http://127.0.0.1:5000

## 🔧 Configuração

**Database** (`app/config.py`):
```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:password@localhost:3306/docsstorage"
```

## 🔐 Google OAuth (Login via Google)

O backend espera as seguintes variáveis de ambiente para habilitar o fluxo OAuth do Google:

- `GOOGLE_CLIENT_ID` — Client ID do OAuth criado no Google Cloud Console
- `GOOGLE_CLIENT_SECRET` — Client Secret do OAuth (mantenha em segredo)

Exemplo para definir temporariamente no PowerShell (sessão atual):

```powershell
$env:GOOGLE_CLIENT_ID = 'seu-client-id.apps.googleusercontent.com'
$env:GOOGLE_CLIENT_SECRET = 'seu-client-secret'
python app.py
```

Para produção, configure essas variáveis no ambiente do servidor (não coloque o secret no frontend). O `redirect_uri` usado pelo frontend é `http://localhost:4200/oauth/callback` por padrão — mantenha esse valor registrado nas credenciais do Google durante testes locais.

Recomendações de segurança:
- Use `state` para prevenir CSRF no fluxo OAuth (implementar no frontend/backend).
- Verifique o `id_token` retornado pelo Google (assinatura e claims) em produção.


**Criar Admin:**
```bash
python -c "from app import create_app; from app.extensions import db; from app.models import User; app=create_app(); app.app_context().__enter__(); db.create_all(); user=User(username='admin', email='admin@admin.com'); user.set_password('admin123'); db.session.add(user); db.session.commit(); print('Admin criado!')"
```

## 📝 API Endpoints
- `GET /` - Status da API
- `POST /api/auth/login` - Login tradicional
- `GET /api/files` - Listar arquivos do usuário
- `POST /api/files/upload` - Upload de arquivo
- `GET /api/files/<id>` - Download arquivo
- `DELETE /api/files/<id>` - Deletar arquivo

## 🔐 Autenticação
Login retorna JWT token para autorização:
```json
{
  "success": true,
  "message": "Login realizado com sucesso",
  "user": {"id": 1, "username": "admin", "email": "admin@admin.com"},
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---
**Backend API | DocsStorage 2025**