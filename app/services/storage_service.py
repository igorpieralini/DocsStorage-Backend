import os
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
import hashlib
import datetime

class StorageService:
    """Serviço para gerenciar armazenamento de arquivos"""
    
    @staticmethod
    def initialize_storage():
        """Cria a estrutura de diretórios se não existir"""
        storage_path = current_app.config['STORAGE_PATH']
        
        if not storage_path.exists():
            print(f"📁 Criando diretório de storage: {storage_path}")
            storage_path.mkdir(parents=True, exist_ok=True)
            print("✅ Diretório criado com sucesso")
        else:
            print(f"✅ Diretório de storage já existe: {storage_path}")
        
        return storage_path
    
    @staticmethod
    def get_storage_info():
        """Retorna informações sobre o storage"""
        storage_path = current_app.config['STORAGE_PATH']
        max_size = current_app.config['MAX_STORAGE_SIZE']
        
        if not storage_path.exists():
            return {
                'used': 0,
                'max': max_size,
                'available': max_size,
                'percentage': 0,
                'files_count': 0
            }
        
        total_size = 0
        files_count = 0
        
        for root, dirs, files in os.walk(storage_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.exists():
                    total_size += file_path.stat().st_size
                    files_count += 1
        
        return {
            'used': total_size,
            'max': max_size,
            'available': max_size - total_size,
            'percentage': round((total_size / max_size) * 100, 2) if max_size > 0 else 0,
            'files_count': files_count
        }
    
    @staticmethod
    def has_space_available(file_size):
        """Verifica se há espaço disponível para um novo arquivo"""
        info = StorageService.get_storage_info()
        return info['available'] >= file_size
    
    @staticmethod
    def get_user_directory(user_id):
        """Retorna o diretório do usuário, criando se necessário"""
        storage_path = current_app.config['STORAGE_PATH']
        user_dir = storage_path / f"user_{user_id}"
        
        if not user_dir.exists():
            user_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Diretório criado para usuário {user_id}")
        
        return user_dir
    
    @staticmethod
    def save_file(file, user_id, original_filename=None):
        """Salva um arquivo no storage do usuário"""
        if not original_filename:
            original_filename = file.filename
        
        # Valida tamanho máximo por arquivo
        max_file_size = current_app.config['MAX_FILE_SIZE']
        file.seek(0, 2)  # Move para o final do arquivo
        file_size = file.tell()
        file.seek(0)  # Volta para o início
        
        if file_size > max_file_size:
            return None, f'Arquivo muito grande. Máximo permitido: {max_file_size / (1024*1024):.0f}MB'
        
        # Verifica espaço disponível no storage
        if not StorageService.has_space_available(file_size):
            return None, 'Espaço de armazenamento esgotado (limite de 10GB)'
        
        # Gera nome seguro e único
        filename = secure_filename(original_filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_hash = hashlib.md5(f"{user_id}_{timestamp}_{filename}".encode()).hexdigest()[:8]
        unique_filename = f"{timestamp}_{unique_hash}_{filename}"
        
        # Salva o arquivo
        user_dir = StorageService.get_user_directory(user_id)
        file_path = user_dir / unique_filename
        
        try:
            file.save(str(file_path))
            print(f"✅ Arquivo salvo: {file_path}")
            return {
                'filename': unique_filename,
                'original_filename': original_filename,
                'size': file_size,
                'path': str(file_path.relative_to(current_app.config['STORAGE_PATH']))
            }, None
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return None, f'Erro ao salvar arquivo: {str(e)}'
    
    @staticmethod
    def delete_file(user_id, filename):
        """Remove um arquivo do storage"""
        user_dir = StorageService.get_user_directory(user_id)
        file_path = user_dir / filename
        
        if not file_path.exists():
            return False, 'Arquivo não encontrado'
        
        try:
            file_path.unlink()
            print(f"🗑️ Arquivo deletado: {file_path}")
            return True, 'Arquivo deletado com sucesso'
        except Exception as e:
            print(f"❌ Erro ao deletar arquivo: {e}")
            return False, f'Erro ao deletar arquivo: {str(e)}'
    
    @staticmethod
    def get_file_path(user_id, filename):
        """Retorna o caminho completo de um arquivo"""
        user_dir = StorageService.get_user_directory(user_id)
        file_path = user_dir / filename
        
        if file_path.exists():
            return file_path
        return None
    
    @staticmethod
    def list_user_files(user_id):
        """Lista todos os arquivos de um usuário"""
        user_dir = StorageService.get_user_directory(user_id)
        
        if not user_dir.exists():
            return []
        
        files = []
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'created_at': datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(files, key=lambda x: x['created_at'], reverse=True)
