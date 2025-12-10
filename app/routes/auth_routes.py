from flask import Blueprint, request, jsonify, current_app
from ..models import User
from ..extensions import db
import os
import requests
from flask_jwt_extended import create_access_token

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


@auth_bp.post('/google-callback')
def google_callback():
    """Recebe o 'code' do frontend, troca por token no Google, obtém perfil
    e cria/obtém usuário local retornando dados e um JWT.
    Espera JSON: { code: string, redirectUri: string }
    """
    data = request.json or {}
    code = data.get('code')
    redirect_uri = data.get('redirectUri')

    if not code:
        return {"success": False, "message": "Código de autorização é obrigatório"}, 400

    # Config via env vars
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    if not client_id or not client_secret:
        current_app.logger.error('Google client ID/secret não configurados')
        return {"success": False, "message": "Server OAuth não configurado"}, 500

    token_url = 'https://oauth2.googleapis.com/token'
    token_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    try:
        token_resp = requests.post(token_url, data=token_payload, timeout=10)
        token_resp.raise_for_status()
        tokens = token_resp.json()
    except Exception as e:
        current_app.logger.exception('Erro ao trocar código por token no Google')
        return {"success": False, "message": "Erro ao trocar código por token", "detail": str(e)}, 502

    access_token = tokens.get('access_token')
    if not access_token:
        return {"success": False, "message": "Token de acesso não recebido do Google", "tokens": tokens}, 502

    # Obter informações do usuário
    userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    try:
        userinfo_resp = requests.get(userinfo_url, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
        userinfo_resp.raise_for_status()
        profile = userinfo_resp.json()
    except Exception as e:
        current_app.logger.exception('Erro ao obter perfil do Google')
        return {"success": False, "message": "Erro ao obter perfil do Google", "detail": str(e)}, 502

    email = profile.get('email')
    name = profile.get('name') or profile.get('given_name') or (email.split('@')[0] if email else 'user')
    google_id = profile.get('sub')
    picture = profile.get('picture')

    if not email:
        return {"success": False, "message": "Email não retornado pelo Google"}, 502

    # Busca ou cria usuário local
    user = User.query.filter_by(email=email).first()
    if not user:
        # Gera username simples a partir do nome
        username = name.replace(' ', '').lower()[:50]
        # Garantir uniqueness simples
        base_username = username
        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{suffix}"
            suffix += 1

        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()

    # Gera JWT
    access_jwt = create_access_token(identity=user.id)

    return {
        "success": True,
        "message": "Autenticação Google realizada com sucesso",
        "user": {"id": user.id, "username": user.username, "email": user.email, "picture": picture},
        "token": access_jwt
    }, 200
