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

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import MAX_REMINDER_MINUTES
from bot.handlers.chat import send_long_message
from bot.services.groq_service import GroqService
from bot.services.tavily_service import TavilyService

logger = logging.getLogger(__name__)

# Mapeamento de códigos de idioma para nomes
_LANGUAGES: dict[str, str] = {
    "en": "inglês",
    "es": "espanhol",
    "fr": "francês",
    "de": "alemão",
    "it": "italiano",
    "ja": "japonês",
    "ko": "coreano",
    "zh": "chinês",
    "pt": "português",
    "ru": "russo",
    "ar": "árabe",
    "hi": "hindi",
    "nl": "holandês",
    "sv": "sueco",
    "pl": "polonês",
    "tr": "turco",
}


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
    """Traduz um texto para o idioma especificado (padrão: inglês)."""
    groq: GroqService = context.bot_data["groq"]
    args = context.args or []

    target_lang = "inglês"
    text = None

    if args:
        # Verifica se o primeiro argumento é um código de idioma
        first_arg = args[0].lower()
        if first_arg in _LANGUAGES:
            target_lang = _LANGUAGES[first_arg]
            text = " ".join(args[1:]) if len(args) > 1 else None
        else:
            text = " ".join(args)

    # Se não tem texto nos args, tenta a mensagem respondida
    if not text:
        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text
        else:
            langs_list = ", ".join(
                f"`{code}` ({name})" for code, name in list(_LANGUAGES.items())[:8]
            )
            await update.message.reply_text(
                "🌐 *Como usar o /traduzir:*\n\n"
                "• `/traduzir <texto>` — Traduz para inglês\n"
                "• `/traduzir en <texto>` — Traduz para inglês\n"
                "• `/traduzir es <texto>` — Traduz para espanhol\n"
                "• Ou responda a uma mensagem com `/traduzir`\n\n"
                f"*Idiomas:* {langs_list}...",
                parse_mode="Markdown",
            )
            return

    await update.message.chat.send_action("typing")
    response = await groq.translate(text, target_lang)

    await send_long_message(
        update, f"🌐 *Tradução ({target_lang}):*\n\n{response}"
    )


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


# ── /instagram ────────────────────────────────────────────────

async def instagram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera uma ideia de post com legenda e hashtags otimizadas para o Instagram."""
    groq: GroqService = context.bot_data["groq"]

    text = _get_text(update, context)

    if not text:
        await update.message.reply_text(
            "📸 *Como usar o /instagram:*\n\n"
            "• `/instagram <assunto ou ideia do post>`\n\n"
            "*Exemplos:*\n"
            "• `/instagram dicas de segurança da informação para leigos`\n"
            "• `/instagram a rotina de um programador em home office`\n"
            "• `/instagram 5 extensões indispensáveis do VS Code`",
            parse_mode="Markdown",
        )
        return

    await update.message.chat.send_action("typing")
    response = await groq.generate_instagram_post(text)

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
    """Cria um lembrete que será enviado após o tempo especificado."""
    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "⏰ *Como usar o /lembrete:*\n\n"
            "• `/lembrete <minutos> <mensagem>`\n\n"
            "*Exemplos:*\n"
            "• `/lembrete 30 Hora de beber água`\n"
            "• `/lembrete 60 Reunião com o time`\n"
            "• `/lembrete 5 Verificar o forno`",
            parse_mode="Markdown",
        )
        return

    # Valida o tempo
    try:
        minutes = int(args[0])
    except ValueError:
        await update.message.reply_text(
            "⚠️ O primeiro argumento deve ser um número (minutos).\n"
            "Exemplo: `/lembrete 30 Beber água`",
            parse_mode="Markdown",
        )
        return

    if minutes <= 0 or minutes > MAX_REMINDER_MINUTES:
        await update.message.reply_text(
            f"⚠️ O tempo deve ser entre *1* e *{MAX_REMINDER_MINUTES}* minutos "
            f"({MAX_REMINDER_MINUTES // 60} horas).",
            parse_mode="Markdown",
        )
        return

    reminder_text = " ".join(args[1:])
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "Amigo"

    # Agenda o lembrete
    context.job_queue.run_once(
        _reminder_callback,
        when=minutes * 60,
        data={"text": reminder_text, "chat_id": chat_id, "user_name": user_name},
        name=f"reminder_{chat_id}_{minutes}",
    )

    # Formata a confirmação
    if minutes >= 60:
        hours = minutes // 60
        remaining = minutes % 60
        time_str = f"{hours}h{f'{remaining}min' if remaining else ''}"
    else:
        time_str = f"{minutes} minutos"

    await update.message.reply_text(
        f"✅ *Lembrete criado!*\n\n"
        f"⏰ Vou te avisar em *{time_str}*\n"
        f"📌 _{reminder_text}_",
        parse_mode="Markdown",
    )


async def _reminder_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback executado quando o lembrete dispara."""
    data = context.job.data

    await context.bot.send_message(
        chat_id=data["chat_id"],
        text=(
            f"⏰ *LEMBRETE, {data['user_name']}!*\n\n"
            f"📌 {data['text']}"
        ),
        parse_mode="Markdown",
    )


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
            temperature=0.6,
            max_tokens=2048,
        )
        
        synthesized_response = resposta_ia.choices[0].message.content or "🤔 Não consegui resumir as notícias."
        
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
