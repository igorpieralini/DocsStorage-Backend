from app.models import User
import sys
from datetime import datetime

def authenticate_user(email, password):
    print(f"[LOGIN][{datetime.now()}] Tentando autenticar: {email}", file=sys.stderr)
    
    if not email or not email.strip():
        return None, "Email é obrigatório"
    
    if not password or not password.strip():
        return None, "Senha é obrigatória"
    
    user = User.query.filter_by(email=email.strip()).first()
    
    if not user:
        print(f"[LOGIN][{datetime.now()}] Usuário não encontrado: {email}", file=sys.stderr)
        return None, "Usuário não encontrado"
    
    if not user.check_password(password):
        print(f"[LOGIN][{datetime.now()}] Senha incorreta para: {email}", file=sys.stderr)
        return None, "Senha incorreta"
    
    print(f"[LOGIN][{datetime.now()}] Login bem-sucedido: {email} (id={user.id})", file=sys.stderr)
    return user, None
