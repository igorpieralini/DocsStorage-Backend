from flask import Blueprint, request, jsonify

file_bp = Blueprint("file", __name__)

@file_bp.route("/upload", methods=["POST"])
def upload_file():
    return jsonify({"message": "arquivo recebido"})
