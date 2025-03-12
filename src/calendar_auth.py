"""
Sistema de autenticação com Google Calendar API.
Gerencia a autenticação OAuth2, armazenamento de tokens e acesso à API.
"""

import os
import json
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Escopos necessários para acessar o Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarAuth:
    """Gerencia a autenticação e acesso à API do Google Calendar"""
    
    def __init__(self, storage_path='./data'):
        """
        Inicializa o gerenciador de autenticação
        
        Args:
            storage_path (str): Diretório base para armazenamento de dados
        """
        self.storage_path = storage_path
        self.user_data_path = os.path.join(storage_path, 'user_data')
        
        # Garantir que os diretórios existam
        os.makedirs(self.user_data_path, exist_ok=True)
    
    def save_temp_credentials(self, user_id, client_id, client_secret):
        """
        Salva as credenciais temporárias para o processo de autenticação
        
        Args:
            user_id (str): ID único do usuário
            client_id (str): Google OAuth2 Client ID
            client_secret (str): Google OAuth2 Client Secret
            
        Returns:
            str: Caminho para o arquivo de credenciais
        """
        creds_data = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        # Criar arquivo de credenciais temporárias
        creds_file = os.path.join(self.user_data_path, f"{user_id}_temp_credentials.json")
        with open(creds_file, 'w') as f:
            json.dump(creds_data, f)
        
        return creds_file
    
    def get_auth_url(self, user_id, credentials_file):
        """
        Gera URL para autorização OAuth2
        
        Args:
            user_id (str): ID único do usuário
            credentials_file (str): Caminho para o arquivo de credenciais
            
        Returns:
            str: URL de autorização ou None se falhar
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            
            # Não vamos mais salvar o flow para evitar problemas de serialização
            # Em vez disso, vamos salvar os dados necessários para recriar o flow
            flow_data = {
                'client_id': flow.client_config['client_id'],
                'client_secret': flow.client_config['client_secret'],
                'redirect_uri': flow.redirect_uri,
                'scope': ' '.join(SCOPES)
            }
            
            flow_file = os.path.join(self.user_data_path, f"{user_id}_flow_data.json")
            with open(flow_file, 'w') as f:
                json.dump(flow_data, f)
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true')
            
            return auth_url
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autorização: {e}")
            return None
    
    def process_auth_code(self, user_id, auth_code):
        """
        Processa o código de autorização para obter tokens de acesso
        
        Args:
            user_id (str): ID único do usuário
            auth_code (str): Código de autorização recebido
            
        Returns:
            tuple: (sucesso (bool), mensagem (str))
        """
        # Recriar o flow a partir dos dados salvos
        flow_file = os.path.join(self.user_data_path, f"{user_id}_flow_data.json")
        if not os.path.exists(flow_file):
            return False, "Sessão de autorização expirada. Por favor, reinicie o processo."
        
        try:
            with open(flow_file, 'r') as f:
                flow_data = json.load(f)
            
            # Recriar o flow a partir dos dados
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": flow_data['client_id'],
                        "client_secret": flow_data['client_secret'],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                },
                SCOPES
            )
            flow.redirect_uri = flow_data['redirect_uri']
            
            # Trocar o código pelo token
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # Salvar as credenciais
            token_file = os.path.join(self.user_data_path, f"{user_id}_token.json")
            with open(token_file, 'w') as f:
                json.dump({
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                    'expiry': credentials.expiry.isoformat() if credentials.expiry else None
                }, f)
            
            # Limpar arquivos temporários
            if os.path.exists(flow_file):
                os.remove(flow_file)
                
            temp_creds_file = os.path.join(self.user_data_path, f"{user_id}_temp_credentials.json")
            if os.path.exists(temp_creds_file):
                os.remove(temp_creds_file)
            
            return True, "Autenticação concluída com sucesso!"
        except Exception as e:
            logger.error(f"Erro ao processar código de autenticação: {e}")
            return False, f"Erro ao processar o código: {str(e)}"
    
    # No método get_credentials, altere a parte que lida com a expiração:

    def get_credentials(self, user_id):
        """
        Obtém credenciais válidas para o usuário, renovando se necessário
        
        Args:
            user_id (str): ID único do usuário
            
        Returns:
            Credentials: Objeto de credenciais ou None se falhar
        """
        token_file = os.path.join(self.user_data_path, f"{user_id}_token.json")
        
        if not os.path.exists(token_file):
            logger.info(f"Arquivo de token não encontrado para usuário {user_id}")
            return None
        
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Mantenha o expiry como string ou None
            # Não tente converter para datetime aqui, a biblioteca fará isso
            
            # Certifique-se de que as chaves necessárias existam
            required_keys = ['token', 'client_id', 'client_secret', 'token_uri']
            for key in required_keys:
                if key not in token_data:
                    logger.error(f"Token data missing required key: {key}")
                    return None
            
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            
            # Renovar o token se estiver expirado
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
                # Salvar o token atualizado
                with open(token_file, 'w') as f:
                    token_info = {
                        'token': creds.token,
                        'refresh_token': creds.refresh_token,
                        'token_uri': creds.token_uri,
                        'client_id': creds.client_id,
                        'client_secret': creds.client_secret,
                        'scopes': creds.scopes
                    }
                    # Adicionar expiry apenas se existir
                    if creds.expiry:
                        token_info['expiry'] = creds.expiry.isoformat()
                    
                    json.dump(token_info, f)
            
            return creds
        except Exception as e:
            logger.error(f"Erro ao obter credenciais para usuário {user_id}: {e}")
            return None
        
    def get_calendar_service(self, user_id):
        """
        Obtém um serviço autenticado do Google Calendar
        
        Args:
            user_id (str): ID único do usuário
            
        Returns:
            Resource: Serviço do Google Calendar ou None se falhar
        """
        creds = self.get_credentials(user_id)
        if not creds:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Erro ao construir serviço do Calendar: {e}")
            return None
    
    def test_connection(self, user_id):
        """
        Testa a conexão com o Google Calendar
        
        Args:
            user_id (str): ID único do usuário
            
        Returns:
            bool: True se a conexão funciona
        """
        try:
            service = self.get_calendar_service(user_id)
            if not service:
                return False
                
            # Tenta listar os próximos 1 evento
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=1,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao testar conexão para usuário {user_id}: {e}")
            return False
    
    def is_authenticated(self, user_id):
        """
        Verifica se o usuário já está autenticado
        
        Args:
            user_id (str): ID único do usuário
            
        Returns:
            bool: True se o usuário está autenticado
        """
        return self.get_credentials(user_id) is not None
    
    def clear_auth_data(self, user_id):
        """
        Remove todos os dados de autenticação do usuário
        
        Args:
            user_id (str): ID único do usuário
        """
        files_to_remove = [
            f"{user_id}_token.json",
            f"{user_id}_temp_credentials.json",
            f"{user_id}_flow_data.json"
        ]
        
        for filename in files_to_remove:
            file_path = os.path.join(self.user_data_path, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Erro ao remover {file_path}: {e}")