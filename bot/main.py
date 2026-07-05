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

from bot.config import TELEGRAM_BOT_TOKEN, GROQ_API_KEY, GROQ_MODEL, BOT_NAME, DB_PATH, TAVILY_API_KEY
from bot.database.db import Database
from bot.handlers.chat import handle_photo, handle_text
from bot.handlers.settings import nova_command, status_command
from bot.handlers.start import help_command, start_command
from bot.handlers.tools import (
    codigo_command,
    lembrete_command,
    pesquisar_command,
    resumir_command,
    traduzir_command,
    linkedin_command,
    olhardigital_command,
    instagram_command,
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
    """Inicializa banco de dados e serviço Groq após o app arrancar."""
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

    # Constrói a aplicação
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
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
    app.add_handler(CommandHandler("olhardigital", olhardigital_command))

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
