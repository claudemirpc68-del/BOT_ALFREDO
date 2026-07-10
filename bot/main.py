"""
ALFREDO — Bot Assistente Pessoal no Telegram.
Entry point: inicializa serviços, registra handlers e inicia o polling.
"""

import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bot.config import TELEGRAM_BOT_TOKEN, GROQ_API_KEY, GROQ_MODEL, BOT_NAME, DB_PATH, TAVILY_API_KEY
from bot.database.db import Database
from bot.handlers.chat import handle_photo, handle_text
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
    linkedin_command,
    olhardigital_command,
    instagram_command,
    hora_command,
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
    groq = GroqService(api_key=GROQ_API_KEY, model=GROQ_MODEL)
    application.bot_data["groq"] = groq

    # Serviço Tavily (pesquisa na internet)
    tavily = TavilyService(api_key=TAVILY_API_KEY)
    application.bot_data["tavily"] = tavily

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


# ── Main ──────────────────────────────────────────────────────

def main() -> None:
    """Constrói e executa o bot ALFREDO."""
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
    app.add_handler(CommandHandler("instagram", instagram_command))
    app.add_handler(CommandHandler("pesquisar", pesquisar_command))
    app.add_handler(CommandHandler("lembrete", lembrete_command))
    app.add_handler(CommandHandler("lembretes", lembretes_command))
    app.add_handler(CommandHandler("lembrete_cancelar", lembrete_cancelar_command))
    app.add_handler(CommandHandler("olhardigital", olhardigital_command))
    app.add_handler(CommandHandler("hora", hora_command))
    app.add_handler(CommandHandler("data", hora_command))

    # ── Registra handlers de mensagens ──
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # ── Handler global de erros ──
    app.add_error_handler(error_handler)

    # ── Inicia o bot ──
    print(f"[OK] {BOT_NAME} esta rodando! Pressione Ctrl+C para parar.\n")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
