from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.storage_service import StorageService
from werkzeug.utils import secure_filename
import os
from pathlib import Path

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


@file_bp.get('/download-by-path')
@jwt_required()
def download_by_path():
    """Faz download informando path relativo e nome"""
    user_id = get_jwt_identity()
    relative_path = request.args.get('path', '')
    name = request.args.get('name')
    if not name:
        return {"success": False, "message": "name é obrigatório"}, 400

    try:
        base_dir = StorageService.get_user_directory(user_id, relative_path)
    except ValueError:
        return {"success": False, "message": "Caminho inválido"}, 400

    from pathlib import Path
    file_path = Path(base_dir) / name
    if not file_path.exists():
        return {"success": False, "message": "Arquivo não encontrado"}, 404

    return send_file(str(file_path), as_attachment=False, download_name=name)

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


@file_bp.post('/mkdir')
@jwt_required()
def create_folder():
    """Cria uma nova pasta no caminho informado"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    name = data.get('name')
    relative_path = data.get('path', '')

    if not name or not name.strip():
        return {"success": False, "message": "Nome inválido"}, 400

    # sanitize name
    safe_name = secure_filename(name)
    try:
        target = str(Path(relative_path) / safe_name)
        # StorageService.get_user_directory will create the directory
        StorageService.get_user_directory(user_id, target)
    except ValueError:
        return {"success": False, "message": "Caminho inválido"}, 400

    return {"success": True, "message": "Pasta criada com sucesso", "path": target}, 201


@file_bp.post('/create')
@jwt_required()
def create_file_endpoint():
    """Cria um arquivo vazio no caminho informado"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    name = data.get('name')
    relative_path = data.get('path', '')

    if not name or not name.strip():
        return {"success": False, "message": "Nome inválido"}, 400

    safe_name = secure_filename(name)
    try:
        dir_path = StorageService.get_user_directory(user_id, relative_path)
    except ValueError:
        return {"success": False, "message": "Caminho inválido"}, 400

    file_path = Path(dir_path) / safe_name
    if file_path.exists():
        return {"success": False, "message": "Arquivo já existe"}, 400

    try:
        # create empty file
        file_path.touch()
        return {"success": True, "message": "Arquivo criado", "filename": safe_name}, 201
    except Exception as e:
        return {"success": False, "message": f"Erro ao criar arquivo: {str(e)}"}, 500


@file_bp.post('/move')
@jwt_required()
def move_file():
    """Move/renomeia um arquivo para um destino informado"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    filename = data.get('filename')
    target_path = data.get('target_path', '')

    if not filename:
        return {"success": False, "message": "Filename é obrigatório"}, 400

    # source path
    src = StorageService.get_file_path(user_id, filename)
    if not src:
        return {"success": False, "message": "Arquivo não encontrado"}, 404

    try:
        dest_dir = StorageService.get_user_directory(user_id, target_path)
    except ValueError:
        return {"success": False, "message": "Caminho de destino inválido"}, 400

    dest = Path(dest_dir) / filename
    if dest.exists():
        return {"success": False, "message": "Arquivo de destino já existe"}, 400

    try:
        src.replace(dest)
        return {"success": True, "message": "Arquivo movido"}, 200
    except Exception as e:
        return {"success": False, "message": f"Erro ao mover arquivo: {str(e)}"}, 500
