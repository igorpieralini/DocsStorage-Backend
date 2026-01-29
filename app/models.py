from .extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255))  # Texto plano (banco existente)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    google_id = db.Column(db.String(64), unique=True)
    profile_picture = db.Column(db.String(255))
    google_access_token = db.Column(db.Text)
    google_refresh_token = db.Column(db.Text)

    def set_password(self, password):
        """Define a senha do usuário (texto plano para compatibilidade)"""
        self.password = password

    def check_password(self, password):
        """Verifica se a senha está correta"""
        if not self.password:
            return False
        return self.password == password
    
    def to_dict(self):
        """Retorna dados do usuário como dicionário"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'profile_picture': self.profile_picture,
            'google_id': self.google_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
