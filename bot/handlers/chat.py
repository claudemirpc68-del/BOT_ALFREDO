import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import MAX_MESSAGE_LENGTH
from bot.database.db import Database
from bot.services.groq_service import GroqService

logger = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa mensagens de texto e envia para o Groq com contexto.
    Mantém o histórico de conversa no banco de dados.
    """
    db: Database = context.bot_data["db"]
    groq: GroqService = context.bot_data["groq"]
    user = update.effective_user
    message_text = update.message.text

    # Registra/atualiza o usuário
    await db.save_user(user.id, user.username, user.first_name, user.last_name)

    # Mostra indicador de "digitando..."
    await update.message.chat.send_action("typing")

    # Busca histórico de conversa
    history = await db.get_history(user.id)

    # Obtém resposta da IA
    response = await groq.chat(message_text, history)

    # Salva ambas as mensagens no histórico
    await db.save_message(user.id, "user", message_text)
    await db.save_message(user.id, "model", response)

    # Envia resposta (dividindo se necessário)
    await send_long_message(update, response)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processa fotos enviadas pelo usuário.
    Baixa a imagem e envia para análise pelo Groq Vision.
    """
    db: Database = context.bot_data["db"]
    groq: GroqService = context.bot_data["groq"]
    user = update.effective_user

    # Registra/atualiza o usuário
    await db.save_user(user.id, user.username, user.first_name, user.last_name)

    # Mostra indicador de "digitando..."
    await update.message.chat.send_action("typing")

    # Pega a foto na maior resolução disponível
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    caption = update.message.caption
    history = await db.get_history(user.id)

    # Analisa a imagem com o Groq
    response = await groq.analyze_image(
        bytes(image_bytes), "image/jpeg", caption, history
    )

    # Salva no histórico (representação textual da imagem)
    user_msg = f"[📷 Imagem enviada]{f': {caption}' if caption else ''}"
    await db.save_message(user.id, "user", user_msg)
    await db.save_message(user.id, "model", response)

    await send_long_message(update, response)


async def send_long_message(update: Update, text: str) -> None:
    """
    Envia uma mensagem, dividindo em chunks se exceder o limite do Telegram.
    Tenta enviar com Markdown; se falhar, envia como texto puro.
    """
    if not text:
        text = "🤔 Resposta vazia recebida."

    if len(text) <= MAX_MESSAGE_LENGTH:
        await _safe_reply(update, text)
        return

    # Divide em chunks respeitando quebras de linha/espaços
    chunks = _split_text(text, MAX_MESSAGE_LENGTH)

    for chunk in chunks:
        await _safe_reply(update, chunk)


async def _safe_reply(update: Update, text: str) -> None:
    """Envia resposta com Markdown, fallback para texto puro se der erro."""
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        # Markdown inválido — tenta sem formatação
        try:
            await update.message.reply_text(text)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")


def _split_text(text: str, max_length: int) -> list[str]:
    """Divide texto em chunks inteligentes, respeitando quebras naturais."""
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Tenta dividir em quebra de linha
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1 or split_at < max_length // 2:
            # Tenta dividir em espaço
            split_at = text.rfind(" ", 0, max_length)
        if split_at == -1:
            # Último recurso: corta no limite
            split_at = max_length

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    return chunks
