"""
Handlers para comandos de configuração: /nova e /status.
Gerencia sessões de conversa do usuário.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import BOT_NAME, GROQ_MODEL
from bot.database.db import Database


async def nova_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Limpa o histórico de conversa e inicia uma nova sessão."""
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id

    count = await db.clear_history(user_id)

    await update.message.reply_text(
        f"🔄 *Conversa reiniciada!*\n\n"
        f"Apaguei {count} mensagens do histórico.\n"
        f"Pode começar um novo assunto! 😊",
        parse_mode="Markdown",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra informações sobre a sessão atual do usuário."""
    db: Database = context.bot_data["db"]
    user = update.effective_user

    msg_count = await db.get_message_count(user.id)

    status_text = (
        f"📊 *Status da Sessão — {BOT_NAME}*\n\n"
        f"👤 Usuário: {user.first_name or 'N/A'}"
        f"{f' (@{user.username})' if user.username else ''}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💬 Mensagens no histórico: {msg_count}\n"
        f"🧠 Modelo: `{GROQ_MODEL}`\n"
        f"✅ Status: *Online*"
    )

    await update.message.reply_text(status_text, parse_mode="Markdown")
