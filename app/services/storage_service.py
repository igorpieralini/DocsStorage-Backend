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
        """Cria a estrutura de diretórios se não existir e reserva pastas para todos os usuários"""
        from app.models import User
        
        storage_path = current_app.config['STORAGE_PATH']
        
        if not storage_path.exists():
            print(f"📁 Criando diretório de storage: {storage_path}")
            storage_path.mkdir(parents=True, exist_ok=True)
            print("✅ Diretório criado com sucesso")
        else:
            print(f"✅ Diretório de storage já existe: {storage_path}")
        
        # Cria pastas para todos os usuários existentes
        users = User.query.all()
        for user in users:
            user_dir = storage_path / f"user_{user.id}"
            if not user_dir.exists():
                user_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 Pasta reservada para usuário {user.id}: {user_dir}")
        
        if users:
            print(f"✅ {len(users)} pastas de usuário criadas/verificadas")
        
        return storage_path
    
    @staticmethod
    def get_storage_info():
        """Retorna informações sobre o storage global (todos os usuários)"""
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
    def get_user_storage_info(user_id):
        """Retorna informações sobre o storage de um usuário específico"""
        user_dir = StorageService.get_user_directory(user_id)
        max_user_size = current_app.config['MAX_USER_STORAGE_SIZE']

        if not user_dir.exists():
            return {
                'used': 0,
                'max': max_user_size,
                'available': max_user_size,
                'percentage': 0,
                'files_count': 0
            }

        total_size = 0
        files_count = 0

        for file_path in user_dir.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                files_count += 1

        return {
            'used': total_size,
            'max': max_user_size,
            'available': max_user_size - total_size,
            'percentage': round((total_size / max_user_size) * 100, 2) if max_user_size > 0 else 0,
            'files_count': files_count
        }
    
    @staticmethod
    def has_space_available(file_size, user_id=None):
        """Verifica se há espaço disponível para um novo arquivo"""
        if user_id is not None:
            # Verifica limite do usuário (2GB)
            user_info = StorageService.get_user_storage_info(user_id)
            return user_info['available'] >= file_size
        else:
            # Verifica limite global (10GB)
            info = StorageService.get_storage_info()
            return info['available'] >= file_size
    
    @staticmethod
    def get_user_directory(user_id, relative_path: str = ""):
        """Retorna o diretório do usuário (ou subdiretório), criando se necessário"""
        storage_path = current_app.config['STORAGE_PATH']
        user_root = storage_path / f"user_{user_id}"

        if not user_root.exists():
            user_root.mkdir(parents=True, exist_ok=True)
            print(f"📁 Diretório criado para usuário {user_id}")

        if not relative_path:
            return user_root

        safe_parts = [p for p in Path(relative_path).parts if p not in ("..", ".")]
        target = (user_root / Path(*safe_parts)).resolve()
        if not str(target).startswith(str(user_root.resolve())):
            raise ValueError("Caminho inválido")

        target.mkdir(parents=True, exist_ok=True)
        return target

    @staticmethod
    def list_user_entries(user_id, relative_path: str = ""):
        """Lista arquivos e pastas do usuário no caminho fornecido"""
        base_dir = StorageService.get_user_directory(user_id, relative_path)

        entries = []
        for item in base_dir.iterdir():
            stat = item.stat()
            if item.is_dir():
                size = 0
                for f in item.rglob('*'):
                    if f.is_file():
                        size += f.stat().st_size
                entries.append({
                    'type': 'dir',
                    'name': item.name,
                    'path': str(Path(relative_path) / item.name),
                    'size': size,
                    'modified_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            else:
                entries.append({
                    'type': 'file',
                    'name': item.name,
                    'path': str(Path(relative_path) / item.name),
                    'size': stat.st_size,
                    'modified_at': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        entries.sort(key=lambda e: (0 if e['type'] == 'dir' else 1, e['name'].lower()))
        return entries
    
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
        
        # Verifica espaço disponível do usuário (2GB por usuário)
        if not StorageService.has_space_available(file_size, user_id):
            max_user_gb = current_app.config['MAX_USER_STORAGE_SIZE'] / (1024*1024*1024)
            return None, f'Espaço de armazenamento esgotado (limite de {max_user_gb:.0f}GB por usuário)'
        
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
