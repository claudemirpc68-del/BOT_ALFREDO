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


async def _safe_send_message(bot, chat_id: int, text: str) -> None:
    """Envia uma mensagem no Telegram com Markdown, e faz fallback para texto puro se houver erro de parsing."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Erro ao enviar mensagem com Markdown para o chat {chat_id}: {e}. Tentando enviar como texto puro...")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text
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

    logger.info(f"Disparando resumo diário de notícias para o chat {chat_id}. Temas: {temas}")

    try:
        termos = [t.strip() for t in temas.split() if t.strip()]
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

        if not contexto_pesquisa.strip():
            contexto_pesquisa = "Não foi possível obter notícias recentes dos servidores de busca."

        from bot.prompts.skills import build_prompt
        prompt = build_prompt("news_digest")

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    f"Elabore o resumo diário de notícias para o usuário.\n\n"
                    f"Temas solicitados pelo usuário: {', '.join(termos)}\n\n"
                    f"Contexto das notícias encontradas na internet:\n{contexto_pesquisa}\n\n"
                    "Formate o resumo final de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest)."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.6,
            max_tokens=2048
        )

        texto_resumo = response.choices[0].message.content or "🤔 Não consegui estruturar o resumo das notícias de hoje."

        await _safe_send_message(context.bot, chat_id, texto_resumo)
    except Exception as e:
        logger.error(f"Erro na execução do callback de notícias diárias: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Ocorreu um erro ao processar o seu lembrete diário de notícias."
            )
        except Exception:
            pass


async def lembretes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista todos os lembretes ativos do usuário."""
    db = context.bot_data["db"]
    user = update.effective_user
    user_id = user.id

    try:
        try:
            await db.save_user(user.id, user.username, user.first_name, user.last_name)
        except Exception as e:
            logger.error(f"Erro ao registrar usuário ao listar lembretes: {e}")

        reminders = await db.get_user_reminders(user_id)
        if not reminders:
            await update.message.reply_text("⏰ Você não possui nenhum lembrete ativo no momento.")
            return

        text = "⏰ *Seus Lembretes Ativos:*\n\n"
        for r in reminders:
            r_id = r["id"]
            r_type = "Diário" if r["type"] == "daily" else "Único"
            r_time = r["trigger_time"]
            r_content = r["content"]

            if r["type"] == "daily":
                text += f"• *ID:* `{r_id}` | 📅 *{r_type} às {r_time}*\n"
                text += f"  📌 Temas: _{r_content}_\n\n"
            else:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(r_time)
                    time_str = dt.strftime("%d/%m/%Y às %H:%M")
                except Exception:
                    time_str = r_time
                text += f"• *ID:* `{r_id}` | ⏰ *{r_type} para {time_str}*\n"
                text += f"  📌 Lembrete: _{r_content}_\n\n"

        text += "💡 Para cancelar um lembrete, use: `/lembrete_cancelar <ID>`"
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Erro ao listar lembretes: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao listar seus lembretes.")


