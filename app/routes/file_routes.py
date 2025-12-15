from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.storage_service import StorageService
from werkzeug.utils import secure_filename
import os

file_bp = Blueprint("file", __name__)

@file_bp.get("/")
@jwt_required()
def list_files():
    """Lista arquivos e pastas do usuário no caminho informado"""
    user_id = get_jwt_identity()
    relative_path = request.args.get('path', '')

    try:
        entries = StorageService.list_user_entries(user_id, relative_path)
    except ValueError:
        return {
            "success": False,
            "message": "Caminho inválido"
        }, 400
    
    return {
        "success": True,
        "items": entries,
        "count": len(entries),
        "path": relative_path
    }, 200

@file_bp.get("/storage-info")
@jwt_required()
def storage_info():
    """Retorna informações sobre o storage do usuário"""
    user_id = get_jwt_identity()
    user_info = StorageService.get_user_storage_info(user_id)
    global_info = StorageService.get_storage_info()
    
    return {
        "success": True,
        "user_storage": {
            "used_bytes": user_info['used'],
            "used_mb": round(user_info['used'] / (1024 * 1024), 2),
            "used_gb": round(user_info['used'] / (1024 * 1024 * 1024), 2),
            "max_bytes": user_info['max'],
            "max_gb": round(user_info['max'] / (1024 * 1024 * 1024), 2),
            "available_bytes": user_info['available'],
            "available_gb": round(user_info['available'] / (1024 * 1024 * 1024), 2),
            "percentage": user_info['percentage'],
            "files_count": user_info['files_count']
        },
        "global_storage": {
            "used_bytes": global_info['used'],
            "used_gb": round(global_info['used'] / (1024 * 1024 * 1024), 2),
            "max_gb": round(global_info['max'] / (1024 * 1024 * 1024), 2),
            "percentage": global_info['percentage']
        }
    }, 200

@file_bp.post("/upload")
@jwt_required()
def upload_file():
    """Faz upload de um arquivo"""
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return {
            "success": False,
            "message": "Nenhum arquivo enviado"
        }, 400
    
    file = request.files['file']
    
    if file.filename == '':
        return {
            "success": False,
            "message": "Nome do arquivo vazio"
        }, 400
    
    result, error = StorageService.save_file(file, user_id)
    
    if error:
        return {
            "success": False,
            "message": error
        }, 400
    
    return {
        "success": True,
        "message": "Arquivo enviado com sucesso",
        "file": result
    }, 201

@file_bp.get("/download/<filename>")
@jwt_required()
def download_file(filename):
    """Faz download de um arquivo"""
    user_id = get_jwt_identity()
    
    file_path = StorageService.get_file_path(user_id, filename)
    
    if not file_path:
        return {
            "success": False,
            "message": "Arquivo não encontrado"
        }, 404
    
    # Extrai o nome original (remove timestamp e hash)
    parts = filename.split('_', 2)
    original_name = parts[2] if len(parts) > 2 else filename
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=original_name
    )

@file_bp.delete("/delete/<filename>")
@jwt_required()
def delete_file(filename):
    """Deleta um arquivo"""
    user_id = get_jwt_identity()
    
    success, message = StorageService.delete_file(user_id, filename)
    
    if not success:
        return {
            "success": False,
            "message": message
        }, 404
    
    return {
        "success": True,
        "message": message
    }, 200
