from app.models import User
from app.extensions import db
from sqlalchemy.exc import IntegrityError

def register_user(username, email, password):
    
    import datetime
    import sys
    print(f"[REGISTER][{datetime.datetime.now()}] Tentando registrar: username={username}, email={email}", file=sys.stderr)

    if not username or not username.strip():
        print(f"[REGISTER][{datetime.datetime.now()}] Falha: username vazio", file=sys.stderr)
        return None, 'Nome de usuário não pode ser vazio.'

    elif not email or not email.strip():
        print(f"[REGISTER][{datetime.datetime.now()}] Falha: email vazio", file=sys.stderr)
        return None, 'Email não pode ser vazio.'

    if User.query.filter_by(username=username).first():
        print(f"[REGISTER][{datetime.datetime.now()}] Falha: username já existe", file=sys.stderr)
        return None, 'Nome de usuário já está em uso.'

    if User.query.filter_by(email=email).first():
        print(f"[REGISTER][{datetime.datetime.now()}] Falha: email já cadastrado", file=sys.stderr)
        return None, 'Email já cadastrado.'

    user = User(username=username, email=email, password=password)
    db.session.add(user)

    try:
        print(f"[REGISTER][{datetime.datetime.now()}] Commitando novo usuário...", file=sys.stderr)
        db.session.commit()
        print(f"[REGISTER][{datetime.datetime.now()}] Usuário criado com sucesso: id={user.id}", file=sys.stderr)
    except IntegrityError as e:
        db.session.rollback()
        print(f"[REGISTER][{datetime.datetime.now()}] IntegrityError: {e}", file=sys.stderr)
        return None, 'Erro ao criar usuário.'

    return user, None
