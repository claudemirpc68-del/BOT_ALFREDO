"""
Handler do comando /email e /emails para o BOT ALFREDO.
Conecta-se ao GENNIE BOT via GennieService para exibir a caixa de entrada,
briefings executivos e detalhes de e-mails com elegância no Telegram.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.gennie_service import GennieService

logger = logging.getLogger(__name__)


async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Comando unificado de e-mails no Alfredo.
    Uso:
      /email             -> Lista os 3 e-mails mais recentes da Inbox
      /email nao-lidos   -> Lista apenas e-mails não lidos
      /email briefing    -> Exibe o briefing executivo consolidado do dia
      /email ler <id>    -> Lê o conteúdo completo de um e-mail
    """
    if not update.effective_message:
        return

    gennie: GennieService = context.bot_data.get("gennie")
    if not gennie:
        gennie = GennieService()

    args = context.args or []
    subcomando = args[0].lower() if args else ""

    # ── 1. Subcomando: Briefing ──────────────────────────────────────────────
    if subcomando in ("briefing", "resumo", "hoje"):
        await update.effective_message.reply_text("⏳ _Consultando a GENNIE para compilar o briefing de e-mails..._", parse_mode="Markdown")
        res = await gennie.obter_briefing(max_emails=6)
        if not res.get("sucesso"):
            await update.effective_message.reply_text(f"❌ *Não foi possível obter o briefing da GENNIE:*\n`{res.get('erro')}`", parse_mode="Markdown")
            return

        sintese = res.get("sintese_executiva")
        total = res.get("total_analisados", 0)
        
        if sintese:
            texto_resp = f"🧞 *Briefing Executivo de E-mails (via GENNIE)*\n\n{sintese}"
        else:
            texto_resp = f"📬 *Briefing:* {total} e-mail(s) recente(s) analisado(s)."

        await update.effective_message.reply_text(texto_resp, parse_mode="Markdown")
        return

    # ── 2. Subcomando: Ler e-mail específico ─────────────────────────────────
    if subcomando in ("ler", "ver", "detalhe") and len(args) > 1:
        msg_id = args[1].strip()
        await update.effective_message.reply_text(f"⏳ _Buscando e-mail `{msg_id}` com a GENNIE..._", parse_mode="Markdown")
        res = await gennie.ler_email(msg_id)
        if not res.get("sucesso"):
            await update.effective_message.reply_text(f"❌ *Erro ao ler e-mail:* `{res.get('erro')}`", parse_mode="Markdown")
            return

        email = res.get("email", {})
        anexos_txt = "\n📎 *Anexos:* " + ", ".join(email.get("anexos", [])) if email.get("anexos") else ""
        corpo = email.get("body", "")[:2500]

        texto_email = (
            f"📨 *E-mail:* `{email.get('id')}`\n"
            f"👤 *De:* {email.get('from')}\n"
            f"📌 *Assunto:* {email.get('subject')}\n"
            f"📅 *Data:* {email.get('date')}{anexos_txt}\n\n"
            f"📝 *Conteúdo:*\n{corpo}"
        )
        await update.effective_message.reply_text(texto_email, parse_mode="Markdown")
        return

    # ── 3. Subcomando Padrão: Listagem de E-mails ───────────────────────────
    query = "in:inbox is:unread" if subcomando in ("nao-lidos", "unread", "novos") else "in:inbox"
    status_txt = "não lidos" if "is:unread" in query else "recentes"

    await update.effective_message.reply_text(f"⏳ _Verificando e-mails {status_txt} com a GENNIE..._", parse_mode="Markdown")
    res = await gennie.listar_emails(query=query, max_results=4)

    if not res.get("sucesso"):
        await update.effective_message.reply_text(
            f"⚠️ *A GENNIE não respondeu no momento.*\n"
            f"Verifique se o processo da GENNIE e o Bridge Server estão ativos.\n"
            f"Detalhe: `{res.get('erro')}`",
            parse_mode="Markdown"
        )
        return

    emails = res.get("emails", [])
    if not emails:
        await update.effective_message.reply_text(f"📬 *Nenhum e-mail encontrado na caixa de entrada.* ({query})", parse_mode="Markdown")
        return

    linhas = ["📬 *E-mails na Caixa de Entrada (via GENNIE):*\n"]
    for i, e in enumerate(emails, 1):
        tags = []
        if e.get("unread"):
            tags.append("🔴 *Novo*")
        if e.get("starred"):
            tags.append("⭐ *Estrela*")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        linhas.append(
            f"*{i}.* {e.get('subject')}{tag_str}\n"
            f"   👤 De: `{e.get('from')[:35]}`\n"
            f"   🆔 ID: `/email ler {e.get('id')}`\n"
        )

    linhas.append("💡 _Para ver o resumo completo do dia, use:_ `/email briefing`")
    await update.effective_message.reply_text("\n".join(linhas), parse_mode="Markdown")
