from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from ..models import User
import os

google_drive_bp = Blueprint('google_drive', __name__, url_prefix='/api/google-drive')

def get_drive_service(user):
    """Cria e retorna um serviço do Google Drive para o usuário."""
    if not user.google_access_token:
        raise ValueError("Usuário não possui token de acesso ao Google")
    
    credentials = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
    )
    
    return build('drive', 'v3', credentials=credentials)

@google_drive_bp.get('/files')
@jwt_required()
def list_files():
    """Lista arquivos do Google Drive do usuário autenticado."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return {"success": False, "message": "Usuário não encontrado"}, 404
        
        # Parâmetros opcionais
        folder_id = request.args.get('folder_id', 'root')
        page_size = int(request.args.get('page_size', 100))
        page_token = request.args.get('page_token')
        
        # Constrói query para listar apenas arquivos na pasta especificada
        query = f"'{folder_id}' in parents and trashed=false"
        
        service = get_drive_service(user)
        
        # Campos que queremos retornar
        fields = "nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, iconLink, thumbnailLink)"
        
        # Parâmetros da requisição
        params = {
            'q': query,
            'pageSize': page_size,
            'fields': fields,
            'orderBy': 'folder,name'
        }
        
        if page_token:
            params['pageToken'] = page_token
        
        results = service.files().list(**params).execute()
        files = results.get('files', [])
        next_page_token = results.get('nextPageToken')
        
        # Formata os arquivos para um formato mais amigável
        formatted_files = []
        for file in files:
            formatted_files.append({
                'id': file['id'],
                'name': file['name'],
                'type': 'folder' if file['mimeType'] == 'application/vnd.google-apps.folder' else 'file',
                'mime_type': file['mimeType'],
                'size': file.get('size', 0),
                'modified_at': file['modifiedTime'],
                'web_view_link': file.get('webViewLink'),
                'icon_link': file.get('iconLink'),
                'thumbnail_link': file.get('thumbnailLink')
            })
        
        return {
            "success": True,
            "files": formatted_files,
            "count": len(formatted_files),
            "next_page_token": next_page_token
        }, 200
        
    except ValueError as ve:
        current_app.logger.error(f'Erro de valor ao listar arquivos do Drive: {str(ve)}')
        return {"success": False, "message": str(ve)}, 400
        
    except Exception as e:
        current_app.logger.exception('Erro ao listar arquivos do Google Drive')
        return {"success": False, "message": "Erro ao listar arquivos do Google Drive", "detail": str(e)}, 500

@google_drive_bp.get('/file/<file_id>')
@jwt_required()
def get_file_metadata(file_id):
    """Obtém metadados de um arquivo específico do Google Drive."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return {"success": False, "message": "Usuário não encontrado"}, 404
        
        service = get_drive_service(user)
        
        file = service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, modifiedTime, webViewLink, iconLink, thumbnailLink, parents'
        ).execute()
        
        return {
            "success": True,
            "file": {
                'id': file['id'],
                'name': file['name'],
                'type': 'folder' if file['mimeType'] == 'application/vnd.google-apps.folder' else 'file',
                'mime_type': file['mimeType'],
                'size': file.get('size', 0),
                'modified_at': file['modifiedTime'],
                'web_view_link': file.get('webViewLink'),
                'icon_link': file.get('iconLink'),
                'thumbnail_link': file.get('thumbnailLink'),
                'parents': file.get('parents', [])
            }
        }, 200
        
    except Exception as e:
        current_app.logger.exception(f'Erro ao obter metadados do arquivo {file_id}')
        return {"success": False, "message": "Erro ao obter arquivo", "detail": str(e)}, 500
