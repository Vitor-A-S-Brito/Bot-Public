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
def Interpretar_mensagem(texto):
    # Inicializar variáveis para armazenar as informações extraídas
    nome_evento = None
    dia = None
    mes = None
    ano = None
    meet = None
    convidados = None

    # Lista de palavras-chave relevantes
    palavras_chaves = ['reuniao', 'encontro', 'compromisso', 'dia', 'mes', 'de']
    
    # Dividir o texto em palavras
    palavras = texto.lower().split()

    # Mapeamento de nomes de meses para números de mês
    meses = {'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
             'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
             'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
            }
    
    # Iterar sobre as palavras para identificar as informações relevantes
    for i, palavra in enumerate(palavras):
        if palavra in palavras_chaves:
            # Verificar se é dia
            if palavra == 'dia':
                dia = palavras[i + 1]
            elif palavra == 'mes':
                proxima_palavra = palavras[i + 1]
                if proxima_palavra.isdigit():
                    mes = proxima_palavra.zfill(2)
                else:
                    mes = meses.get(proxima_palavra)
            elif palavra == 'ano':
                ano = palavras[i + 1]
            elif palavra == 'reuniao':
                meet = True
                convidados = []
                break
            else:
                nome_evento = extract_event_name(texto)
                print(f"Título do evento: {extract_event_name}")

    # Se a data estiver no formato "dia de mês de ano"
    for i, palavra in enumerate(palavras):
        if palavra.isdigit() and int(palavra) <= 31:
            dia = palavra
            if i + 2 < len(palavras):
                if palavras[i + 1] in meses:
                    mes_nome = palavras[i + 1]
                    mes = meses[mes_nome]
                    if i + 3 < len(palavras):
                        if palavras[i + 2].isdigit() and len(palavras[i + 2]) == 4:
                            ano = palavras[i + 2]
    if meet == True:
        print('Deseja agendar a reunião no Google Meet? (s/n)')
        resposta = input()
        if resposta.lower() == 's':
            print('Digite os e-mails dos convidados separados por vírgula:')
            convidados = input().split(',')
            print('Deseja adicionar mais algum convidado? (s/n)')
            resposta = input()
            while resposta.lower() == 's':
                print('Digite o e-mail do convidado:')
                convidados.append(input())
                print('Deseja adicionar mais algum convidado? (s/n)')
                resposta = input()

    return nome_evento, dia, mes, ano, meet, convidados


def extract_event_name(input_text):
    # Lista de palavras-chave para identificar o nome do evento
    keywords = ["minha agenda", "tenho uma", "marque para mim", "vou ter", "para amanha", "Marque na agenda"]

    # Procura por palavras-chave no texto de entrada
    for keyword in keywords:
        if keyword in input_text:
            # Obtém o nome do evento a partir do texto após a palavra-chave
            event_name = input_text.split(keyword)[+1].strip()
            if ',' in event_name:
                event_name = event_name.split(',')[0].strip()
            return event_name

    # Se nenhuma palavra-chave for encontrada, retorna None
    return None

def criar_evento_interativo(calendar_id, nome_evento, dia, mes, ano, meet=False):
    service = create_service()

    # Solicitar informações adicionais ao usuário
    if nome_evento is None:
        summary = input("Digite o título do evento: ")
    else:
        summary = nome_evento

    location = input("Digite a localização do evento: ")
    description = input("Digite a descrição do evento: ")

    if dia is None:
        start_date = input("Digite a data de início (no formato YYYY-MM-DD): ")
    else:
        if mes is None:
            mes = datetime.now().strftime('%m')  # Obter o mês atual
        if ano is None:
            ano = datetime.now().strftime('%Y')  # Obter o ano atual
        start_date = f"{ano}-{mes}-{dia}"

    start_time = input("Digite a hora de início (no formato HH:MM): ")

    if dia is None:
        end_date = input("Digite a data de término (no formato YYYY-MM-DD): ")
    else:
        same_day_end = input("O evento termina no mesmo dia em que começa? (s/n): ")
        if same_day_end.lower() == 's':
            end_date = start_date
        else:
            end_date = input("Digite a data de término (no formato YYYY-MM-DD): ")

    end_time = input("Digite a hora de término (no formato HH:MM): ")

    # Formatar a data e hora
    start_datetime = f"{start_date}T{start_time}:00"
    end_datetime = f"{end_date}T{end_time}:00"

    try:
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

        if meet:
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': '7qxalsvy0e',
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }

            print('Digite os e-mails dos convidados separados por vírgula:')
            convidados = input().split(',')
            event['attendees'] = [{'email': email} for email in convidados]

        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print('Evento criado:', event.get('htmlLink'))

    except Exception as e:
        print('Erro:', e)