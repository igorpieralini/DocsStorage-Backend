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
    # Prints de debug serão feitos após obter profile e user
    """Recebe o 'code' do frontend, troca por token no Google, obtém perfil
    e cria/obtém usuário local retornando dados e um JWT.
    Espera JSON: { code: string, redirectUri: string }
    """

    data = request.json or {}
    import datetime
    print('🔵 [Google Callback] JSON recebido:', data)
    code = data.get('code')
    redirect_uri = data.get('redirectUri')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f'🔵 [Google Callback] code: {code} | horário: {now}')
    print(f'🔵 [Google Callback] redirect_uri: {redirect_uri}')

    if not code:
        print('❌ [Google Callback] Código de autorização ausente!')
        return {"success": False, "message": "Código de autorização é obrigatório"}, 400

    # Config via env vars
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    print(f'🔵 [Google Callback] client_id: {client_id}')
    print(f'🔵 [Google Callback] client_secret: {client_secret}')

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
    print('🔵 [Google Callback] token_payload:', token_payload)


    try:
        print('🔵 [Google Callback] Solicitando token ao Google...')
        token_resp = requests.post(token_url, data=token_payload, timeout=10)
        print('🔵 [Google Callback] Status da resposta do token:', token_resp.status_code)
        print('🔵 [Google Callback] Conteúdo da resposta do token:', token_resp.text)
        if token_resp.status_code == 400:
            # Tenta extrair erro específico do Google
            try:
                err_json = token_resp.json()
                if err_json.get('error') == 'invalid_grant':
                    print('❌ [Google Callback] invalid_grant: code expirado, já usado ou redirect_uri incorreto.')
                    return {"success": False, "message": "Código expirado, já utilizado ou inválido. Faça login novamente."}, 400
            except Exception:
                pass
        token_resp.raise_for_status()
        tokens = token_resp.json()
        print('🔵 [Google Callback] Tokens recebidos:', tokens)
    except Exception as e:
        print('❌ [Google Callback] Erro ao trocar código por token:', str(e))
        current_app.logger.exception('Erro ao trocar código por token no Google')
        return {"success": False, "message": "Erro ao trocar código por token", "detail": str(e)}, 502

    access_token = tokens.get('access_token')
    print(f'🔵 [Google Callback] access_token: {access_token}')
    if not access_token:
        print('❌ [Google Callback] Token de acesso não recebido do Google!')
        return {"success": False, "message": "Token de acesso não recebido do Google", "tokens": tokens}, 502

    # Obter informações do usuário
    userinfo_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    try:
        print('🔵 [Google Callback] Solicitando perfil do usuário ao Google...')
        userinfo_resp = requests.get(userinfo_url, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
        print('🔵 [Google Callback] Status da resposta do userinfo:', userinfo_resp.status_code)
        print('🔵 [Google Callback] Conteúdo da resposta do userinfo:', userinfo_resp.text)
        userinfo_resp.raise_for_status()
        profile = userinfo_resp.json()
        print('🔵 [Google Callback] Perfil recebido:', profile)
    except Exception as e:
        print('❌ [Google Callback] Erro ao obter perfil do Google:', str(e))
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

        user = User(username=username, email=email, google_id=google_id, profile_picture=picture)
        db.session.add(user)
        db.session.commit()
    else:
        # Atualiza foto e google_id se mudou
        updated = False
        if user.profile_picture != picture:
            user.profile_picture = picture
            updated = True
        if user.google_id != google_id:
            user.google_id = google_id
            updated = True
        if updated:
            db.session.commit()

    # Gera JWT
    access_jwt = create_access_token(identity=user.id)

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
    print('🔴 JSON enviado ao frontend:', response_dict)
    return response_dict, 200
