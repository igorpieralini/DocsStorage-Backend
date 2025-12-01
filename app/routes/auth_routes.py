from flask import Blueprint, request
from ..queries.auth import check_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    result = check_user(email, password)

    return result, 200 if result["success"] else 401
