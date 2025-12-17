from .extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255))  # Aumentado para suportar hash seguro
    google_id = db.Column(db.String(64), unique=True)
    profile_picture = db.Column(db.String(255))
    google_access_token = db.Column(db.Text)
    google_refresh_token = db.Column(db.Text)

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password
