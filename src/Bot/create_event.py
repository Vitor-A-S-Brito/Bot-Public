from google.oauth2 import service_account
import googleapiclient.discovery
from datetime import datetime

# Configurações do Google Agenda
CLIENT_SERVICE_FILE = 'D:/Zoe/zoebot-413418-6988e17bec4b.json'
API_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_service():
    credentials = service_account.Credentials.from_service_account_file(CLIENT_SERVICE_FILE, scopes=SCOPES)
    service = googleapiclient.discovery.build(API_NAME, API_VERSION, credentials=credentials)
    return service

def criar_evento_interativo(calendar_id):
    service = create_service()

    # Solicitar informações ao usuário
    summary = input("Digite o título do evento: ")
    location = input("Digite a localização do evento: ")
    description = input("Digite a descrição do evento: ")

    # Solicitar data ao usuário
    start_date = input("Digite a data de início (no formato YYYY-MM-DD): ")
    start_time = input("Digite a hora de início (no formato HH:MM): ")

    # Solicitar hora ao usuário
    end_date = input("Digite a data de término (no formato YYYY-MM-DD): ")
    end_time = input("Digite a hora de término (no formato HH:MM): ")

    # Formatar a data e hora
    start_datetime = f"{start_date}T{start_time}:00"
    end_datetime = f"{end_date}T{end_time}:00"

    try:
        calendar_id = '042bd9f9c7757f611d765a6b8fb84c7911246aa7d2ee6ce260dbc19953048450@group.calendar.google.com'
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'America/Sao_Paulo',
            }
        }

        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print('Event created:', event.get('htmlLink'))

    except Exception as e:
        print('Error:', e)
