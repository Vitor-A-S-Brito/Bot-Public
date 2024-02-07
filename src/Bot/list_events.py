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

def listar_eventos(calendar_id):
    service = create_service()
    try:
        calendar_id = '042bd9f9c7757f611d765a6b8fb84c7911246aa7d2ee6ce260dbc19953048450@group.calendar.google.com'
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=datetime.utcnow().isoformat() + 'Z',
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return 'No upcoming events found.'

        resposta = 'Próximos eventos:'
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            resposta += f"\n- {event['summary']} em {start}"

        return resposta

    except Exception as e:
        return f"Erro ao listar eventos: {e}"
