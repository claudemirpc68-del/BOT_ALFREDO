"""
Handlers para ferramentas especializadas:
- /resumir   → Resumo de textos
- /traduzir  → Tradução entre idiomas
- /codigo    → Geração de código
- /linkedin  → Posts virais para LinkedIn
- /pesquisar → Pesquisa na internet via Tavily
- /lembrete  → Lembretes programados
"""

import logging
import re

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from bot.config import MAX_REMINDER_MINUTES
from bot.handlers.chat import send_long_message
from bot.services.groq_service import GroqService
from bot.services.tavily_service import TavilyService

logger = logging.getLogger(__name__)

# Mapeamento flexível de códigos e nomes de idiomas para formato legível
_LANGUAGES: dict[str, str] = {
    # Inglês
    "en": "inglês", "eng": "inglês", "english": "inglês", "ingles": "inglês", "inglês": "inglês",
    # Espanhol
    "es": "espanhol", "esp": "espanhol", "spanish": "espanhol", "espanhol": "espanhol", "castelhano": "espanhol", "castellano": "espanhol",
    # Francês
    "fr": "francês", "fra": "francês", "french": "francês", "frances": "francês", "francês": "francês",
    # Alemão
    "de": "alemão", "deu": "alemão", "ger": "alemão", "german": "alemão", "alemao": "alemão", "alemão": "alemão",
    # Italiano
    "it": "italiano", "ita": "italiano", "italian": "italiano", "italiano": "italiano",
    # Português
    "pt": "português", "por": "português", "portuguese": "português", "portugues": "português", "português": "português", "pt-br": "português", "pt-pt": "português",
    # Japonês
    "ja": "japonês", "jp": "japonês", "jpn": "japonês", "japanese": "japonês", "japones": "japonês", "japonês": "japonês",
    # Chinês
    "zh": "chinês", "chi": "chinês", "zho": "chinês", "chinese": "chinês", "chines": "chinês", "chinês": "chinês", "mandarim": "chinês",
    # Coreano
    "ko": "coreano", "kor": "coreano", "korean": "coreano", "coreano": "coreano",
    # Russo
    "ru": "russo", "rus": "russo", "russian": "russo", "russo": "russo",
    # Árabe
    "ar": "árabe", "ara": "árabe", "arabic": "árabe", "arabe": "árabe", "árabe": "árabe",
    # Holandês
    "nl": "holandês", "nld": "holandês", "dut": "holandês", "dutch": "holandês", "holandes": "holandês", "holandês": "holandês", "neerlandes": "holandês", "neerlandês": "holandês",
    # Polonês
    "pl": "polonês", "pol": "polonês", "polish": "polonês", "polones": "polonês", "polonês": "polonês",
    # Sueco
    "sv": "sueco", "swe": "sueco", "swedish": "sueco", "sueco": "sueco",
    # Turco
    "tr": "turco", "tur": "turco", "turkish": "turco", "turco": "turco",
    # Hindi
    "hi": "hindi", "hin": "hindi", "hindi": "hindi",
    # Grego
    "el": "grego", "gre": "grego", "greek": "grego", "grego": "grego",
    # Hebraico
    "he": "hebraico", "heb": "hebraico", "hebrew": "hebraico", "hebraico": "hebraico",
    # Latim
    "la": "latim", "lat": "latim", "latin": "latim", "latim": "latim",
}


def _parse_translation_args(args: list[str]) -> tuple[str | None, str | None]:
    """
    Identifica de forma inteligente o idioma de destino e o texto nos argumentos.
    Trata preposições como 'para o', 'para a', 'para', 'pra', 'to', etc.
    Retorna (target_lang, text). Se nenhum idioma explícito foi fornecido, target_lang será None.
    """
    if not args:
        return None, None

    tokens = list(args)

    # Remove preposições iniciais: 'para o', 'para a', 'para', 'pra', 'pro', 'to', 'in'
    if tokens and tokens[0].lower() in ["para", "pra", "pro", "to", "in"]:
        tokens.pop(0)
        if tokens and tokens[0].lower() in ["o", "a", "os", "as", "the"]:
            tokens.pop(0)

    if tokens:
        first = tokens[0].lower()
        if first in _LANGUAGES:
            target_lang = _LANGUAGES[first]
            remaining = tokens[1:]
            text = " ".join(remaining).strip() if remaining else None
            return target_lang, text

    # Se não especificou idioma reconhecido, nenhum idioma alvo foi fixado
    return None, " ".join(args).strip()


