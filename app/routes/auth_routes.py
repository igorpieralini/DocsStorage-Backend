from flask import Blueprint, request, jsonify
from ..models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")

def login():
    if not request.json:
        print("❌ Nenhum dado JSON recebido")
        return {
            "success": False, 
            "message": "Dados JSON são obrigatórios",
            "error_type": "no_data"
        }, 400
    
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    print(f"🔐 Data recebida: {data}")
    print(f"📧 Email: '{email}' | 🔑 Senha: '{password}'")
    
    if not email:
        print("❌ Email vazio")
        return {
            "success": False, 
            "message": "Email é obrigatório",
            "error_type": "missing_email"
        }, 400
    
    if not password:
        print("❌ Senha vazia")
        return {
            "success": False, 
            "message": "Senha é obrigatória",
            "error_type": "missing_password"
        }, 400
    
    user = User.query.filter_by(email=email).first()
    print(f"👤 Usuário encontrado: {user}")
    
    if not user:
        print("❌ Usuário não encontrado no banco")
        return {
            "success": False, 
            "message": f"Usuário com email '{email}' não foi encontrado",
            "error_type": "user_not_found"
        }, 404
    
    print(f"🔍 Senha no banco: '{user.password}' | Digitada: '{password}'")
    senha_ok = user.check_password(password)
    print(f"✅ Check senha: {senha_ok}")
    
    if not senha_ok:
        print("❌ Senha incorreta")
        return {
            "success": False, 
            "message": "Senha incorreta",
            "error_type": "invalid_password"
        }, 401
    
    print("✅ Login OK!")
    return {
        "success": True, 
        "message": "Login realizado com sucesso",
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }, 200
