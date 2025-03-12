"""
Bot principal para gerenciamento de calendário via Telegram.
Integra processamento de linguagem natural e Google Calendar API.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

from calendar_auth import CalendarAuth
from calendar_manager import CalendarManager
from nlp_processor import NLPProcessor

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Obter token do bot do Telegram das variáveis de ambiente
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("Token do Telegram não encontrado! Adicione TELEGRAM_TOKEN ao arquivo .env")

# Estados de conversa
(
    STATE_NORMAL,                 # Estado normal, processando comandos
    STATE_SETUP_START,            # Início da configuração
    STATE_AWAITING_CLIENT_ID,     # Aguardando Client ID
    STATE_AWAITING_CLIENT_SECRET, # Aguardando Client Secret
    STATE_AWAITING_AUTH_CODE,     # Aguardando código de autorização
    
    STATE_AWAITING_DATE,          # Aguardando data
    STATE_AWAITING_TIME,          # Aguardando hora
    STATE_AWAITING_DURATION,      # Aguardando duração
    STATE_AWAITING_SUMMARY,       # Aguardando título/assunto
    STATE_AWAITING_ADD_MEET,      # Aguardando confirmação para adicionar Meet
    STATE_AWAITING_ATTENDEES,     # Aguardando participantes
    STATE_AWAITING_EVENT_REF,     # Aguardando referência do evento para edição/exclusão
    STATE_CONFIRM_DELETE          # Confirmação para excluir evento
) = range(13)

class CalendarBot:
    """Gerencia o bot e integra todos os componentes"""
    
    def __init__(self):
        """Inicializa o bot com todos os componentes necessários"""
        self.auth_manager = CalendarAuth()
        self.calendar_manager = CalendarManager(self.auth_manager)
        self.nlp_processor = NLPProcessor()
        
        # Inicializar a aplicação do Telegram
        self.app = Application.builder().token(TOKEN).build()
        
        # Adicionar handlers
        self._add_handlers()
    
    def _add_handlers(self):
        """Adiciona todos os handlers necessários para o bot"""
        # Comandos principais
        self.app.add_handler(CommandHandler("start", self.start_cmd))
        self.app.add_handler(CommandHandler("setup", self.setup_cmd))
        self.app.add_handler(CommandHandler("help", self.help_cmd))
        
        # Callbacks para botões
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Mensagens de texto (não comandos)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_message))
        
        # Handler de erro
        self.app.add_error_handler(self.error_handler)
    
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Inicia a interação com o bot e verifica autenticação"""
        user_id = str(update.effective_user.id)
        
        # Verificar se o usuário já está autenticado
        if self.auth_manager.is_authenticated(user_id):
            # Testar a conexão
            if self.auth_manager.test_connection(user_id):
                # Usuário já está configurado
                await update.message.reply_text(
                    "🤖 Olá! Eu sou seu assistente de calendário.\n\n"
                    "Você já está conectado ao Google Calendar. 🎉\n\n"
                    "Você pode pedir para:\n"
                    "• Agendar eventos: 'Agendar reunião amanhã às 10h'\n"
                    "• Consultar agenda: 'O que tenho hoje?'\n"
                    "• Modificar eventos: 'Mudar reunião de amanhã para sexta'\n\n"
                    "Use /help para ver mais detalhes."
                )
                context.user_data['state'] = STATE_NORMAL
            else:
                # Autenticação expirada ou inválida
                await update.message.reply_text(
                    "Parece que sua autenticação com o Google Calendar expirou. Vamos configurar novamente.\n\n"
                    "Você já possui um projeto no Google Cloud com a API Calendar habilitada?"
                )
                context.user_data['state'] = STATE_SETUP_START
        else:
            # Usuário não está autenticado, iniciar configuração
            await update.message.reply_text(
                "👋 Bem-vindo ao seu Assistente de Calendário!\n\n"
                "Para começar, precisamos conectar seu Google Calendar.\n\n"
                "Você já possui um projeto no Google Cloud com a API Calendar habilitada?"
            )
            context.user_data['state'] = STATE_SETUP_START
    
    async def setup_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Inicia ou reinicia o processo de configuração"""
        user_id = str(update.effective_user.id)
        
        # Limpar dados de autenticação existentes
        self.auth_manager.clear_auth_data(user_id)
        
        await update.message.reply_text(
            "Vamos configurar sua conexão com o Google Calendar.\n\n"
            "Você já tem um projeto no Google Cloud com a API Calendar habilitada?"
        )
        context.user_data['state'] = STATE_SETUP_START
    
    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Envia uma mensagem de ajuda com exemplos de uso"""
        await update.message.reply_text(
            "🤖 Assistente de Calendário - Comandos\n\n"
            "📆 *Criar eventos*\n"
            "• 'Agendar reunião com equipe amanhã às 14h'\n"
            "• 'Marcar call com cliente na quinta às 10h30'\n"
            "• 'Criar evento de planejamento dia 15/04 às 9h com duração de 2 horas'\n\n"
            "👀 *Consultar agenda*\n"
            "• 'O que tenho hoje?'\n"
            "• 'Mostrar minha agenda de amanhã'\n"
            "• 'Ver compromissos da próxima semana'\n\n"
            "✏️ *Modificar eventos*\n"
            "• 'Mudar reunião de amanhã para sexta-feira'\n"
            "• 'Alterar horário da call para 15h'\n"
            "• 'Estender duração da reunião para 2 horas'\n\n"
            "❌ *Cancelar eventos*\n"
            "• 'Cancelar reunião de amanhã'\n"
            "• 'Remover evento de planejamento'\n\n"
            "⚙️ *Configuração*\n"
            "• /start - Iniciar o bot\n"
            "• /setup - Reconfigurar conexão com Google Calendar\n"
            "• /help - Ver esta ajuda",
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Processa callbacks dos botões inline"""
        query = update.callback_query
        await query.answer()
        
        # Extrair dados do callback
        data = query.data
        user_id = str(update.effective_user.id)
        
        # Processar diferentes tipos de callbacks
        if data.startswith('meet_'):
            # Resposta para adicionar Google Meet
            add_meet = data == 'meet_yes'
            
            if 'pending_event' in context.user_data:
                context.user_data['pending_event']['add_meet_link'] = add_meet
                
                # Se adicionar Meet, perguntar sobre participantes
                if add_meet and not context.user_data['pending_event'].get('attendees'):
                    await query.edit_message_text(
                        "Quem serão os participantes da reunião? \n\n"
                        "Digite os e-mails separados por vírgula ou nomes dos participantes."
                    )
                    context.user_data['state'] = STATE_AWAITING_ATTENDEES
                else:
                    # Criar o evento
                    await self._create_event_from_pending(update, context, is_button=True)
            else:
                await query.edit_message_text(
                    "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."
                )
        
        elif data.startswith('delete_'):
            # Confirmação para excluir evento
            confirm_delete = data == 'delete_yes'
            
            if confirm_delete and 'event_to_delete' in context.user_data:
                event_id = context.user_data['event_to_delete']
                
                # Excluir o evento
                success, result = self.calendar_manager.delete_event(user_id, event_id)
                
                if success:
                    await query.edit_message_text("✅ Evento excluído com sucesso!")
                else:
                    await query.edit_message_text(f"❌ Erro ao excluir evento: {result}")
                
                # Limpar dados temporários
                if 'event_to_delete' in context.user_data:
                    del context.user_data['event_to_delete']
                context.user_data['state'] = STATE_NORMAL
            else:
                await query.edit_message_text("Operação cancelada.")
                context.user_data['state'] = STATE_NORMAL
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Processa mensagens de texto recebidas"""
        user_id = str(update.effective_user.id)
        text = update.message.text
        
        # Obter o estado atual da conversa
        state = context.user_data.get('state', STATE_NORMAL)
        
        # Processar mensagem com base no estado atual
        if state == STATE_SETUP_START:
            await self._handle_setup_start(update, context, text)
        
        elif state == STATE_AWAITING_CLIENT_ID:
            await self._handle_client_id(update, context, text)
        
        elif state == STATE_AWAITING_CLIENT_SECRET:
            await self._handle_client_secret(update, context, text)
        
        elif state == STATE_AWAITING_AUTH_CODE:
            await self._handle_auth_code(update, context, text)
        
        elif state in [STATE_AWAITING_DATE, STATE_AWAITING_TIME, STATE_AWAITING_DURATION, 
                       STATE_AWAITING_SUMMARY, STATE_AWAITING_ATTENDEES, STATE_AWAITING_EVENT_REF]:
            await self._handle_pending_info(update, context, text, state)
        
        elif state == STATE_NORMAL:
            # Processamento normal de comando
            await self._process_normal_message(update, context, text)
        
        else:
            # Estado desconhecido
            logger.warning(f"Estado desconhecido: {state}")
            await update.message.reply_text(
                "Desculpe, houve um problema ao processar sua mensagem. Vamos recomeçar.\n\n"
                "Use /start para iniciar o bot novamente."
            )
            context.user_data['state'] = STATE_NORMAL
    
    async def _handle_setup_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """Processa a resposta inicial do setup"""
        if any(word in text.lower() for word in ["sim", "s", "yes", "y", "tenho"]):
            await update.message.reply_text(
                "Ótimo! Agora preciso que você me envie o Client ID do seu projeto.\n\n"
                "Você pode encontrá-lo no Console do Google Cloud > APIs e Serviços > Credenciais > IDs de cliente OAuth 2.0"
            )
            context.user_data['state'] = STATE_AWAITING_CLIENT_ID
        else:
            await update.message.reply_text(
                "Para usar este bot, você precisa criar um projeto no Google Cloud e habilitar a API do Calendar. Siga estes passos:\n\n"
                "1. Acesse https://console.cloud.google.com/\n"
                "2. Crie um novo projeto\n"
                "3. No menu lateral, acesse 'APIs e Serviços' > 'Biblioteca'\n"
                "4. Busque por 'Google Calendar API' e habilite-a\n"
                "5. No menu lateral, acesse 'APIs e Serviços' > 'Credenciais'\n"
                "6. Clique em 'Criar Credenciais' > 'ID do Cliente OAuth'\n"
                "7. Configure a tela de consentimento (tipo 'Externo')\n"
                "8. Para tipo de aplicativo, escolha 'Aplicativo para Desktop'\n"
                "9. Dê um nome e clique em 'Criar'\n\n"
                "Você receberá um Client ID e um Client Secret. Me avise quando estiver pronto!"
            )
    
    async def _handle_client_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """Processa o Client ID recebido"""
        # Verificar se o texto parece um Client ID
        if '.' in text and len(text) > 20:
            context.user_data['client_id'] = text.strip()
            await update.message.reply_text(
                "Ótimo! Agora preciso que você me envie o Client Secret."
            )
            context.user_data['state'] = STATE_AWAITING_CLIENT_SECRET
        else:
            await update.message.reply_text(
                "Isso não parece um Client ID válido. O formato deve ser algo como:\n"
                "123456789012-abcdefghijklmnop.apps.googleusercontent.com\n\n"
                "Por favor, verifique e tente novamente."
            )
    
    async def _handle_client_secret(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """Processa o Client Secret recebido"""
        user_id = str(update.effective_user.id)
        client_id = context.user_data.get('client_id')
        client_secret = text.strip()
        
        # Salvar credenciais e gerar URL de autorização
        credentials_file = self.auth_manager.save_temp_credentials(user_id, client_id, client_secret)
        
        try:
            # Gerar URL de autorização
            auth_url = self.auth_manager.get_auth_url(user_id, credentials_file)
            
            if auth_url:
                await update.message.reply_text(
                    f"Agora você precisa autorizar o acesso ao seu Google Calendar. Clique no link abaixo:\n\n"
                    f"{auth_url}\n\n"
                    f"Após autorizar, você receberá um código. Copie e cole esse código aqui."
                )
                context.user_data['state'] = STATE_AWAITING_AUTH_CODE
            else:
                await update.message.reply_text(
                    "Ocorreu um erro ao gerar o link de autorização. Verifique se o Client ID e Client Secret estão corretos.\n\n"
                    "Vamos tentar novamente. Por favor, envie seu Client ID."
                )
                context.user_data['state'] = STATE_AWAITING_CLIENT_ID
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autorização: {e}")
            await update.message.reply_text(
                f"Ocorreu um erro: {str(e)}\n\n"
                f"Vamos tentar novamente. Por favor, envie seu Client ID."
            )
            context.user_data['state'] = STATE_AWAITING_CLIENT_ID
    
    async def _handle_auth_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """Processa o código de autorização"""
        user_id = str(update.effective_user.id)
        auth_code = text.strip()
        
        # Processar o código de autorização
        success, message = self.auth_manager.process_auth_code(user_id, auth_code)
        
        if success:
            await update.message.reply_text(
                f"🎉 {message}\n\n"
                f"Seu assistente de calendário está pronto para uso!\n\n"
                f"Você pode me pedir para:\n"
                f"• Agendar eventos: 'Agendar reunião amanhã às 10h'\n"
                f"• Consultar agenda: 'O que tenho hoje?'\n"
                f"• E muito mais!\n\n"
                f"Use /help para ver mais exemplos."
            )
            context.user_data['state'] = STATE_NORMAL
        else:
            await update.message.reply_text(
                f"{message}\n\n"
                f"Por favor, tente novamente ou use /setup para reiniciar o processo."
            )
    
    async def _handle_pending_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, state: int) -> None:
        """Processa informações pendentes para completar uma operação"""
        user_id = str(update.effective_user.id)
        
        # Garantir que há um dicionário para armazenar o evento pendente
        if 'pending_event' not in context.user_data:
            context.user_data['pending_event'] = {}
        
        if 'pending_intent' not in context.user_data:
            context.user_data['pending_intent'] = "CREATE_EVENT"
        
        # Processar com base no estado atual
        if state == STATE_AWAITING_DATE:
            # Extrair data da resposta
            date = self.nlp_processor.extract_date(text)
            if date:
                context.user_data['pending_event']['date'] = date
                
                # Verificar se também precisa de hora
                if 'time' not in context.user_data['pending_event']:
                    await update.message.reply_text("Em qual horário?")
                    context.user_data['state'] = STATE_AWAITING_TIME
                else:
                    # Verificar se é um evento de reunião
                    await self._check_if_meeting(update, context)
            else:
                await update.message.reply_text(
                    "Não consegui entender a data. Por favor, tente novamente com formatos como 'amanhã', 'sexta-feira' ou '15/04'."
                )
        
        elif state == STATE_AWAITING_TIME:
            # Extrair hora da resposta
            time = self.nlp_processor.extract_time(text)
            if time:
                context.user_data['pending_event']['time'] = time
                
                # Verificar se também precisa de data
                if 'date' not in context.user_data['pending_event']:
                    await update.message.reply_text("Em qual data?")
                    context.user_data['state'] = STATE_AWAITING_DATE
                else:
                    # Verificar se é um evento de reunião
                    await self._check_if_meeting(update, context)
            else:
                await update.message.reply_text(
                    "Não consegui entender o horário. Por favor, tente novamente com formatos como '14h', '14:30' ou '2 da tarde'."
                )
        
        elif state == STATE_AWAITING_DURATION:
            # Extrair duração da resposta
            duration = self.nlp_processor.extract_duration(text)
            if duration:
                context.user_data['pending_event']['duration'] = duration
                
                # Verificar o intent para decidir o próximo passo
                intent = context.user_data.get('pending_intent')
                
                if intent == "UPDATE_DURATION":
                    # Atualizar duração de um evento existente
                    await self._update_event_duration(update, context)
                else:
                    # Para criar evento, verificar se é uma reunião
                    await self._check_if_meeting(update, context)
            else:
                await update.message.reply_text(
                    "Não consegui entender a duração. Por favor, tente novamente com formatos como '1 hora', '90 minutos' ou '1,5 horas'."
                )
        
        elif state == STATE_AWAITING_SUMMARY:
            # Usar o texto diretamente como título/assunto
            context.user_data['pending_event']['summary'] = text.strip()
            
            # Verificar se é um evento de reunião
            await self._check_if_meeting(update, context)
        
        elif state == STATE_AWAITING_ATTENDEES:
            # Processar lista de participantes
            attendees = []
            
            # Dividir por vírgulas
            for attendee in text.split(','):
                attendee = attendee.strip()
                if '@' in attendee:  # É um email
                    attendees.append(attendee)
                else:  # É um nome, poderia ser convertido para email em uma implementação real
                    attendees.append(attendee)
            
            if attendees:
                context.user_data['pending_event']['attendees'] = attendees
                
                # Criar o evento
                await self._create_event_from_pending(update, context)
            else:
                await update.message.reply_text(
                    "Não consegui identificar os participantes. Por favor, tente novamente com emails ou nomes separados por vírgula."
                )
        
        elif state == STATE_AWAITING_EVENT_REF:
            # Buscar eventos que correspondam à referência
            success, events = self.calendar_manager.find_events_by_query(user_id, text)
            
            if success and events:
                if len(events) == 1:
                    # Apenas um evento encontrado, usar diretamente
                    event = events[0]
                    context.user_data['pending_event']['event_id'] = event['id']
                    
                    # Processar com base na intenção
                    intent = context.user_data.get('pending_intent')
                    
                    if intent == "UPDATE_DURATION":
                        if 'duration' in context.user_data['pending_event']:
                            # Já tem duração, atualizar
                            await self._update_event_duration(update, context)
                        else:
                            # Perguntar a duração
                            await update.message.reply_text("Qual deve ser a nova duração do evento?")
                            context.user_data['state'] = STATE_AWAITING_DURATION
                    
                    elif intent == "DELETE_EVENT":
                        # Confirmar exclusão
                        context.user_data['event_to_delete'] = event['id']
                        
                        # Formatar data e hora para exibição
                        start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).replace(tzinfo=None)
                        
                        keyboard = [
                            [
                                InlineKeyboardButton("✅ Sim, excluir", callback_data="delete_yes"),
                                InlineKeyboardButton("❌ Não, cancelar", callback_data="delete_no")
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(
                            f"Você deseja excluir este evento?\n\n"
                            f"📝 {event['summary']}\n"
                            f"📅 {start.strftime('%d/%m/%Y')}\n"
                            f"🕒 {start.strftime('%H:%M')}",
                            reply_markup=reply_markup
                        )
                        context.user_data['state'] = STATE_CONFIRM_DELETE
                else:
                    # Múltiplos eventos encontrados, pedir para escolher
                    message = "Encontrei vários eventos. Qual deles você deseja?\n\n"
                    
                    for i, event in enumerate(events[:5]):  # Limitar a 5 eventos
                        start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).replace(tzinfo=None)
                        message += f"{i+1}. {event['summary']} - {start.strftime('%d/%m/%Y %H:%M')}\n"
                    
                    await update.message.reply_text(message)
                    # Mantém o estado para esperar a escolha
            else:
                await update.message.reply_text(
                    "Não encontrei eventos correspondentes à sua descrição. Por favor, tente novamente com mais detalhes."
                )
    
    async def _check_if_meeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Verifica se é um evento de reunião e pergunta se deve adicionar Google Meet"""
        # Verificar se todas as informações essenciais estão presentes
        pending_event = context.user_data.get('pending_event', {})
        has_essential_info = all(field in pending_event for field in ['date', 'time'])
        
        if has_essential_info:
            # Verificar se é reunião e não foi decidido ainda sobre o Meet
            is_meeting = pending_event.get('is_meeting', False)
            
            if is_meeting and 'add_meet_link' not in pending_event:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Sim", callback_data="meet_yes"),
                        InlineKeyboardButton("❌ Não", callback_data="meet_no")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "Deseja adicionar um link do Google Meet para esta reunião?",
                    reply_markup=reply_markup
                )
                context.user_data['state'] = STATE_AWAITING_ADD_MEET
            else:
                # Criar o evento diretamente
                await self._create_event_from_pending(update, context)
    
    async def _create_event_from_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_button=False) -> None:
        """Cria um evento a partir das informações pendentes"""
        user_id = str(update.effective_user.id)
        pending_event = context.user_data.get('pending_event', {})
        
        # Verificar se tem todas as informações necessárias
        if 'date' in pending_event and 'time' in pending_event:
            # Extrair informações
            date = pending_event.get('date')
            time = pending_event.get('time')
            duration = pending_event.get('duration', 1)  # Padrão: 1 hora
            summary = pending_event.get('summary', "Evento")
            location = pending_event.get('location')
            add_meet_link = pending_event.get('add_meet_link', False)
            attendees = pending_event.get('attendees')
            
            # Criar o evento
            success, result = self.calendar_manager.create_event(
                user_id=user_id,
                summary=summary,
                start_date=date,
                start_time=time,
                duration=duration,
                location=location,
                attendees=attendees,
                add_meet_link=add_meet_link
            )
            
            if success:
                # Formatar data e hora para exibição
                date_obj = datetime.fromisoformat(date)
                date_display = f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"
                
                hour, minute = time.split(":")
                time_display = f"{int(hour)}:{minute}"
                
                # Mensagem de sucesso
                if is_button:
                    # Editar a mensagem do botão
                    await update.callback_query.edit_message_text(
                        f"✅ Evento criado com sucesso!\n\n"
                        f"📝 {summary}\n"
                        f"📅 {date_display}\n"
                        f"🕒 {time_display}\n"
                        f"⏱️ Duração: {duration} hora(s)"
                    )
                else:
                    # Responder com nova mensagem
                    await update.message.reply_text(
                        f"✅ Evento criado com sucesso!\n\n"
                        f"📝 {summary}\n"
                        f"📅 {date_display}\n"
                        f"🕒 {time_display}\n"
                        f"⏱️ Duração: {duration} hora(s)"
                    )
            else:
                error_message = f"❌ Erro ao criar evento: {result}"
                
                if is_button:
                    await update.callback_query.edit_message_text(error_message)
                else:
                    await update.message.reply_text(error_message)
            
            # Limpar dados temporários
            if 'pending_event' in context.user_data:
                del context.user_data['pending_event']
            context.user_data['state'] = STATE_NORMAL
    
    async def _update_event_duration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Atualiza a duração de um evento"""
        user_id = str(update.effective_user.id)
        pending_event = context.user_data.get('pending_event', {})
        
        if 'event_id' in pending_event and 'duration' in pending_event:
            event_id = pending_event['event_id']
            duration = pending_event['duration']
            
            # Atualizar duração
            success, result = self.calendar_manager.update_event_duration(user_id, event_id, duration)
            
            if success:
                # Obter informações do evento atualizado
                event_success, event = self.calendar_manager.get_event_by_id(user_id, event_id)
                
                if event_success:
                    start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).replace(tzinfo=None)
                    end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))).replace(tzinfo=None)
                    
                    await update.message.reply_text(
                        f"✅ Duração atualizada com sucesso!\n\n"
                        f"📝 {event['summary']}\n"
                        f"📅 {start.strftime('%d/%m/%Y')}\n"
                        f"🕒 {start.strftime('%H:%M')} - {end.strftime('%H:%M')}\n"
                        f"⏱️ Nova duração: {duration} hora(s)"
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Duração atualizada para {duration} hora(s), mas não foi possível obter detalhes do evento."
                    )
            else:
                await update.message.reply_text(
                    f"❌ Erro ao atualizar duração: {result}"
                )
            
            # Limpar dados temporários
            if 'pending_event' in context.user_data:
                del context.user_data['pending_event']
            context.user_data['state'] = STATE_NORMAL
    
    async def _process_normal_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
        """Processa mensagens no estado normal (comando completo)"""
        user_id = str(update.effective_user.id)
        
        # Verificar se o usuário está autenticado
        if not self.auth_manager.is_authenticated(user_id):
            await update.message.reply_text(
                "Você ainda não está conectado ao Google Calendar. Use /start para configurar."
            )
            return
        
        # Processar a mensagem com NLP
        intent, entities = self.nlp_processor.process_message(text)
        
        # Verificar se entendeu a intenção
        if intent == "UNKNOWN":
            await update.message.reply_text(
                "Desculpe, não entendi o que você quer fazer. Você pode:\n"
                "• Agendar eventos: 'Agendar reunião amanhã às 10h'\n"
                "• Consultar agenda: 'O que tenho hoje?'\n"
                "• Modificar eventos: 'Mudar reunião de amanhã para sexta'\n\n"
                "Use /help para mais exemplos."
            )
            return
        
        # Verificar informações faltantes
        missing = self.nlp_processor.get_missing_info(intent, entities)
        
        if missing:
            # Armazenar intenção e informações parciais
            context.user_data['pending_intent'] = intent
            context.user_data['pending_event'] = entities
            
            # Perguntar por informações faltantes
            if 'date' in missing:
                await update.message.reply_text("Em qual data?")
                context.user_data['state'] = STATE_AWAITING_DATE
                return
            
            if 'time' in missing:
                await update.message.reply_text("Em qual horário?")
                context.user_data['state'] = STATE_AWAITING_TIME
                return
            
            if 'duration' in missing:
                await update.message.reply_text("Qual deve ser a duração?")
                context.user_data['state'] = STATE_AWAITING_DURATION
                return
            
            if 'summary' in missing:
                await update.message.reply_text("Qual é o título ou assunto do evento?")
                context.user_data['state'] = STATE_AWAITING_SUMMARY
                return
            
            if 'event_reference' in missing:
                await update.message.reply_text("Qual evento você deseja modificar?")
                context.user_data['state'] = STATE_AWAITING_EVENT_REF
                return
            
            if 'add_meet_link' in missing:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Sim", callback_data="meet_yes"),
                        InlineKeyboardButton("❌ Não", callback_data="meet_no")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "Deseja adicionar um link do Google Meet para esta reunião?",
                    reply_markup=reply_markup
                )
                context.user_data['state'] = STATE_AWAITING_ADD_MEET
                return
        
        # Se chegou aqui, temos todas as informações necessárias
        if intent == "CREATE_EVENT":
            # Criar evento
            date = entities.get('date')
            time = entities.get('time')
            duration = entities.get('duration', 1)
            summary = entities.get('summary', "Evento")
            location = entities.get('location')
            add_meet_link = entities.get('is_meeting', False)
            attendees = entities.get('attendees')
            
            success, result = self.calendar_manager.create_event(
                user_id=user_id,
                summary=summary,
                start_date=date,
                start_time=time,
                duration=duration,
                location=location,
                attendees=attendees,
                add_meet_link=add_meet_link
            )
            
            if success:
                # Formatar data e hora para exibição
                date_obj = datetime.fromisoformat(date)
                date_display = f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"
                
                hour, minute = time.split(":")
                time_display = f"{int(hour)}:{minute}"
                
                await update.message.reply_text(
                    f"✅ Evento criado com sucesso!\n\n"
                    f"📝 {summary}\n"
                    f"📅 {date_display}\n"
                    f"🕒 {time_display}\n"
                    f"⏱️ Duração: {duration} hora(s)"
                )
            else:
                await update.message.reply_text(f"❌ Erro ao criar evento: {result}")
        
        elif intent == "LIST_EVENTS":
                    # Listar eventos
                    date = entities.get('date')
                    
                    if date:
                        # Listar eventos para uma data específica
                        date_obj = datetime.fromisoformat(date)
                        next_day = (date_obj + timedelta(days=1)).isoformat() + "Z"
                        
                        success, events = self.calendar_manager.list_events(
                            user_id=user_id,
                            time_min=date + "T00:00:00Z",
                            time_max=next_day,
                            max_results=10
                        )
                    else:
                        # Listar próximos eventos
                        success, events = self.calendar_manager.list_events(
                            user_id=user_id,
                            max_results=5
                        )
                    
                    if success:
                        if events:
                            # Definir os dias da semana para formatação
                            days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                            
                            if date:
                                date_obj = datetime.fromisoformat(date)
                                weekday = days[date_obj.weekday()]
                                date_display = f"{weekday}, {date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year}"
                                message = f"📅 Eventos para {date_display}:\n\n"
                            else:
                                now = datetime.now()
                                message = f"📅 Próximos eventos a partir de hoje ({now.day:02d}/{now.month:02d}):\n\n"
                            
                            # Processar cada evento
                            for event in events:
                                start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).replace(tzinfo=None)
                                
                                # Se não for do dia específico ou estamos listando próximos eventos, mostrar a data
                                if not date or (date and start.date() != date_obj.date()):
                                    event_weekday = days[start.weekday()]
                                    date_str = f"{event_weekday}, {start.day:02d}/{start.month:02d} • "
                                else:
                                    date_str = ""
                                
                                if 'dateTime' in event['start']:  # Evento com hora específica
                                    end = datetime.fromisoformat(event['end'].get('dateTime')).replace(tzinfo=None)
                                    duration = (end - start).total_seconds() / 3600  # Duração em horas
                                    time_str = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
                                    message += f"🕒 {date_str}{time_str}: {event['summary']}"
                                    
                                    # Adicionar informações do Google Meet se disponível
                                    if 'conferenceData' in event and event['conferenceData'].get('conferenceId'):
                                        message += " 📹"
                                else:  # Evento do dia todo
                                    message += f"📌 {date_str}{event['summary']} (dia todo)"
                                
                                message += "\n"
                            
                            await update.message.reply_text(message)
                        else:
                            if date:
                                date_obj = datetime.fromisoformat(date)
                                weekday = days[date_obj.weekday()]
                                date_display = f"{weekday}, {date_obj.day:02d}/{date_obj.month:02d}"
                                await update.message.reply_text(f"Não há eventos agendados para {date_display}.")
                            else:
                                await update.message.reply_text("Não há eventos próximos agendados.")
                    else:
                        await update.message.reply_text(f"❌ Erro ao listar eventos: {events}")
            
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Lida com erros durante o processamento"""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Tentar enviar mensagem ao usuário
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou use /start para reiniciar."
            )
    
    def run(self):
        """Inicia o bot"""
        # Criar diretórios necessários
        os.makedirs("data/user_data", exist_ok=True)
        
        # Iniciar o bot
        self.app.run_polling()


def main():
    """Função principal"""
    # Criar e executar o bot
    bot = CalendarBot()
    bot.run()


if __name__ == "__main__":
    main()