def _get_translation_keyboard() -> InlineKeyboardMarkup:
    """Gera teclado interativo para seleção rápida de idioma de destino."""
    keyboard = [
        [
            InlineKeyboardButton("🇧🇷 Português", callback_data="trans:português"),
            InlineKeyboardButton("🇺🇸 Inglês", callback_data="trans:inglês"),
        ],
        [
            InlineKeyboardButton("🇪🇸 Espanhol", callback_data="trans:espanhol"),
            InlineKeyboardButton("🇫🇷 Francês", callback_data="trans:francês"),
        ],
        [
            InlineKeyboardButton("🇩🇪 Alemão", callback_data="trans:alemão"),
            InlineKeyboardButton("🇮🇹 Italiano", callback_data="trans:italiano"),
        ],
        [
            InlineKeyboardButton("🇯🇵 Japonês", callback_data="trans:japonês"),
            InlineKeyboardButton("🇨🇳 Chinês", callback_data="trans:chinês"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ── /resumir ──────────────────────────────────────────────────

async def resumir_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume um texto fornecido como argumento ou mensagem respondida."""
    groq: GroqService = context.bot_data["groq"]

    text = _get_text(update, context)

    if not text:
        await update.message.reply_text(
            "📝 *Como usar o /resumir:*\n\n"
            "• `/resumir <seu texto aqui>`\n"
            "• Ou responda a uma mensagem com `/resumir`",
            parse_mode="Markdown",
        )
        return

    await update.message.chat.send_action("typing")
    response = await groq.summarize(text)

    await send_long_message(
        update, f"📝 *Resumo:*\n\n{response}"
    )


# ── /traduzir ─────────────────────────────────────────────────

async def traduzir_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Traduz um texto para o idioma especificado ou solicita o idioma interativamente."""
    groq: GroqService = context.bot_data["groq"]
    args = context.args or []

    target_lang, text = _parse_translation_args(args)

    # Se não tem texto nos args, tenta obter da mensagem respondida
    if not text:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text
        else:
            await update.message.reply_text(
                "🌐 *Como usar o /traduzir:*\n\n"
                "• `/traduzir <texto>` — O bot perguntará para qual idioma traduzir\n"
                "• `/traduzir pt <texto>` ou `/traduzir português <texto>` — Traduz direto para português\n"
                "• `/traduzir en <texto>` ou `/traduzir inglês <texto>` — Traduz direto para inglês\n"
                "• `/traduzir es <texto>` ou `/traduzir espanhol <texto>` — Traduz direto para espanhol\n"
                "• `/traduzir para o francês <texto>` — Traduz direto para francês\n"
                "• Ou responda a qualquer mensagem com `/traduzir [idioma]`",
                parse_mode="Markdown",
            )
            return

    # Se o usuário não especificou o idioma, pergunta com botões interativos
    if not target_lang:
        context.user_data["pending_translation_text"] = text
        preview = (text[:120] + "...") if len(text) > 120 else text
        await update.message.reply_text(
            f"🌐 *Para qual idioma você deseja traduzir?*\n\n"
            f"📝 *Texto:* _{preview}_\n\n"
            "👇 Escolha o idioma de destino abaixo:",
            reply_markup=_get_translation_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Se o idioma já foi especificado, traduz imediatamente
    await update.message.chat.send_action("typing")
    response = await groq.translate(text, target_lang)

    await send_long_message(
        update, f"🌐 *Tradução ({target_lang}):*\n\n{response}"
    )


async def traduzir_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa a seleção interativa de idioma via botões inline."""
    query = update.callback_query
    await query.answer()

    groq: GroqService = context.bot_data["groq"]
    data = query.data
    if not data or not data.startswith("trans:"):
        return

    target_lang = data.split(":", 1)[1]
    text = context.user_data.get("pending_translation_text")

    if not text:
        await query.edit_message_text(
            "⚠️ O texto para tradução expirou. Por favor, use `/traduzir <texto>` novamente.",
            parse_mode="Markdown",
        )
        return

    await query.edit_message_text(
        f"⏳ *Traduzindo para {target_lang}...*",
        parse_mode="Markdown",
    )

    response = await groq.translate(text, target_lang)
    final_text = f"🌐 *Tradução ({target_lang}):*\n\n{response}"

    if len(final_text) <= 4096:
        try:
            await query.edit_message_text(final_text, parse_mode="Markdown")
        except Exception:
            await query.edit_message_text(final_text)
    else:
        await query.delete_message()
        await send_long_message(update, final_text)


# ── /codigo ───────────────────────────────────────────────────

async def codigo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera código com base na descrição fornecida."""
    groq: GroqService = context.bot_data["groq"]

    text = _get_text(update, context)

    if not text:
        await update.message.reply_text(
            "💻 *Como usar o /codigo:*\n\n"
            "• `/codigo <descrição do que precisa>`\n\n"
            "*Exemplos:*\n"
            "• `/codigo função Python que calcula fibonacci`\n"
            "• `/codigo API REST em Node.js com Express`\n"
            "• `/codigo query SQL para vendas por mês`",
            parse_mode="Markdown",
        )
        return

    await update.message.chat.send_action("typing")
    response = await groq.generate_code(text)

    await send_long_message(update, response)


# ── /linkedin ─────────────────────────────────────────────────

async def linkedin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera um post viral para o LinkedIn sobre TI ou IA com base na descrição fornecida."""
    groq: GroqService = context.bot_data["groq"]

    text = _get_text(update, context)

    if not text:
        await update.message.reply_text(
            "🚀 *Como usar o /linkedin:*\n\n"
            "• `/linkedin <ideia ou assunto do post>`\n\n"
            "*Exemplos:*\n"
            "• `/linkedin suporte técnico usando IA generativa`\n"
            "• `/linkedin a importância da computação em nuvem hoje`\n"
            "• `/linkedin transição de carreira para ciência de dados`",
            parse_mode="Markdown",
        )
        return

    await update.message.chat.send_action("typing")
    response = await groq.generate_linkedin_post(text)

    await send_long_message(update, response)


# ── /pesquisar ────────────────────────────────────────────────

async def pesquisar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pesquisa na internet usando a API do Tavily e responde com IA."""
    groq: GroqService = context.bot_data["groq"]
    tavily: TavilyService = context.bot_data["tavily"]

    text = _get_text(update, context)

    if not text:
        await update.message.reply_text(
            "🔍 *Como usar o /pesquisar:*\n\n"
            "• `/pesquisar <sua pergunta>`\n\n"
            "*Exemplos:*\n"
            "• `/pesquisar últimas notícias sobre IA`\n"
            "• `/pesquisar previsão do tempo em São Paulo`\n"
            "• `/pesquisar melhores práticas de Python 2026`",
            parse_mode="Markdown",
        )
        return

    await update.message.chat.send_action("typing")

    try:
        # 1. Busca resultados no Tavily
        search_response = await tavily.search(text)

        # 2. Extrai contexto para a IA
        search_context = tavily.extract_context(search_response)

        # 3. Gera resposta inteligente com o Groq
        ai_response = await groq.search_answer(text, search_context)

        # 4. Monta a resposta final
        sources = search_response.get("results", [])[:3]
        source_links = "\n".join(
            f"• [{s.get('title', 'Fonte')[:50]}]({s.get('url', '')})"
            for s in sources
        )

        final_response = f"🔍 *Pesquisa:* _{text}_\n\n{ai_response}"
        if source_links:
            final_response += f"\n\n📚 *Fontes:*\n{source_links}"

        await send_long_message(update, final_response)

    except Exception as e:
        logger.error(f"Erro na pesquisa: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ocorreu um erro ao pesquisar. Tente novamente em alguns segundos."
        )


# ── /lembrete ─────────────────────────────────────────────────

async def lembrete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cria um lembrete único (minutos) ou recorrente (notícias diárias)."""
    args = context.args or []
    db = context.bot_data["db"]
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    user_name = user.first_name or "Amigo"

    # Garante que o usuário está registrado no banco antes de criar lembretes
    try:
        await db.save_user(user.id, user.username, user.first_name, user.last_name)
    except Exception as e:
        logger.error(f"Erro ao registrar usuário ao criar lembrete: {e}")

    if not args:
        await update.message.reply_text(
            "⏰ *Como usar o /lembrete:*\n\n"
            "• *Lembrete Simples (minutos):*\n"
            "  `/lembrete <minutos> <mensagem>`\n"
            "  _Exemplo: `/lembrete 30 Beber água`_\n\n"
            "• *Resumo Diário de Notícias:*\n"
            "  `/lembrete noticias <HH:MM> <temas>`\n"
            "  _Exemplo: `/lembrete noticias 06:35 Brasil Mundo`_",
            parse_mode="Markdown",
        )
        return

    # Caso A: Lembrete recorrente de notícias
    if args[0].lower() == "noticias":
        if len(args) < 2:
            await update.message.reply_text(
                "⚠️ Para agendar notícias, informe o horário no formato de 24h (HH:MM).\n"
                "Exemplo: `/lembrete noticias 06:35 Brasil Mundo`",
                parse_mode="Markdown",
            )
            return

        time_str = args[1]
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError()
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError()
        except ValueError:
            await update.message.reply_text(
                "⚠️ Horário inválido. Use o formato de 24h (HH:MM).\n"
                "Exemplo: `/lembrete noticias 06:35 Brasil Mundo`",
                parse_mode="Markdown",
            )
            return

        temas = " ".join(args[2:]) if len(args) > 2 else "Brasil Mundo"

        # 1. Salva no banco de dados
        try:
            reminder_id = await db.save_reminder(
                chat_id=chat_id,
                user_id=user_id,
                reminder_type="daily",
                trigger_time=f"{hour:02d}:{minute:02d}",
                content=temas
            )
        except Exception as e:
            logger.error(f"Erro ao salvar lembrete diário no banco: {e}")
            await update.message.reply_text("❌ Erro ao salvar o lembrete no banco de dados.")
            return

        # 2. Agenda no Telegram Job Queue
        from datetime import time, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
        except Exception:
            tz = timezone(timedelta(hours=-3))

        trigger_time_obj = time(hour, minute, tzinfo=tz)

        context.job_queue.run_daily(
            _daily_news_callback,
            time=trigger_time_obj,
            data={"chat_id": chat_id, "user_id": user_id, "temas": temas, "reminder_id": reminder_id},
            name=f"news_{chat_id}_{reminder_id}"
        )

        await update.message.reply_text(
            f"✅ *Lembrete diário de notícias agendado!*\n\n"
            f"⏰ Todos os dias às *{hour:02d}:{minute:02d}* (horário de Brasília)\n"
            f"📌 Assuntos: _{temas}_",
            parse_mode="Markdown",
        )
        return

    # Caso B: Lembrete simples de minutos
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Como usar lembrete simples: `/lembrete <minutos> <mensagem>`\n"
            "Exemplo: `/lembrete 30 Tomar água`",
            parse_mode="Markdown",
        )
        return

    try:
        minutes = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "⚠️ O primeiro argumento deve ser um número inteiro correspondente aos minutos.\n"
            "Exemplo: `/lembrete 30 Beber água`",
            parse_mode="Markdown",
        )
        return

    if minutes <= 0 or minutes > MAX_REMINDER_MINUTES:
        await update.message.reply_text(
            f"⚠️ O tempo deve ser entre *1* e *{MAX_REMINDER_MINUTES}* minutos.",
            parse_mode="Markdown",
        )
        return

    reminder_text = " ".join(args[1:])

    # 1. Calcula timestamp de disparo e salva no banco de dados
    from datetime import datetime, timezone, timedelta
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Sao_Paulo")
        agora_dt = datetime.now(tz)
    except Exception:
        tz = timezone(timedelta(hours=-3))
        agora_dt = datetime.now(tz)

    trigger_dt = agora_dt + timedelta(minutes=minutes)
    trigger_time_str = trigger_dt.isoformat()

    try:
        reminder_id = await db.save_reminder(
            chat_id=chat_id,
            user_id=user_id,
            reminder_type="once",
            trigger_time=trigger_time_str,
            content=reminder_text
        )
    except Exception as e:
        logger.error(f"Erro ao salvar lembrete único no banco: {e}")
        await update.message.reply_text("❌ Erro ao salvar o lembrete no banco de dados.")
        return

    # 2. Agenda no Telegram Job Queue
    context.job_queue.run_once(
        _reminder_callback,
        when=minutes * 60,
        data={"text": reminder_text, "chat_id": chat_id, "user_name": user_name, "reminder_id": reminder_id},
        name=f"reminder_{chat_id}_{reminder_id}",
    )

    time_str = f"{minutes} minutos" if minutes < 60 else f"{minutes // 60}h{f'{minutes % 60}min' if minutes % 60 else ''}"

    await update.message.reply_text(
        f"✅ *Lembrete criado!*\n\n"
        f"⏰ Vou te avisar em *{time_str}*\n"
        f"📌 _{reminder_text}_",
        parse_mode="Markdown",
    )


async def _reminder_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback executado quando o lembrete de minutos dispara."""
    data = context.job.data
    db = context.application.bot_data["db"]

    await context.bot.send_message(
        chat_id=data["chat_id"],
        text=(
            f"⏰ *LEMBRETE, {data['user_name']}!*\n\n"
            f"📌 {data['text']}"
        ),
        parse_mode="Markdown",
    )

    # Limpa do banco de dados
    try:
        await db.delete_reminder(data["reminder_id"])
    except Exception as e:
        logger.error(f"Erro ao deletar lembrete único do banco pós-disparo: {e}")


def _split_news_chunks(text: str, max_length: int = 4000) -> list[str]:
    """Divide texto longo em partes menores respeitando limites do Telegram e quebras de linha."""
    if not text:
        return []
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        # Tenta quebra de parágrafo duplo primeiro
        split_at = text.rfind("\n\n", 0, max_length)
        if split_at == -1 or split_at < max_length // 2:
            # Tenta quebra de linha simples
            split_at = text.rfind("\n", 0, max_length)
        if split_at == -1 or split_at < max_length // 2:
            # Tenta espaço
            split_at = text.rfind(" ", 0, max_length)
        if split_at == -1:
            split_at = max_length

        chunks.append(text[:split_at].strip())
        text = text[split_at:].lstrip()

    return [c for c in chunks if c]


async def _safe_send_message(bot, chat_id: int, text: str) -> None:
    """
    Envia uma mensagem no Telegram de forma segura e resiliente:
    1. Limpa blocos de raciocínio interno (<think>...</think>).
    2. Divide automaticamente em chunks se ultrapassar o limite de 4096 caracteres do Telegram.
    3. Envia com Markdown, com fallback para texto puro se houver erro de parsing em qualquer chunk.
    """
    if not text:
        return

    # 1. Limpeza de raciocínio de LLMs (<think>...</think>)
    cleaned = GroqService._clean_response(text)
    if not cleaned:
        cleaned = text.strip()

    # 2. Divide em blocos seguros
    chunks = _split_news_chunks(cleaned, max_length=4000)
    if not chunks:
        return

    # 3. Envia cada bloco
    for chunk in chunks:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Erro ao enviar chunk com Markdown para o chat {chat_id}: {e}. Tentando enviar como texto puro...")
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=chunk
                )
            except Exception as e_inner:
                logger.error(f"Erro crítico ao enviar mensagem como texto puro para o chat {chat_id}: {e_inner}")


async def _daily_news_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback diário que busca notícias, resume e envia ao usuário."""
    data = context.job.data
    chat_id = data["chat_id"]
    temas = data["temas"]
    groq = context.application.bot_data["groq"]
    tavily = context.application.bot_data["tavily"]
    db = context.application.bot_data["db"]

    logger.info(f"Disparando resumo diário de notícias para o chat {chat_id}. Temas: {temas}")

    try:
        viagem_text = ""
        if "|" in temas:
            partes_temas = temas.split("|")
            temas_noticias = partes_temas[0].strip()
            for parte in partes_temas[1:]:
                if "viagem:" in parte.lower():
                    viagem_text = parte.lower().replace("viagem:", "").strip()
        else:
            temas_noticias = temas

        termos = [t.strip() for t in temas_noticias.split() if t.strip()]
        if not termos:
            termos = ["Brasil", "Mundo"]

        contexto_pesquisa = ""
        for termo in termos:
            query = f"principais noticias de hoje sobre {termo} nos portais G1, BBC, CNN Brasil, Folha, Estadao"
            try:
                busca = await tavily.search(query)
                contexto_pesquisa += f"\n--- Notícias sobre {termo} ---\n"
                contexto_pesquisa += tavily.extract_context(busca) + "\n"
            except Exception as ex:
                logger.error(f"Erro ao buscar notícias do tema {termo}: {ex}")

        # Busca trânsito se configurado
        if viagem_text:
            maps = context.application.bot_data.get("google_maps")
            if maps and " ate " in viagem_text.lower():
                partes_rota = re.split(r'\s+ate\s+', viagem_text, flags=re.IGNORECASE)
                if len(partes_rota) == 2:
                    origem = partes_rota[0].strip()
                    destino = partes_rota[1].strip()
                    
                    if origem.lower() in ["minha localizacao", "minha localização", "aqui"]:
                        user_lat, user_lng = await db.get_user_location(data["user_id"])
                        if user_lat is not None and user_lng is not None:
                            origem = f"{user_lat},{user_lng}"
                    
                    matriz = await maps.get_distance_matrix(origem, destino)
                    if matriz:
                        contexto_pesquisa += (
                            f"\n--- Tempo de Viagem e Trânsito (Google Maps) ---\n"
                            f"Origem: {origem}\n"
                            f"Destino: {destino}\n"
                            f"Distância: {matriz['distance']}\n"
                            f"Tempo estimado: {matriz['duration']}\n"
                            f"Tempo sob trânsito atual: {matriz['duration_in_traffic']}\n"
                        )

        if not contexto_pesquisa.strip():
            contexto_pesquisa = "Não foi possível obter notícias recentes dos servidores de busca."

        from bot.prompts.skills import build_prompt
        prompt = build_prompt("news_digest")
        prompt += "\n\n[DIRETRIZ DE DESEMPENHO]\nSeja conciso, direto e dinâmico. Elabore o resumo diretamente no formato final para o Telegram."
        
        if viagem_text:
            prompt += "\n- Caso haja informações de Tempo de Viagem e Trânsito no contexto, inclua uma seção dedicada apresentando a distância, o tempo estimado e o trânsito atual de forma elegante."

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_semana_str = dias_semana[agora_dt.weekday()]
        agora_str = f"{dia_semana_str}, {agora_dt.strftime('%d/%m/%Y %H:%M:%S')}"
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Elabore o resumo diário de notícias para o usuário.\n\n"
                    f"Temas solicitados pelo usuário: {', '.join(termos)}\n\n"
                    f"Contexto das notícias e rotas encontradas:\n{contexto_pesquisa}\n\n"
                    "Formate o resumo final de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest)."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        texto_resumo = GroqService._clean_response(response.choices[0].message.content) or "🤔 Não consegui estruturar o resumo das notícias de hoje."

        await _safe_send_message(context.bot, chat_id, texto_resumo)
    except Exception as e:
        logger.error(f"Erro na execução do callback de notícias diárias: {e}", exc_info=True)
        try:
            await _safe_send_message(
                context.bot,
                chat_id,
                "❌ Não foi possível carregar as notícias diárias hoje. Verifiquei as conexões e tentarei novamente no próximo horário programado."
            )
        except Exception:
            pass


async def lembretes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista todos os lembretes ativos do usuário."""
    db = context.bot_data["db"]
    user = update.effective_user

    try:
        reminders = await db.get_user_reminders(user.id)
        if not reminders:
            await update.message.reply_text(
                "⏰ *Você não possui lembretes ou notícias agendadas.*\n\n"
                "Para criar um novo:\n"
                "• Lembrete simples: `/lembrete 30min Comprar pão`\n"
                "• Notícias diárias: `/lembrete noticias 06:30 Brasil Mundo` ou fale no chat: _'Alfredo, me mande as notícias às 06:30'_",
                parse_mode="Markdown"
            )
            return

        texto = "⏰ *Seus Lembretes e Agendamentos Ativos:*\n\n"
        for r in reminders:
            r_id = r["id"]
            r_type = r["type"]
            trigger = r["trigger_time"]
            content = r["content"]

            if r_type == "daily":
                texto += f"• *ID {r_id}* (Diário às {trigger}): 📰 Notícias sobre _{content}_\n"
            else:
                texto += f"• *ID {r_id}* (Único): 📌 _{content}_\n"

        texto += "\nPara cancelar qualquer um, use: `/cancelarlembrete <ID>`"
        await update.message.reply_text(texto, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erro ao listar lembretes: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao consultar seus lembretes.")


async def cancelar_lembrete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela um lembrete específico pelo ID."""
    db = context.bot_data["db"]
    user = update.effective_user

    if not context.args:
        await update.message.reply_text("⚠️ Uso: `/cancelarlembrete <ID>`\n(Consulte os IDs com `/lembretes`)", parse_mode="Markdown")
        return

    try:
        reminder_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ O ID do lembrete deve ser um número. Ex: `/cancelarlembrete 1`", parse_mode="Markdown")
        return

    try:
        deleted = await db.delete_reminder(reminder_id, user.id)
        if not deleted:
            await update.message.reply_text("⚠️ Lembrete não encontrado ou já executado.")
            return

        # Remove da JobQueue se estiver rodando
        jobs_cancelados = 0
        job_names = [f"reminder_{user.id}_{reminder_id}", f"news_{user.id}_{reminder_id}"]
        for name in job_names:
            for job in context.job_queue.get_jobs_by_name(name):
                job.schedule_removal()
                jobs_cancelados += 1

        logger.info(f"Lembrete {reminder_id} removido. Jobs removidos na fila: {jobs_cancelados}")
        await update.message.reply_text("✅ Lembrete cancelado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao cancelar lembrete: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao cancelar o lembrete.")


# Alias para compatibilidade
lembrete_cancelar_command = cancelar_lembrete_command


# ── /boletim ──────────────────────────────────────────────────

async def boletim_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca notícias recentes de Brasil e Mundo nos portais confiáveis e gera um boletim instantâneo."""
    db = context.bot_data["db"]
    groq = context.bot_data["groq"]
    tavily = context.bot_data["tavily"]
    user = update.effective_user

    # Garante que o usuário está registrado no banco
    try:
        await db.save_user(user.id, user.username, user.first_name, user.last_name)
    except Exception as e:
        logger.error(f"Erro ao registrar usuário ao solicitar boletim: {e}")

    await update.message.chat.send_action("typing")

    try:
        # Busca notícias para Brasil e Mundo
        manchetes = {}
        for termo in ["Brasil", "Mundo"]:
            query = f"principais noticias de hoje sobre {termo} nos portais G1, BBC, CNN Brasil, Folha, Estadao"
            try:
                busca = await tavily.search(query, max_results=3)
                manchetes[termo] = tavily.extract_context(busca)
            except Exception as ex:
                logger.error(f"Erro ao buscar notícias do tema {termo} para o boletim: {ex}")
                manchetes[termo] = "Não foi possível obter notícias recentes dos servidores de busca."

        # Busca cotações via Finexly
        finexly = context.bot_data.get("finexly")
        rates = await finexly.get_rates(base="USD", symbols="BRL,EUR") if finexly else {}
        cotacoes_context = ""
        if rates:
            cotacoes_context = f"\n--- Cotação de Moedas (Base USD) ---\nUSD/BRL: {rates.get('BRL')}\nUSD/EUR: {rates.get('EUR')}\n"

        # Combina os resultados
        contexto_pesquisa = f"--- Notícias sobre Brasil ---\n{manchetes['Brasil']}\n\n--- Notícias sobre Mundo ---\n{manchetes['Mundo']}\n"
        if cotacoes_context:
            contexto_pesquisa += cotacoes_context

        from bot.prompts.skills import build_prompt
        prompt = build_prompt("news_digest")
        prompt += "\n\n[DIRETRIZ DE DESEMPENHO]\nSeja conciso, direto e dinâmico. Elabore o boletim diretamente no formato final para o Telegram."

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_semana_str = dias_semana[agora_dt.weekday()]
        agora_str = f"{dia_semana_str}, {agora_dt.strftime('%d/%m/%Y %H:%M:%S')}"
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        saudacao = "Bom dia!" if 5 <= agora_dt.hour < 12 else "Boa tarde!" if 12 <= agora_dt.hour < 18 else "Boa noite!"

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Elabore o Boletim de Notícias de hoje.\n\n"
                    "Temas fixos: Brasil, Mundo e Mercado Financeiro (cotações USD/BRL e USD/EUR)\n\n"
                    f"Contexto das últimas manchetes e mercado financeiro:\n{contexto_pesquisa}\n\n"
                    f"Gere um Boletim de Notícias elegante e formatado de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest), integrando os destaques de notícias e os dados de câmbio de forma harmoniosa. Como a hora atual de Brasília é {agora_dt.strftime('%H:%M')}, saúde o usuário com '{saudacao}' no início do boletim."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        texto_resumo = GroqService._clean_response(response.choices[0].message.content) or "🤔 Não consegui estruturar o boletim de notícias de hoje."
        await send_long_message(update, texto_resumo)

    except Exception as e:
        logger.error(f"Erro ao gerar boletim de notícias: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao buscar e resumir as notícias de hoje.")


async def _daily_boletim_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback diário executado automaticamente às 19:00 para enviar o boletim a todos os usuários."""
    db = context.application.bot_data["db"]
    groq = context.application.bot_data["groq"]
    tavily = context.application.bot_data["tavily"]

    logger.info("Disparando Boletim Diário Automático de Notícias (19h00).")

    try:
        # Busca notícias para Brasil e Mundo
        manchetes = {}
        for termo in ["Brasil", "Mundo"]:
            query = f"principais noticias de hoje sobre {termo} nos portais G1, BBC, CNN Brasil, Folha, Estadao"
            try:
                busca = await tavily.search(query, max_results=3)
                manchetes[termo] = tavily.extract_context(busca)
            except Exception as ex:
                logger.error(f"Erro ao buscar notícias do tema {termo} para o boletim automático: {ex}")
                manchetes[termo] = "Não foi possível obter notícias recentes dos servidores de busca."

        contexto_pesquisa = f"--- Notícias sobre Brasil ---\n{manchetes['Brasil']}\n\n--- Notícias sobre Mundo ---\n{manchetes['Mundo']}\n"

        from bot.prompts.skills import build_prompt
        prompt = build_prompt("news_digest")
        prompt += "\n\n[DIRETRIZ DE DESEMPENHO]\nSeja conciso, direto e dinâmico. Elabore o boletim noturno diretamente no formato final para o Telegram."

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_semana_str = dias_semana[agora_dt.weekday()]
        agora_str = f"{dia_semana_str}, {agora_dt.strftime('%d/%m/%Y %H:%M:%S')}"
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Elabore o Boletim de Notícias de hoje.\n\n"
                    "Temas fixos: Brasil e Mundo\n\n"
                    f"Contexto das últimas manchetes encontradas nos portais confiáveis:\n{contexto_pesquisa}\n\n"
                    "Gere um Boletim de Notícias elegante e formatado de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest). Como este é o boletim noturno (19h00), saúde o usuário com um 'Boa noite!' caloroso no início do boletim."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        texto_resumo = GroqService._clean_response(response.choices[0].message.content) or "🤔 Não consegui estruturar o boletim de notícias de hoje."

        # Obtém todos os usuários cadastrados no banco para enviar o boletim
        usuarios = await db.get_active_users()
        logger.info(f"Enviando Boletim Automático para {len(usuarios)} usuários.")

        for user_id in usuarios:
            try:
                await _safe_send_message(context.bot, user_id, texto_resumo)
            except Exception as send_err:
                logger.warning(f"Não foi possível enviar boletim diário para o usuário {user_id}: {send_err}")

    except Exception as e:
        logger.error(f"Erro ao processar boletim de notícias diário automático: {e}", exc_info=True)


async def _daily_boletim_job_matinal(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback diário executado automaticamente às 06:30 para enviar o boletim matinal a todos os usuários."""
    db = context.application.bot_data["db"]
    groq = context.application.bot_data["groq"]
    tavily = context.application.bot_data["tavily"]

    logger.info("Disparando Boletim Diário Automático Matinal de Notícias (06h30).")

    try:
        # Busca notícias para Brasil e Mundo
        manchetes = {}
        for termo in ["Brasil", "Mundo"]:
            query = f"principais noticias de hoje sobre {termo} nos portais G1, BBC, CNN Brasil, Folha, Estadao"
            try:
                busca = await tavily.search(query, max_results=3)
                manchetes[termo] = tavily.extract_context(busca)
            except Exception as ex:
                logger.error(f"Erro ao buscar notícias do tema {termo} para o boletim matinal: {ex}")
                manchetes[termo] = "Não foi possível obter notícias recentes dos servidores de busca."

        # Busca cotações via Finexly
        finexly = context.application.bot_data.get("finexly")
        rates = await finexly.get_rates(base="USD", symbols="BRL,EUR") if finexly else {}
        cotacoes_context = ""
        if rates:
            cotacoes_context = f"\n--- Cotação de Moedas (Base USD) ---\nUSD/BRL: {rates.get('BRL')}\nUSD/EUR: {rates.get('EUR')}\n"

        # Combina os resultados
        contexto_pesquisa = f"--- Notícias sobre Brasil ---\n{manchetes['Brasil']}\n\n--- Notícias sobre Mundo ---\n{manchetes['Mundo']}\n"
        if cotacoes_context:
            contexto_pesquisa += cotacoes_context

        from bot.prompts.skills import build_prompt
        prompt = build_prompt("news_digest")
        prompt += "\n\n[DIRETRIZ DE DESEMPENHO]\nSeja conciso, direto e dinâmico. Elabore o boletim matinal diretamente no formato final para o Telegram."

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_semana_str = dias_semana[agora_dt.weekday()]
        agora_str = f"{dia_semana_str}, {agora_dt.strftime('%d/%m/%Y %H:%M:%S')}"
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Elabore o Boletim de Notícias Matinal de hoje.\n\n"
                    "Temas fixos: Brasil, Mundo e Mercado Financeiro (cotações USD/BRL e USD/EUR)\n\n"
                    f"Contexto das últimas manchetes e mercado financeiro:\n{contexto_pesquisa}\n\n"
                    "Gere um Boletim de Notícias elegante, focado em começar o dia bem informado, formatado de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest), integrando notícias e câmbio. Como este é o boletim matinal (06h30), saúde o usuário com um 'Bom dia!' caloroso no início do boletim."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        texto_resumo = GroqService._clean_response(response.choices[0].message.content) or "🤔 Não consegui estruturar o boletim de notícias matinal de hoje."

        # Obtém todos os usuários cadastrados no banco para enviar o boletim
        usuarios = await db.get_active_users()
        logger.info(f"Enviando Boletim Matinal Automático para {len(usuarios)} usuários.")

        for user_id in usuarios:
            try:
                await _safe_send_message(context.bot, user_id, texto_resumo)
            except Exception as send_err:
                logger.warning(f"Não foi possível enviar boletim matinal para o usuário {user_id}: {send_err}")

    except Exception as e:
        logger.error(f"Erro ao processar boletim de notícias matinal diário automático: {e}", exc_info=True)


# ── /olhardigital ─────────────────────────────────────────────

async def olhardigital_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca notícias de IA no Olhar Digital e apresenta um resumo inteligente."""
    groq: GroqService = context.bot_data["groq"]
    
    # As preferências de filtros serão extraídas dos argumentos do comando
    preferencias = context.args if context.args else None
    
    await update.message.chat.send_action("typing")
    
    try:
        from bot.services.olhardigital_service import AlfredoSkillOlharDigitalAI
        from bot.config import TAVILY_API_KEY
        from bot.prompts.skills import build_prompt
        import asyncio
        
        # Inicializa a skill do Olhar Digital
        skill = AlfredoSkillOlharDigitalAI(TAVILY_API_KEY)
        
        # Executa em thread para evitar bloquear o loop assíncrono
        resultados = await asyncio.to_thread(skill.executar, preferencias)
        
        if isinstance(resultados, dict) and "erro" in resultados:
            await update.message.reply_text(f"❌ {resultados['erro']}")
            return
            
        if not resultados:
            filtro_str = f" com o filtro '{', '.join(preferencias)}'" if preferencias else ""
            await update.message.reply_text(f"📰 Nenhuma notícia recente sobre IA encontrada no Olhar Digital{filtro_str}.")
            return
            
        # Formata as notícias como contexto de texto para a IA
        noticias_context = ""
        for i, artigo in enumerate(resultados[:5], 1):
            noticias_context += f"Notícia {i}:\nTítulo: {artigo['titulo']}\nResumo: {artigo['resumo']}\nLink: {artigo['link']}\n\n"
            
        prompt_sistema = build_prompt("olhardigital")
        prompt_sistema += "\n\n[DIRETRIZ DE DESEMPENHO]\nSeja conciso, direto e dinâmico. Elabore o resumo diretamente no formato final para o Telegram."
        
        filtro_info = f" (Filtro: {', '.join(preferencias)})" if preferencias else ""
        mensagem_usuario = (
            f"Aqui estão as últimas notícias de Inteligência Artificial do site Olhar Digital{filtro_info}:\n\n"
            f"{noticias_context}\n"
            "Resuma e organize as principais novidades de forma amigável em tópicos. "
            "Cite os links para que o usuário possa ler mais."
        )
        
        # Gera a resposta sintetizada
        resposta_ia = await groq.client.chat.completions.create(
            model=groq.model,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": mensagem_usuario}
            ],
            temperature=0.5,
            max_tokens=4096,
        )
        
        synthesized_response = GroqService._clean_response(resposta_ia.choices[0].message.content) or "🤔 Não consegui resumir as notícias."
        
        links_list = "\n".join([f"• [{a['titulo'][:50]}...]({a['link']})" for a in resultados[:5]])
        final_text = f"📰 *Últimas de IA no Olhar Digital*{filtro_info}:\n\n{synthesized_response}"
        
        if "http" not in synthesized_response:
            final_text += f"\n\n🔗 *Links das Notícias:*\n{links_list}"
            
        await send_long_message(update, final_text)
        
    except Exception as e:
        logger.error(f"Erro ao executar skill Olhar Digital: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ocorreu um erro ao buscar notícias do Olhar Digital. Tente novamente em instantes."
        )


# ── /cotacao ──────────────────────────────────────────────────

async def cotacao_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Consulta taxas de câmbio em tempo real via Finexly API."""
    finexly = context.bot_data.get("finexly")
    if not finexly:
        await update.message.reply_text("❌ Serviço de cotações não inicializado.")
        return

    await update.message.chat.send_action("typing")

    rates = await finexly.get_rates(base="USD", symbols="BRL,EUR")
    if not rates:
        await update.message.reply_text(
            "⚠️ Não foi possível obter as cotações de moedas no momento. Tente novamente mais tarde."
        )
        return

    usd_brl = rates.get("BRL")
    usd_eur = rates.get("EUR")

    try:
        usd_brl_str = f"R$ {float(usd_brl):.4f}"
    except Exception:
        usd_brl_str = str(usd_brl)

    try:
        usd_eur_str = f"€ {float(usd_eur):.4f}"
    except Exception:
        usd_eur_str = str(usd_eur)

    msg = (
        "💱 *Cotações de Moedas (Base: USD)*\n\n"
        f"💵 *Dólar Comercial (USD/BRL):* `{usd_brl_str}`\n"
        f"💶 *Dólar para Euro (USD/EUR):* `{usd_eur_str}`\n\n"
        "📈 _Valores obtidos em tempo real via Finexly API._"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


# ── /hora ─────────────────────────────────────────────────────

async def hora_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde com a data e hora atual formatada."""
    from datetime import datetime, timezone, timedelta
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Sao_Paulo")
        agora = datetime.now(tz)
    except Exception:
        # Fallback manual para o fuso horário de Brasília (UTC-3)
        tz = timezone(timedelta(hours=-3))
        agora = datetime.now(tz)
    dias_semana = {
        0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
        3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
    }
    dia_str = dias_semana[agora.weekday()]
    data_formatada = agora.strftime(f"{dia_str}, %d/%m/%Y às %H:%M:%S")
    
    await update.message.reply_text(
        f"📅 *Data e Hora Atual:*\n"
        f"⏰ `{data_formatada}`",
        parse_mode="Markdown"
    )


# ── /rota ─────────────────────────────────────────────────────

async def rota_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Consulta a melhor rota e direções passo a passo entre dois locais."""
    args = context.args or []
    maps = context.bot_data.get("google_maps")
    db = context.bot_data.get("db")
    user_id = update.effective_user.id
    
    if not maps:
        await update.message.reply_text("❌ Serviço do Google Maps não inicializado.")
        return
        
    texto = " ".join(args)
    if not texto or " ate " not in texto.lower():
        await update.message.reply_text(
            "⚠️ *Como usar o /rota:*\n"
            "`/rota <origem> ate <destino>`\n\n"
            "_Exemplo: `/rota Av Paulista 1000 ate Aeroporto de Congonhas`_\n"
            "_Ou: `/rota aqui ate Shopping Metrô Tatuapé` (se sua localização estiver registrada)_",
            parse_mode="Markdown"
        )
        return
        
    await update.message.chat.send_action("typing")
    
    partes = re.split(r'\s+ate\s+', texto, flags=re.IGNORECASE)
    origem = partes[0].strip()
    destino = partes[1].strip()
    
    if origem.lower() in ["minha localizacao", "minha localização", "aqui"]:
        lat, lng = await db.get_user_location(user_id)
        if lat is not None and lng is not None:
            origem = f"{lat},{lng}"
        else:
            await update.message.reply_text("❌ Não tenho sua localização salva. Envie sua localização física no Telegram primeiro.")
            return
            
    try:
        direcoes = await maps.get_directions(origem, destination=destino)
        if not direcoes:
            await update.message.reply_text("❌ Não foi possível calcular a rota para os locais informados.")
            return
            
        passos_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(direcoes["steps"])])
        
        msg = (
            f"🗺️ *Instruções de Rota (Google Maps)*\n\n"
            f"📍 *Origem:* {direcoes['origin_address']}\n"
            f"🏁 *Destino:* {direcoes['destination_address']}\n\n"
            f"📏 *Distância:* `{direcoes['distance']}`\n"
            f"⏱️ *Tempo Estimado:* `{direcoes['duration']}`\n\n"
            f"🥾 *Passos Principais:*\n{passos_str}"
        )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Erro no comando de rotas: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao calcular as rotas.")


# ── /onde ─────────────────────────────────────────────────────

async def onde_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca estabelecimentos próximos à localização do usuário."""
    args = context.args or []
    maps = context.bot_data.get("google_maps")
    db = context.bot_data.get("db")
    user_id = update.effective_user.id
    
    if not maps:
        await update.message.reply_text("❌ Serviço do Google Maps não inicializado.")
        return
        
    busca = " ".join(args)
    if not busca:
        await update.message.reply_text(
            "⚠️ *Como usar o /onde:*\n"
            "`/onde <tipo de estabelecimento>`\n\n"
            "_Exemplo: `/onde casa de câmbio`_\n"
            "_Exemplo: `/onde restaurante japonês`_",
            parse_mode="Markdown"
        )
        return
        
    await update.message.chat.send_action("typing")
    
    lat, lng = await db.get_user_location(user_id)
    if lat is None or lng is None:
        await update.message.reply_text(
            "❌ Sua localização de referência é desconhecida.\n\n"
            "Por favor, envie sua localização física pelo Telegram para eu guardá-la e buscar locais próximos a ela."
        )
        return
        
    try:
        locais = await maps.search_places(busca, lat, lng)
        if not locais:
            await update.message.reply_text(f"🔍 Nenhum local do tipo '{busca}' foi encontrado nas proximidades.")
            return
            
        msg = f"🔍 *Locais Próximos de Você ({busca}):*\n\n"
        for i, l in enumerate(locais, 1):
            dist_info = f" (a ~{l['distance_str']} de você)" if l.get("distance_str") else ""
            msg += (
                f"*{i}. {l['name']}*{dist_info}\n"
                f"📍 Endereço: _{l['address']}_\n"
                f"⭐ Nota: `{l['rating']}` ({l['user_ratings_total']} avaliações)\n\n"
            )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Erro no comando onde: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao buscar locais.")


# ── Utilitários ──────────────────────────────────────────────

def _get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """
    Extrai texto dos argumentos do comando ou da mensagem respondida.
    Prioriza args do comando; se vazio, tenta reply.
    """
    if context.args:
        return " ".join(context.args)

    if update.message.reply_to_message and update.message.reply_to_message.text:
        return update.message.reply_to_message.text

    return None
