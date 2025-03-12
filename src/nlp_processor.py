"""
Processador de linguagem natural para o assistente de calendário.
Utiliza regras e expressões regulares para interpretar comandos do usuário.
"""

import re
import logging
from datetime import datetime, timedelta
import dateutil.parser
from dateutil.relativedelta import relativedelta
import pytz

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NLPProcessor:
    """Processa mensagens em linguagem natural para extrair intenções e entidades"""
    
    def __init__(self):
        """
        Inicializa o processador NLP
        """
        # Timezone padrão para o Brasil
        self.timezone = pytz.timezone('America/Sao_Paulo')
        
    def identify_intent(self, text):
        """
        Identifica a intenção da mensagem com reconhecimento contextual avançado
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            str: Intenção identificada
        """
        text_lower = text.lower()
        
        # CONSULTANDO AGENDA - Expressões conversacionais
        agenda_queries = [
            # Perguntas diretas
            "quais", "quais são", "me mostra", "mostre", "me diz", "diga", 
            "preciso saber", "gostaria de saber", "poderia me dizer",
            "tenho", "tem", "existe", "há", "estão", "estarão",
            "qual é", "qual a", "qual minha", "quero ver", "quero saber",
            
            # Frases com informações temporais
            "para hoje", "pra hoje", "hoje eu tenho", "tenho hoje",
            "para amanhã", "pra amanhã", "amanhã eu tenho", "tenho amanhã",
            "para essa semana", "essa semana", "na semana", "da semana",
            "tenho marcado", "está marcado", "foi marcado",
            
            # Expressões de preocupação
            "não quero esquecer", "não posso esquecer", "lembrar", "me lembre",
            "o que temos", "preciso me preparar", "preciso saber"
        ]
        
        agenda_objects = [
            "agenda", "calendário", "calendar", "dia", "cronograma",
            "reuniões", "reunioes", "reunião", "reuniao", 
            "compromissos", "compromisso", "eventos", "evento", 
            "marcado", "marcações", "marcacoes", "calls", "meetings"
        ]
        
        # CRIAR EVENTOS - Expressões conversacionais
        create_actions = [
            # Verbos de ação direta
            "agendar", "marcar", "criar", "adicionar", "incluir", "inserir",
            "novo", "nova", "agende", "marque", "crie", "adicione",
            "quero marcar", "quero agendar", "preciso marcar", "preciso agendar",
            "gostaria de marcar", "gostaria de agendar", "poderia marcar",
            "por favor agende", "por favor marque", "coloque", "colocar",
            
            # Indicadores temporais com contexto de criação
            "para amanhã vamos ter", "amanhã teremos", "amanhã será",
            "para semana que vem", "na próxima semana", "semana que vem",
            "vou ter", "teremos", "vamos ter", "acontecerá"
        ]
        
        # ATUALIZAR EVENTOS - Expressões conversacionais
        update_actions = [
            # Verbos de modificação
            "alterar", "mudar", "editar", "atualizar", "modificar", "trocar",
            "mover", "transferir", "reagendar", "remarcar", "ajustar",
            "quero mudar", "preciso alterar", "gostaria de mudar", "poderia alterar",
            
            # Específicos para duração
            "aumentar duração", "diminuir duração", "estender", "prolongar", "encurtar"
        ]
        
        duration_context = [
            "duração", "durar", "dura", "horas", "hora", "minutos", "tempo", 
            "mais longo", "mais curto", "estender", "prolongar", "reduzir",
            "aumentar o tempo", "diminuir o tempo", "por mais tempo"
        ]
        
        # EXCLUIR EVENTOS - Expressões conversacionais
        delete_actions = [
            "cancelar", "remover", "deletar", "apagar", "excluir", "desmarcar",
            "quero cancelar", "preciso cancelar", "gostaria de cancelar", 
            "não quero mais", "não vou participar", "não poderei", "não posso", "impossibilitado",
            "não acontecerá", "não vai acontecer", "não ocorrerá", "removido"
        ]
        
        # Análise de intenção por contexto mais amplo
        
        # Verificar Lista de Eventos
        if any(query in text_lower for query in agenda_queries) and any(obj in text_lower for obj in agenda_objects):
            return "LIST_EVENTS"
        
        # Verificar expressões comuns de consulta de agenda sem objeto explícito
        list_expressions = [
            "o que tenho hoje", "o que eu tenho hoje", "o que tem hoje", 
            "tenho algo hoje", "reuniões de hoje", "compromissos de hoje",
            "o que tenho amanhã", "o que eu tenho amanhã", "o que tem amanhã", 
            "tenho algo amanhã", "reuniões de amanhã", "compromissos de amanhã",
            "o que tenho essa semana", "o que está marcado", "quais são os próximos",
            "próximos eventos", "próximas reuniões", "próximos compromissos"
        ]
        
        for expr in list_expressions:
            if expr in text_lower:
                return "LIST_EVENTS"
        
        # Verificar Criação de Eventos
        if any(action in text_lower for action in create_actions):
            return "CREATE_EVENT"
        
        # Verificar Atualização de Eventos
        if any(action in text_lower for action in update_actions):
            if any(context in text_lower for context in duration_context):
                return "UPDATE_DURATION"
            return "UPDATE_EVENT"
        
        # Verificar Exclusão de Eventos
        if any(action in text_lower for action in delete_actions):
            return "DELETE_EVENT"
        
        # Análise de contexto adicional para casos não cobertos
        
        # Expressões implícitas de consulta
        if "hoje" in text_lower and not any(w in text_lower for w in create_actions + update_actions + delete_actions):
            return "LIST_EVENTS"
        
        if "amanhã" in text_lower and not any(w in text_lower for w in create_actions + update_actions + delete_actions):
            return "LIST_EVENTS"
        
        # Expressões interrogativas sobre agenda
        question_words = ["quando", "que horas", "a que horas", "qual horário", "onde", "com quem"]
        if any(qw in text_lower for qw in question_words):
            return "LIST_EVENTS"
        
        # Não foi possível identificar a intenção
        return "UNKNOWN"
    
    def extract_date(self, text):
        """
        Extrai a data da mensagem
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            str: Data em formato ISO (YYYY-MM-DD) ou None
        """
        # Base de tempo atual
        current_date = datetime.now(self.timezone).date()
        text_lower = text.lower()
        
        # Palavras-chave para datas relativas
        if 'hoje' in text_lower:
            return current_date.isoformat()
        
        if 'amanhã' in text_lower or 'amanha' in text_lower:
            return (current_date + timedelta(days=1)).isoformat()
        
        if 'depois de amanhã' in text_lower or 'depois de amanha' in text_lower:
            return (current_date + timedelta(days=2)).isoformat()
        
        # Dias da semana
        days_map = {
            'segunda': 0, 'segunda-feira': 0, 'segunda feira': 0,
            'terça': 1, 'terça-feira': 1, 'terça feira': 1, 'terca': 1, 'terca-feira': 1, 'terca feira': 1,
            'quarta': 2, 'quarta-feira': 2, 'quarta feira': 2,
            'quinta': 3, 'quinta-feira': 3, 'quinta feira': 3,
            'sexta': 4, 'sexta-feira': 4, 'sexta feira': 4,
            'sábado': 5, 'sabado': 5,
            'domingo': 6
        }
        
        for day_name, day_num in days_map.items():
            if day_name in text_lower:
                # Calcular próximo dia da semana
                days_ahead = (day_num - current_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Se for o mesmo dia, considerar próxima semana
                next_date = current_date + timedelta(days=days_ahead)
                return next_date.isoformat()
        
        # Procurar datas no formato DD/MM ou DD/MM/YY
        date_patterns = [
            r'\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b',  # DD/MM/YYYY ou DD/MM
            r'\bdia (\d{1,2})(?:[ ](?:de|do|da)[ ]([a-zA-Zç]+))?\b'  # "dia 15" ou "dia 15 de março"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                match = matches[0]
                
                # Formato DD/MM ou DD/MM/YYYY
                if len(match) >= 2 and match[0].isdigit() and match[1].isdigit():
                    day = int(match[0])
                    month = int(match[1])
                    
                    # Se tiver o ano
                    if len(match) > 2 and match[2] and match[2].isdigit():
                        year = int(match[2])
                        # Ajustar anos de 2 dígitos
                        if year < 100:
                            year += 2000
                    else:
                        year = current_date.year
                        
                        # Se o mês for anterior ao atual, considerar próximo ano
                        if month < current_date.month or (month == current_date.month and day < current_date.day):
                            year += 1
                    
                    try:
                        date_obj = datetime(year, month, day).date()
                        return date_obj.isoformat()
                    except ValueError:
                        logger.warning(f"Data inválida: {day}/{month}/{year}")
        
        # Se não encontrar uma data específica, retornar None
        return None
    
    def extract_time(self, text):
        """
        Extrai a hora da mensagem
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            str: Hora em formato "HH:MM" ou None
        """
        text_lower = text.lower()
        
        # Procurar horários no formato HH:MM, HHh, HH horas
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\b',  # HH:MM
            r'\b(\d{1,2})h(?:(\d{2}))?\b',  # HHh ou HHhMM
            r'\b(\d{1,2}) ?horas?(?: e (\d{1,2}) ?minutos?)?\b',  # HH horas ou HH horas e MM minutos
            r'\b(\d{1,2}) ?(?:h|hrs)\b',  # HH h ou HH hrs
            r'\b(?:às|as|ao meio[- ]dia)(?: e (\d{1,2}))?\b',  # meio-dia ou meio-dia e MM
            r'\bmeio[- ]dia\b'  # meio-dia
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                match = matches[0]
                
                # Meio-dia
                if pattern == r'\bmeio[- ]dia\b':
                    return "12:00"
                
                # "às meio-dia e 30"
                if pattern == r'\b(?:às|as|ao meio[- ]dia)(?: e (\d{1,2}))?\b':
                    if match:
                        minutes = int(match)
                        return f"12:{minutes:02d}"
                    else:
                        return "12:00"
                
                # Outros formatos
                hour = int(match[0]) if match[0] else 0
                minute = int(match[1]) if len(match) > 1 and match[1] else 0
                
                # Ajustar para formato 24h se necessário
                if 'tarde' in text_lower or 'noite' in text_lower:
                    if hour < 12:
                        hour += 12
                
                return f"{hour:02d}:{minute:02d}"
        
        # Se não encontrar um horário específico, retornar None
        return None
    
    def extract_duration(self, text):
        """
        Extrai a duração do evento em horas
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            float: Duração em horas ou None
        """
        text_lower = text.lower()
        
        # Padrões para duração
        duration_patterns = [
            r'(\d+)(?:\s*|\-)(?:hora|horas|hr|hrs|h)\b',  # X horas
            r'(\d+)(?:\s*|\-)(?:minuto|minutos|min|mins|m)\b',  # X minutos
            r'(\d+)[,\.](\d+)(?:\s*|\-)(?:hora|horas|hr|hrs|h)\b',  # X,Y horas
            r'(meia)(?:\s*|\-)(?:hora)\b',  # meia hora
            r'(uma hora e meia)\b',  # uma hora e meia
            r'(1 hora e meia)\b'  # 1 hora e meia
        ]
        
        for pattern in duration_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                match = matches[0]
                
                # Casos especiais
                if pattern == r'(meia)(?:\s*|\-)(?:hora)\b':
                    return 0.5
                if pattern == r'(uma hora e meia)\b' or pattern == r'(1 hora e meia)\b':
                    return 1.5
                
                # Horas inteiras
                if pattern == r'(\d+)(?:\s*|\-)(?:hora|horas|hr|hrs|h)\b':
                    return int(match)
                
                # Minutos (convertidos para horas)
                if pattern == r'(\d+)(?:\s*|\-)(?:minuto|minutos|min|mins|m)\b':
                    return int(match) / 60
                
                # Horas fracionárias (X,Y horas)
                if pattern == r'(\d+)[,\.](\d+)(?:\s*|\-)(?:hora|horas|hr|hrs|h)\b':
                    if len(match) >= 2:
                        return float(f"{match[0]}.{match[1]}")
        
        # Se não encontrar uma duração específica, retornar None (o padrão será 1 hora)
        return None
    
    def extract_summary(self, text):
        """
        Extrai o título/assunto do evento
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            str: Título/assunto extraído ou None
        """
        text_lower = text.lower()
        
        # Padrões para identificar o assunto
        summary_patterns = [
            r'(?:sobre|assunto|título|titulo|tema)[\s:]+["\']?([^"\']+)["\']?',  # assunto: X
            r'(?:reuni[ãa]o|encontro|evento|compromisso)[\s]+(?:sobre|com|de)[\s]+([^,.:;]+)',  # reunião sobre X
            r'(?:marcar|agendar|criar)[\s]+([^,.:;]+)[\s]+(?:para|em|no dia)',  # agendar X para
            r'(?:marcar|agendar|criar)[\s]+([^,.:;]+)'  # agendar X
        ]
        
        for pattern in summary_patterns:
            matches = re.findall(pattern, text_lower)
            if matches and matches[0].strip():
                # Limpar o texto extraído
                summary = matches[0].strip()
                # Remover palavras comuns de trechos finais que não devem fazer parte do título
                summary = re.sub(r'\b(?:para|no dia|às|as|com duração|com duração de)\b.*$', '', summary).strip()
                return summary.capitalize()
        
        # Se não conseguir extrair um título/assunto específico, retornar um padrão
        if "reunião" in text_lower or "reunir" in text_lower:
            return "Reunião"
        elif "call" in text_lower:
            return "Call"
        elif "entrevista" in text_lower:
            return "Entrevista"
        
        # Padrão genérico
        return "Evento"
    
    def is_meeting_request(self, text):
        """
        Verifica se a mensagem solicita uma reunião (para decidir se adiciona link do Meet)
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            bool: True se for solicitação de reunião
        """
        text_lower = text.lower()
        meeting_keywords = [
            "reunião", "reunir", "meeting", "call", "conferência", "conferencia", 
            "videoconferência", "videoconferencia", "meet", "hangout", "entrevista", 
            "conversa", "bate-papo", "discussão", "discussao", "online"
        ]
        
        return any(keyword in text_lower for keyword in meeting_keywords)
    
    def extract_attendees(self, text):
        """
        Extrai possíveis participantes da mensagem
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            list: Lista de possíveis e-mails/nomes de participantes ou None
        """
        # Procurar e-mails
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        emails = re.findall(email_pattern, text)
        
        if emails:
            return emails
        
        # Procurar nomes de participantes
        text_lower = text.lower()
        
        # Padrões para identificar participantes
        attendee_patterns = [
            r'(?:com|para|convidar|participantes|participante)[\s:]+([^,.;]+(?:(?:,|e)[\s]+[^,.;]+)*)',  # com/para X, Y e Z
            r'(?:convidar|adicionar)[\s:]+([^,.;]+(?:(?:,|e)[\s]+[^,.;]+)*)',  # convidar X, Y e Z
        ]
        
        for pattern in attendee_patterns:
            matches = re.findall(pattern, text_lower)
            if matches and matches[0].strip():
                # Processar a string de participantes
                attendees_text = matches[0].strip()
                
                # Dividir por vírgulas e 'e'
                attendees = []
                for part in re.split(r',|\se\s', attendees_text):
                    part = part.strip()
                    if part and not any(word in part for word in ['reunião', 'evento', 'call']):
                        attendees.append(part)
                
                return attendees if attendees else None
        
        return None
    
    def extract_location(self, text):
        """
        Extrai o local do evento
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            str: Local extraído ou None
        """
        text_lower = text.lower()
        
        # Padrões para identificar o local
        location_patterns = [
            r'(?:em|no|na|local|localização|lugar)[\s:]+["\']?([^"\',.;]+)["\']?',  # local: X
            r'(?:no|na) ([^,.;]+)',  # no X
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                for match in matches:
                    location = match.strip()
                    # Evitar falsos positivos como datas e horas
                    if (not re.search(r'\b\d{1,2}/\d{1,2}\b', location) and 
                        not re.search(r'\b\d{1,2}:\d{2}\b', location) and
                        not re.search(r'\b\d{1,2}h\b', location) and
                        not any(day in location for day in ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo'])):
                        return location.capitalize()
        
        return None
    
    def extract_entities(self, text):
        """
        Extrai todas as entidades relevantes da mensagem
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            dict: Dicionário com todas as entidades extraídas
        """
        entities = {
            'date': self.extract_date(text),
            'time': self.extract_time(text),
            'duration': self.extract_duration(text),
            'summary': self.extract_summary(text),
            'location': self.extract_location(text),
            'is_meeting': self.is_meeting_request(text),
            'attendees': self.extract_attendees(text)
        }
        
        return entities
    
    def process_message(self, text):
        """
        Processa uma mensagem completa e retorna a intenção e entidades
        
        Args:
            text (str): Texto da mensagem
            
        Returns:
            tuple: (intenção, entidades)
        """
        intent = self.identify_intent(text)
        entities = self.extract_entities(text)
        
        return intent, entities
    
    def get_missing_info(self, intent, entities):
        """
        Identifica informações faltantes para completar a ação
        
        Args:
            intent (str): Intenção identificada
            entities (dict): Entidades extraídas
            
        Returns:
            list: Lista de campos faltantes
        """
        missing = []
        
        if intent == "CREATE_EVENT":
            if not entities.get('date'):
                missing.append('date')
            if not entities.get('time'):
                missing.append('time')
            
            # Se for uma reunião, verificar se quer adicionar link do Meet
            if entities.get('is_meeting') and 'add_meet_link' not in entities:
                missing.append('add_meet_link')
                
            # Se quiser adicionar link do Meet, verificar participantes
            if entities.get('add_meet_link') and not entities.get('attendees'):
                missing.append('attendees')
        
        elif intent in ["UPDATE_EVENT", "DELETE_EVENT", "UPDATE_DURATION"]:
            if not entities.get('event_reference') and not entities.get('event_id'):
                missing.append('event_reference')
            
            if intent == "UPDATE_DURATION" and not entities.get('duration'):
                missing.append('duration')
        
        return missing
    
    def format_date_for_display(self, iso_date):
        """
        Formata uma data ISO para exibição
        
        Args:
            iso_date (str): Data em formato ISO (YYYY-MM-DD)
            
        Returns:
            str: Data formatada para exibição
        """
        if not iso_date:
            return None
        
        try:
            date_obj = datetime.fromisoformat(iso_date)
            # Formatar como "15 de março de 2023" em português
            months = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", 
                     "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
            return f"{date_obj.day} de {months[date_obj.month-1]} de {date_obj.year}"
        except:
            return iso_date
    
    def format_time_for_display(self, time_str):
        """
        Formata uma hora para exibição
        
        Args:
            time_str (str): Hora em formato "HH:MM"
            
        Returns:
            str: Hora formatada para exibição
        """
        if not time_str:
            return None
        
        try:
            hour, minute = time_str.split(":")
            if minute == "00":
                return f"{int(hour)}h"
            else:
                return f"{int(hour)}h{minute}"
        except:
            return time_str