async def lembrete_cancelar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela um lembrete ativo com base no ID."""
    db = context.bot_data["db"]
    user = update.effective_user
    user_id = user.id
    args = context.args or []

    if not args:
        await update.message.reply_text("⚠️ Como usar: `/lembrete_cancelar <ID>`\nExemplo: `/lembrete_cancelar 5`")
        return

    try:
        try:
            await db.save_user(user.id, user.username, user.first_name, user.last_name)
        except Exception as e:
            logger.error(f"Erro ao registrar usuário ao cancelar lembrete: {e}")
        reminder_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ O ID do lembrete deve ser um número inteiro.")
        return

    try:
        reminders = await db.get_user_reminders(user_id)
        reminder = next((r for r in reminders if r["id"] == reminder_id), None)

        if not reminder:
            await update.message.reply_text("❌ Lembrete não encontrado ou você não tem permissão para cancelá-lo.")
            return

        # 1. Exclui do banco
        await db.delete_reminder(reminder_id)

        # 2. Cancela da job_queue do bot
        jobs_cancelados = 0
        for job in context.job_queue.jobs():
            job_data = job.data or {}
            if job_data.get("reminder_id") == reminder_id:
                job.schedule_removal()
                jobs_cancelados += 1

        logger.info(f"Lembrete {reminder_id} removido. Jobs removidos na fila: {jobs_cancelados}")
        await update.message.reply_text("✅ Lembrete cancelado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao cancelar lembrete: {e}", exc_info=True)
        await update.message.reply_text("❌ Ocorreu um erro ao cancelar o lembrete.")


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
                busca = await tavily.search(query)
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

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Elabore o Boletim de Notícias de hoje.\n\n"
                    "Temas fixos: Brasil, Mundo e Mercado Financeiro (cotações USD/BRL e USD/EUR)\n\n"
                    f"Contexto das últimas manchetes e mercado financeiro:\n{contexto_pesquisa}\n\n"
                    "Gere um Boletim de Notícias elegante e formatado de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest), integrando os destaques de notícias e os dados de câmbio de forma harmoniosa."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.6,
            max_tokens=2048
        )

        texto_resumo = response.choices[0].message.content or "🤔 Não consegui estruturar o boletim de notícias de hoje."
        try:
            await update.message.reply_text(texto_resumo, parse_mode="Markdown")
        except Exception as markdown_err:
            logger.warning(f"Erro ao enviar boletim interativo com Markdown: {markdown_err}. Enviando texto puro.")
            await update.message.reply_text(texto_resumo)

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
                busca = await tavily.search(query)
                manchetes[termo] = tavily.extract_context(busca)
            except Exception as ex:
                logger.error(f"Erro ao buscar notícias do tema {termo} para o boletim automático: {ex}")
                manchetes[termo] = "Não foi possível obter notícias recentes dos servidores de busca."

        contexto_pesquisa = f"--- Notícias sobre Brasil ---\n{manchetes['Brasil']}\n\n--- Notícias sobre Mundo ---\n{manchetes['Mundo']}\n"

        from bot.prompts.skills import build_prompt
        prompt = build_prompt("news_digest")

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Elabore o Boletim de Notícias de hoje.\n\n"
                    "Temas fixos: Brasil e Mundo\n\n"
                    f"Contexto das últimas manchetes encontradas nos portais confiáveis:\n{contexto_pesquisa}\n\n"
                    "Gere um Boletim de Notícias elegante e formatado de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest)."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.6,
            max_tokens=2048
        )

        texto_resumo = response.choices[0].message.content or "🤔 Não consegui estruturar o boletim de notícias de hoje."

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
                busca = await tavily.search(query)
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

        from datetime import datetime, timezone, timedelta
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("America/Sao_Paulo")
            agora_dt = datetime.now(tz)
        except Exception:
            tz = timezone(timedelta(hours=-3))
            agora_dt = datetime.now(tz)

        agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")
        prompt += f"\n\n[INFORMAÇÃO DO SISTEMA]\nData e hora atual de Brasília: {agora_str}."

        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": (
                    "Elabore o Boletim de Notícias Matinal de hoje.\n\n"
                    "Temas fixos: Brasil, Mundo e Mercado Financeiro (cotações USD/BRL e USD/EUR)\n\n"
                    f"Contexto das últimas manchetes e mercado financeiro:\n{contexto_pesquisa}\n\n"
                    "Gere um Boletim de Notícias elegante, focado em começar o dia bem informado, formatado de acordo com a sua Habilidade de Resumo de Notícias Cotidianas (News Digest), integrando notícias e câmbio."
                )
            }
        ]

        response = await groq.client.chat.completions.create(
            model=groq.model,
            messages=messages,
            temperature=0.6,
            max_tokens=2048
        )

        texto_resumo = response.choices[0].message.content or "🤔 Não consegui estruturar o boletim de notícias matinal de hoje."

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
