"""
ALFREDO — Bot Assistente Pessoal no Telegram.
Entry point: inicializa serviços, registra handlers e inicia o polling.
"""

import os
import sys
from pathlib import Path

# Garante que o diretório raiz do projeto esteja no sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bot.config import TELEGRAM_BOT_TOKEN, GROQ_API_KEY, GROQ_MODEL, GROQ_VISION_MODEL, BOT_NAME, DB_PATH, TAVILY_API_KEY
from bot.database.db import Database
from bot.handlers.chat import handle_photo, handle_text, handle_location
from bot.handlers.settings import nova_command, status_command
from bot.handlers.start import help_command, start_command

from bot.handlers.tools import (
    codigo_command,
    lembrete_command,
    lembretes_command,
    lembrete_cancelar_command,
    pesquisar_command,
    resumir_command,
    traduzir_command,
    traduzir_callback_handler,
    linkedin_command,
    olhardigital_command,
    hora_command,
    boletim_command,
    cotacao_command,
    rota_command,
    onde_command,
)
from bot.services.groq_service import GroqService
from bot.services.tavily_service import TavilyService

# ── Logging ───────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    level=logging.INFO,
)
# Reduz logs verbosos de bibliotecas externas
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ── Lifecycle hooks ───────────────────────────────────────────

