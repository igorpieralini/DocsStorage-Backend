from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"msg": "username, email and password required"}), 400
    if User.query.filter((User.username==username) | (User.email==email)).first():
        return jsonify({"msg": "user already exists"}), 400
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "user created"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter((User.username==username) | (User.email==username)).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "bad username or password"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "access_token": access_token,
        "user": {"id": user.id, "username": user.username, "email": user.email}
    }), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = User.query.get(uid)
    return jsonify({"id": user.id, "username": user.username, "email": user.email})
