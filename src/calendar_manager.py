"""
Gerenciador de eventos do Google Calendar.
Implementa funções para criar, listar, atualizar e excluir eventos.
"""

import logging
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CalendarManager:
    """Gerencia operações com eventos no Google Calendar"""
    
    def __init__(self, auth_manager):
        """
        Inicializa o gerenciador de calendário
        
        Args:
            auth_manager: Instância de CalendarAuth para obter serviços autenticados
        """
        self.auth_manager = auth_manager
    
    def create_event(self, user_id, summary, start_date, start_time, 
                    duration=1, description="", location="", attendees=None, 
                    add_meet_link=False, recurrence=None, end_date=None):
        """
        Cria um novo evento no Google Calendar, com opção de recorrência
        
        Args:
            user_id (str): ID único do usuário
            summary (str): Título/resumo do evento
            start_date (str): Data de início (formato ISO: YYYY-MM-DD)
            start_time (str): Hora de início (formato: HH:MM)
            duration (float): Duração em horas
            description (str): Descrição do evento
            location (str): Local do evento
            attendees (list): Lista de e-mails dos participantes
            add_meet_link (bool): Se True, adiciona um link do Google Meet
            recurrence (str): Tipo de recorrência ('daily', 'weekly', 'monthly', etc.)
            end_date (str): Data final para eventos recorrentes (formato ISO: YYYY-MM-DD)
            
        Returns:
            tuple: (sucesso (bool), resultado (dict ou str))
        """
        service = self.auth_manager.get_calendar_service(user_id)
        if not service:
            return False, "Não foi possível conectar ao Google Calendar."
        
        try:
            # Garantir que duration seja um número
            if duration is None:
                duration = 1.0  # valor padrão
            else:
                # Converter para float para garantir compatibilidade
                duration = float(duration)
            
            # Processar data e hora
            date_str = f"{start_date}T{start_time}:00"
            start_datetime = datetime.fromisoformat(date_str)
            end_datetime = start_datetime + timedelta(hours=duration)
            
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
            }
            
            # Adicionar regra de recorrência se especificada
            if recurrence:
                recurrence_rule = ['RRULE:FREQ=' + recurrence.upper()]
                
                # Adicionar data final para a recorrência se especificada
                if end_date:
                    # Formatar a data final no formato apropriado (YYYYMMDD)
                    end_date_obj = datetime.fromisoformat(end_date)
                    formatted_end_date = end_date_obj.strftime('%Y%m%d')
                    recurrence_rule[0] += f';UNTIL={formatted_end_date}T235959Z'
                
                event['recurrence'] = recurrence_rule
            
            # Adicionar participantes se fornecidos
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Adicionar link do Google Meet se solicitado
            if add_meet_link:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
                
                # Quando adicionar link do Meet, precisamos usar conferenceDataVersion=1
                created_event = service.events().insert(
                    calendarId='primary', 
                    body=event,
                    conferenceDataVersion=1
                ).execute()
            else:
                created_event = service.events().insert(
                    calendarId='primary', 
                    body=event
                ).execute()
            
            # Retornar sucesso e o evento criado
            return True, created_event
        except Exception as e:
            error_message = f"Erro ao criar evento: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def list_events(self, user_id, time_min=None, time_max=None, max_results=10):
        """
        Lista eventos do calendário do usuário
        
        Args:
            user_id (str): ID único do usuário
            time_min (str): Hora mínima em formato ISO ou None para agora
            time_max (str): Hora máxima em formato ISO ou None para indefinido
            max_results (int): Número máximo de resultados
            
        Returns:
            tuple: (sucesso (bool), eventos (list) ou mensagem de erro (str))
        """
        service = self.auth_manager.get_calendar_service(user_id)
        if not service:
            return False, "Não foi possível conectar ao Google Calendar."
        
        try:
            # Se time_min não foi especificado, usar agora
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            # Configurar os parâmetros da busca
            params = {
                'calendarId': 'primary',
                'timeMin': time_min,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            # Adicionar time_max se especificado
            if time_max:
                params['timeMax'] = time_max
            
            # Buscar eventos
            events_result = service.events().list(**params).execute()
            events = events_result.get('items', [])
            
            return True, events
        except HttpError as e:
            error_message = f"Erro na API do Google Calendar: {e}"
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Erro ao listar eventos: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def update_event(self, user_id, event_id, updates, update_conference=False):
        """
        Atualiza um evento existente
        
        Args:
            user_id (str): ID único do usuário
            event_id (str): ID do evento a ser atualizado
            updates (dict): Dicionário com campos a serem atualizados
            update_conference (bool): Se True, atualiza as configurações de conferência
            
        Returns:
            tuple: (sucesso (bool), resultado (dict ou str))
        """
        service = self.auth_manager.get_calendar_service(user_id)
        if not service:
            return False, "Não foi possível conectar ao Google Calendar."
        
        try:
            # Obter o evento existente
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Aplicar atualizações
            if 'summary' in updates:
                event['summary'] = updates['summary']
            
            if 'location' in updates:
                event['location'] = updates['location']
            
            if 'description' in updates:
                event['description'] = updates['description']
            
            if 'start_datetime' in updates:
                event['start']['dateTime'] = updates['start_datetime']
            
            if 'end_datetime' in updates:
                event['end']['dateTime'] = updates['end_datetime']
            
            if 'attendees' in updates:
                event['attendees'] = [{'email': email} for email in updates['attendees']]
            
            # Atualizar conferência (Google Meet)
            if update_conference:
                if 'add_meet_link' in updates and updates['add_meet_link']:
                    # Adicionar link do Meet
                    event['conferenceData'] = {
                        'createRequest': {
                            'requestId': f"{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            'conferenceSolutionKey': {
                                'type': 'hangoutsMeet'
                            }
                        }
                    }
                    conference_data_version = 1
                elif 'remove_meet_link' in updates and updates['remove_meet_link']:
                    # Remover link do Meet
                    if 'conferenceData' in event:
                        del event['conferenceData']
                    conference_data_version = 1
                else:
                    conference_data_version = 0
            else:
                conference_data_version = 0
            
            # Enviar atualizações
            updated_event = service.events().update(
                calendarId='primary', 
                eventId=event_id, 
                body=event,
                conferenceDataVersion=conference_data_version
            ).execute()
            
            return True, updated_event
        except HttpError as e:
            error_message = f"Erro na API do Google Calendar: {e}"
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Erro ao atualizar evento: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def delete_event(self, user_id, event_id):
        """
        Exclui um evento
        
        Args:
            user_id (str): ID único do usuário
            event_id (str): ID do evento a ser excluído
            
        Returns:
            tuple: (sucesso (bool), mensagem (str))
        """
        service = self.auth_manager.get_calendar_service(user_id)
        if not service:
            return False, "Não foi possível conectar ao Google Calendar."
        
        try:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True, "Evento excluído com sucesso."
        except HttpError as e:
            error_message = f"Erro na API do Google Calendar: {e}"
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Erro ao excluir evento: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def find_events_by_query(self, user_id, query_text, time_min=None, time_max=None, max_results=10):
        """
        Busca eventos que correspondam a um texto de consulta
        
        Args:
            user_id (str): ID único do usuário
            query_text (str): Texto para buscar nos eventos
            time_min (str): Hora mínima em formato ISO ou None para agora
            time_max (str): Hora máxima em formato ISO ou None para indefinido
            max_results (int): Número máximo de resultados
            
        Returns:
            tuple: (sucesso (bool), eventos (list) ou mensagem de erro (str))
        """
        # Obter todos os eventos no período
        success, events = self.list_events(user_id, time_min, time_max, max_results=50)
        
        if not success:
            return False, events
        
        # Filtrar eventos que correspondam à consulta
        matching_events = []
        query_lower = query_text.lower()
        
        for event in events:
            # Verificar no título, descrição e local
            summary = event.get('summary', '').lower()
            description = event.get('description', '').lower()
            location = event.get('location', '').lower()
            
            if (query_lower in summary or 
                query_lower in description or 
                query_lower in location):
                matching_events.append(event)
            
            if len(matching_events) >= max_results:
                break
        
        return True, matching_events[:max_results]
    
    def get_event_by_id(self, user_id, event_id):
        """
        Obtém um evento específico pelo ID
        
        Args:
            user_id (str): ID único do usuário
            event_id (str): ID do evento
            
        Returns:
            tuple: (sucesso (bool), evento (dict) ou mensagem de erro (str))
        """
        service = self.auth_manager.get_calendar_service(user_id)
        if not service:
            return False, "Não foi possível conectar ao Google Calendar."
        
        try:
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            return True, event
        except HttpError as e:
            error_message = f"Erro na API do Google Calendar: {e}"
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Erro ao obter evento: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def update_event_duration(self, user_id, event_id, duration_hours):
        """
        Atualiza apenas a duração de um evento, mantendo o horário de início
        
        Args:
            user_id (str): ID único do usuário
            event_id (str): ID do evento a ser atualizado
            duration_hours (float): Nova duração em horas
            
        Returns:
            tuple: (sucesso (bool), resultado (dict ou str))
        """
        service = self.auth_manager.get_calendar_service(user_id)
        if not service:
            return False, "Não foi possível conectar ao Google Calendar."
        
        try:
            # Obter o evento existente
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Obter horário de início e calcular novo fim
            start_datetime = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            new_end_datetime = start_datetime + timedelta(hours=duration_hours)
            
            # Atualizar apenas o horário de término
            event['end']['dateTime'] = new_end_datetime.isoformat()
            
            # Enviar atualizações
            updated_event = service.events().update(
                calendarId='primary', 
                eventId=event_id, 
                body=event
            ).execute()
            
            return True, updated_event
        except HttpError as e:
            error_message = f"Erro na API do Google Calendar: {e}"
            logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Erro ao atualizar duração: {str(e)}"
            logger.error(error_message)
            return False, error_message