async def post_init(application) -> None:
    """Inicializa banco de dados, serviço Groq e restaura lembretes do banco."""
    # Banco de dados
    db = Database(DB_PATH)
    await db.initialize()
    application.bot_data["db"] = db

    # Serviço Groq
    groq = GroqService(api_key=GROQ_API_KEY, model=GROQ_MODEL, vision_model=GROQ_VISION_MODEL)
    application.bot_data["groq"] = groq

    # Serviço Tavily (pesquisa na internet)
    tavily = TavilyService(api_key=TAVILY_API_KEY)
    application.bot_data["tavily"] = tavily

    # Serviço Finexly (cotação de moedas)
    from bot.services.finexly_service import FinexlyService
    from bot.config import FINEXLY_API_KEY
    finexly = FinexlyService(api_key=FINEXLY_API_KEY)
    application.bot_data["finexly"] = finexly

    # Serviço Google Maps (localização e rotas)
    from bot.services.google_maps_service import GoogleMapsService
    from bot.config import GOOGLE_MAPS_API_KEY
    google_maps = GoogleMapsService(api_key=GOOGLE_MAPS_API_KEY)
    application.bot_data["google_maps"] = google_maps

    # Serviço GENNIE (E-mails & Gmail via Bridge)
    from bot.services.gennie_service import GennieService
    gennie = GennieService()
    application.bot_data["gennie"] = gennie

    # Configura o menu autocompletar de comandos no Telegram quando o usuário digita /
    commands = [
        BotCommand("start", "Iniciar atendimento e ver boas-vindas"),
        BotCommand("help", "Ajuda e menu com todos os comandos disponíveis"),
        BotCommand("nova", "Iniciar uma nova conversa e limpar histórico"),
        BotCommand("status", "Verificar o status e saúde do bot"),
        BotCommand("resumir", "Resumir um texto ou mensagem"),
        BotCommand("traduzir", "Traduzir texto para outro idioma"),
        BotCommand("codigo", "Gerar ou explicar código de programação"),
        BotCommand("linkedin", "Gerar post atraente para o LinkedIn"),
        BotCommand("pesquisar", "Pesquisar informações em tempo real na web"),
        BotCommand("olhardigital", "Ler as últimas notícias do Olhar Digital"),
        BotCommand("boletim", "Gerar resumo das principais notícias do dia"),
        BotCommand("cotacao", "Consultar cotação de moedas (ex: USD BRL)"),
        BotCommand("rota", "Calcular rota de transporte (origem para destino)"),
        BotCommand("onde", "Localizar lugares e estabelecimentos próximos"),
        BotCommand("hora", "Consultar a data e hora oficial de Brasília"),
        BotCommand("lembrete", "Agendar um lembrete (ex: /lembrete 30m remedio)"),
        BotCommand("lembretes", "Listar todos os seus lembretes ativos"),
        BotCommand("lembrete_cancelar", "Cancelar um lembrete pelo ID"),
        BotCommand("email", "Consultar e-mails e briefings da GENNIE"),

    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Menu autocompletar de comandos do Telegram registrado com sucesso!")
    except Exception as ex_cmd:
        logger.error(f"Erro ao registrar menu de comandos no Telegram: {ex_cmd}")

    logger.info(f"{BOT_NAME} inicializado com sucesso!")
    logger.info(f"Modelo: {GROQ_MODEL}")
    logger.info(f"Banco de dados: {DB_PATH}")

    # Restauração de Lembretes do Banco
    try:
        reminders = await db.get_active_reminders()
        count_restored = 0
        from datetime import datetime, timezone, timedelta
        from bot.handlers.tools import _reminder_callback, _daily_news_callback
        
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
        except Exception:
            tz = timezone(timedelta(hours=-3))
            
        agora_dt = datetime.now(tz)
        
        for r in reminders:
            r_id = r["id"]
            chat_id = r["chat_id"]
            user_id = r["user_id"]
            r_type = r["type"]
            trigger_time = r["trigger_time"]
            content = r["content"]
            
            # Caso A: Lembrete diário de notícias
            if r_type == "daily":
                try:
                    parts = trigger_time.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1])
                    from datetime import time
                    trigger_time_obj = time(hour, minute, tzinfo=tz)
                    
                    application.job_queue.run_daily(
                        _daily_news_callback,
                        time=trigger_time_obj,
                        data={"chat_id": chat_id, "user_id": user_id, "temas": content, "reminder_id": r_id},
                        name=f"news_{chat_id}_{r_id}"
                    )
                    count_restored += 1
                except Exception as ex:
                    logger.error(f"Erro ao restaurar lembrete diário {r_id}: {ex}")
                    
            # Caso B: Lembrete simples de minutos
            elif r_type == "once":
                try:
                    trigger_dt = datetime.fromisoformat(trigger_time)
                    seconds_left = (trigger_dt - agora_dt).total_seconds()
                    
                    if seconds_left <= 0:
                        # Se já expirou enquanto o bot estava offline, agenda para disparar em 2 segundos
                        seconds_left = 2
                        
                    application.job_queue.run_once(
                        _reminder_callback,
                        when=seconds_left,
                        data={"text": content, "chat_id": chat_id, "user_name": "Amigo", "reminder_id": r_id},
                        name=f"reminder_{chat_id}_{r_id}"
                    )
                    count_restored += 1
                except Exception as ex:
                    logger.error(f"Erro ao restaurar lembrete único {r_id}: {ex}")
                    
        if count_restored > 0:
            logger.info(f"Restaurados {count_restored} lembretes do banco de dados na inicialização.")
    except Exception as e:
        logger.error(f"Erro ao restaurar lembretes na inicialização: {e}")

    # Agendamentos de Boletins Diários Automáticos
    try:
        from bot.handlers.tools import _daily_boletim_job, _daily_boletim_job_matinal
        from datetime import time
        
        # 1. Boletim Matinal (06h30)
        trigger_time_06h30 = time(6, 30, tzinfo=tz)
        for job in application.job_queue.get_jobs_by_name("boletim_diario_06h30"):
            job.schedule_removal()
            
        application.job_queue.run_daily(
            _daily_boletim_job_matinal,
            time=trigger_time_06h30,
            name="boletim_diario_06h30"
        )
        logger.info("Agendamento do Boletim Diário Automático Matinal (06h30) configurado com sucesso.")
        
        # 2. Boletim Noturno (19h00)
        trigger_time_19h = time(19, 0, tzinfo=tz)
        for job in application.job_queue.get_jobs_by_name("boletim_diario_19h"):
            job.schedule_removal()
            
        application.job_queue.run_daily(
            _daily_boletim_job,
            time=trigger_time_19h,
            name="boletim_diario_19h"
        )
        logger.info("Agendamento do Boletim Diário Automático Noturno (19h00) configurado com sucesso.")
        
    except Exception as ex:
        logger.error(f"Erro ao agendar Boletins Diários: {ex}")


