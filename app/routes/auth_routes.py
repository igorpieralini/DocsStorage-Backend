from flask import Blueprint, request, jsonify
from ..models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    data = request.json
    email = data.get("email") if data else None
    password = data.get("password") if data else None
    
    print(f"🔐 Data recebida: {data}")
    print(f"📧 Email: '{email}' | 🔑 Senha: '{password}'")
    
    if not email or not password:
        print("❌ Email ou senha vazios")
        return {"success": False, "message": "Email e senha são obrigatórios"}, 400
    
    user = User.query.filter_by(email=email).first()
    print(f"👤 Usuário encontrado: {user}")
    
    if user:
        print(f"🔍 Senha no banco: '{user.password}' | Digitada: '{password}'")
        senha_ok = user.check_password(password)
        print(f"✅ Check senha: {senha_ok}")
    else:
        print("❌ Usuário não encontrado no banco")
    
    if not user or not user.check_password(password):
        print("❌ Falha na autenticação")
        return {"success": False, "message": "Credenciais inválidas"}, 401
    
    print("✅ Login OK!")
    return {
        "success": True, 
        "message": "Login realizado com sucesso",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }, 200
