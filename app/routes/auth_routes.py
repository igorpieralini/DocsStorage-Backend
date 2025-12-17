from flask import Blueprint, request, jsonify, current_app
from ..models import User
from ..extensions import db
import os
import requests
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.email_service import send_email
from app.services.auth_register_service import register_user
from app.services.auth_login_service import authenticate_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    
    if not request.json:
        return {"success": False, "message": "Dados JSON são obrigatórios", "error_type": "no_data"}, 400
    
    data = request.json
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    user, error = register_user(username, email, password)

    if error:
        return {"success": False, "message": error, "error_type": "register_failed"}, 409
    
    token = create_access_token(identity=str(user.id))

    return {
        "success": True,
        "message": "Conta criada com sucesso",
        "user": {"id": user.id, "username": user.username, "email": user.email},
        "token": token
    }, 201

@auth_bp.post("/login")

def login():
    if not request.json:
        return {
            "success": False, 
            "message": "Dados JSON são obrigatórios",
            "error_type": "no_data"
        }, 400
    
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    
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

    if not user:
        print("❌ Usuário não encontrado no banco")
        return {
            "success": False, 
            "message": f"Usuário com email '{email}' não foi encontrado",
            "error_type": "user_not_found"
        }, 404
    
    senha_ok = user.check_password(password)
    
    if not senha_ok:
        return {
            "success": False, 
            "message": "Senha incorreta",
            "error_type": "invalid_password"
        }, 401
    
    token = create_access_token(identity=str(user.id))
    
    return {
        "success": True, 
        "message": "Login realizado com sucesso",
        "user": {"id": user.id, "username": user.username, "email": user.email},
        "token": token
    }, 200


@auth_bp.put('/profile')
@jwt_required()
def update_profile():
    """Atualiza nome/username e dispara email de notificação"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    username = (data.get('username') or '').strip()
    photo_changed = bool(data.get('photo_changed'))

    user = User.query.filter_by(id=int(user_id)).first()
    if not user:
        return {"success": False, "message": "Usuário não encontrado"}, 404

    changed_fields = []

    if username and username != user.username:
        existing = User.query.filter(User.username == username, User.id != user.id).first()
        if existing:
            return {"success": False, "message": "Username já está em uso"}, 409
        user.username = username
        changed_fields.append('username')

    if name and name != getattr(user, 'name', None):
        try:
            setattr(user, 'name', name)
            changed_fields.append('nome')
        except Exception:
            pass

    if photo_changed:
        changed_fields.append('foto de perfil')

    db.session.commit()

    # envia email se houve alteração relevante
    if changed_fields:
        subject = 'Seu perfil foi atualizado'
        body = (
            "Olá,\n\n"
            f"Detectamos uma atualização no seu perfil: {', '.join(changed_fields)}.\n"
            "Se não foi você, revise sua conta e altere sua senha.\n\n"
            "— Equipe DocsStorage"
        )
        send_email(user.email, subject, body)

    return {
        "success": True,
        "message": "Perfil atualizado",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": getattr(user, 'name', None)
        }
    }, 200


@auth_bp.post('/google-callback')
def google_callback():
    data = request.json or {}
    import datetime
    code = data.get('code')
    redirect_uri = data.get('redirectUri')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    

    if not code:
        return {"success": False, "message": "Código de autorização é obrigatório"}, 400

    # Config via env vars
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    

    if not client_id or not client_secret:
        print('❌ [Google Callback] Google client ID/secret não configurados')
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
    

    token_resp = requests.post(token_url, data=token_payload, timeout=10)
    if token_resp.status_code == 400:

        # Tenta extrair erro específico do Google
        try:
            err_json = token_resp.json()
            if err_json.get('error') == 'invalid_grant':
                # invalid_grant pode indicar code expirado/já usado ou redirect_uri incorreto
                return {"success": False, "message": "Código expirado, já utilizado ou inválido. Faça login novamente."}, 400
        except Exception:
            pass

    token_resp.raise_for_status()
    tokens = token_resp.json()


    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')

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
        username = name.replace(' ', '').lower()[:50]
        base_username = username

        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{suffix}"
            suffix += 1

        user = User(
            username=username, 
            email=email, 
            google_id=google_id, 
            profile_picture=picture,
            google_access_token=access_token,
            google_refresh_token=refresh_token
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Atualiza foto, google_id e tokens se mudou
        updated = False
        if user.profile_picture != picture:
            user.profile_picture = picture
            updated = True
        if user.google_id != google_id:
            user.google_id = google_id
            updated = True
        if user.google_access_token != access_token:
            user.google_access_token = access_token
            updated = True
        if refresh_token and user.google_refresh_token != refresh_token:
            user.google_refresh_token = refresh_token
            updated = True
        if updated:
            db.session.commit()

    # Gera JWT
    access_jwt = create_access_token(identity=str(user.id))

    response_dict = {
        "success": True,
        "message": "Autenticação Google realizada com sucesso",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "picture": picture,
            "profile_picture": picture
        },
        "token": access_jwt
    }
    
    return response_dict, 200