async def post_shutdown(application) -> None:
    """Fecha conexões ao encerrar o bot."""
    db: Database | None = application.bot_data.get("db")
    if db:
        await db.close()
    logger.info(f"{BOT_NAME} encerrado com sucesso.")


async def error_handler(update, context) -> None:
    """Handler global de erros — loga e notifica o usuário."""
    logger.error(f"Erro não tratado: {context.error}", exc_info=context.error)

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Ocorreu um erro inesperado ao processar sua mensagem.\n"
                "Por favor, tente novamente em alguns segundos."
            )
        except Exception:
            pass  # Não deixa o error handler falhar


# ── Healthcheck HTTP Server para Coolify / Reverse Proxy ────────
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import json
from bot.services.task_queue import obter_proxima_tarefa, registrar_resultado

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/agent/poll"):
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            task = obter_proxima_tarefa()
            res = json.dumps({"status": "ok", "task": task}, ensure_ascii=False)
            self.wfile.write(res.encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        res = '{"status": "online", "bot": "' + str(BOT_NAME) + '", "message": "🤖 ALFREDO Telegram Bot está online e operacional!"}'
        self.wfile.write(res.encode("utf-8"))

    def do_POST(self):
        if self.path.startswith("/api/agent/result"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
                task_id = data.get("id")
                output = data.get("output", "")
                if task_id and registrar_resultado(task_id, output):
                    self.send_response(200)
                    self.send_header("Content-type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok"}')
                    return
            except Exception as e:
                logger.error(f"Erro ao processar resultado do agente: {e}")
        self.send_response(400)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(b'{"status": "error"}')

    def log_message(self, format, *args):
        pass

def iniciar_servidor_healthcheck():
    port = int(os.environ.get("PORT", 80))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Servidor HTTP Healthcheck rodando na porta {port}")
    except Exception as e:
        logger.warning(f"Não foi possível abrir porta HTTP {port} para healthcheck: {e}")


# ── Main ──────────────────────────────────────────────────────

def main() -> None:
    """Constrói e executa o bot ALFREDO."""
    iniciar_servidor_healthcheck()
    print(f"""
=============================================
   {BOT_NAME} - Assistente Pessoal
   Telegram Bot | Powered by Google Gemini
=============================================
    """)

    # Configura cliente HTTP com timeout expandido para conexões instáveis
    request_config = HTTPXRequest(connect_timeout=20.0, read_timeout=20.0)

    # Constrói a aplicação
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request_config)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # ── Registra handlers de comandos ──
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("nova", nova_command))
    app.add_handler(CommandHandler("reset", nova_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("resumir", resumir_command))
    app.add_handler(CommandHandler("traduzir", traduzir_command))
    app.add_handler(CommandHandler("codigo", codigo_command))
    app.add_handler(CommandHandler("linkedin", linkedin_command))
    app.add_handler(CommandHandler("pesquisar", pesquisar_command))
    app.add_handler(CommandHandler("lembrete", lembrete_command))
    app.add_handler(CommandHandler("lembretes", lembretes_command))
    app.add_handler(CommandHandler("lembrete_cancelar", lembrete_cancelar_command))
    app.add_handler(CommandHandler("cancelarlembrete", lembrete_cancelar_command))
    app.add_handler(CommandHandler("olhardigital", olhardigital_command))
    app.add_handler(CommandHandler("boletim", boletim_command))
    app.add_handler(CommandHandler("cotacao", cotacao_command))
    app.add_handler(CommandHandler("rota", rota_command))
    app.add_handler(CommandHandler("onde", onde_command))
    app.add_handler(CommandHandler("hora", hora_command))
    from bot.handlers.email_handler import email_command
    app.add_handler(CommandHandler(("email", "emails"), email_command))
    app.add_handler(CommandHandler("data", hora_command))


    # ── Registra handlers de callbacks (botões interativos) ──
    app.add_handler(CallbackQueryHandler(traduzir_callback_handler, pattern=r"^trans:"))

    # ── Registra handlers de mensagens ──
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # ── Handler global de erros ──
    app.add_error_handler(error_handler)

    # ── Inicia o bot ──
    print(f"[OK] {BOT_NAME} esta rodando! Pressione Ctrl+C para parar.\n")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
