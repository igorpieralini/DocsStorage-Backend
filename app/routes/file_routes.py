from flask import Blueprint, jsonify

file_bp = Blueprint("file", __name__)

@file_bp.get("/")
def list_files():
    return {"files": []}, 200

@file_bp.post("/upload")
def upload_file():
    return {"message": "Upload em desenvolvimento"}, 501
