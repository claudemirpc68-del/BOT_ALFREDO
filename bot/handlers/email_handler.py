"""
Handler do comando /email para o BOT ALFREDO.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.gennie_service import GennieService

logger = logging.getLogger(__name__)

async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    gennie: GennieService = context.bot_data.get("gennie")
    if not gennie:
        gennie = GennieService()

    args = context.args or []
    subcomando = args[0].lower() if args else ""

    if subcomando in ("briefing", "resumo", "hoje"):
        await update.effective_message.reply_text("⏳ _Consultando a GENNIE para compilar o briefing de e-mails..._", parse_mode="Markdown")
        res = await gennie.obter_briefing(max_emails=6)
        if not res.get("sucesso"):
            await update.effective_message.reply_text(f"❌ *Não foi possível obter o briefing:*\n`{res.get('erro')}`", parse_mode="Markdown")
            return
        sintese = res.get("sintese_executiva", "Nenhum resumo gerado.")
        await update.effective_message.reply_text(f"🧞 *Briefing de E-mails (via GENNIE)*\n\n{sintese}", parse_mode="Markdown")
        return

    if subcomando in ("ler", "ver") and len(args) > 1:
        msg_id = args[1].strip()
        await update.effective_message.reply_text(f"⏳ _Buscando e-mail `{msg_id}` com a GENNIE..._", parse_mode="Markdown")
        res = await gennie.ler_email(msg_id)
        if not res.get("sucesso"):
            await update.effective_message.reply_text(f"❌ *Erro:* `{res.get('erro')}`", parse_mode="Markdown")
            return
        em = res.get("email", {})
        corpo = em.get("body", "")[:2000]
        texto = f"📨 *De:* {em.get('from')}\n📌 *Assunto:* {em.get('subject')}\n📅 *Data:* {em.get('date')}\n\n📝 *Conteúdo:*\n{corpo}"
        await update.effective_message.reply_text(texto, parse_mode="Markdown")
        return

    # Listagem padrão
    query = "in:inbox is:unread" if subcomando in ("nao-lidos", "novos") else "in:inbox"
    await update.effective_message.reply_text("⏳ _Consultando a GENNIE..._", parse_mode="Markdown")
    res = await gennie.listar_emails(query=query, max_results=4)
    if not res.get("sucesso"):
        await update.effective_message.reply_text(f"⚠️ *A GENNIE não respondeu.*\nDetalhe: `{res.get('erro')}`", parse_mode="Markdown")
        return

    emails = res.get("emails", [])
    if not emails:
        await update.effective_message.reply_text("📬 *Nenhum e-mail recente na caixa de entrada.*", parse_mode="Markdown")
        return

    linhas = ["📬 *E-mails na Caixa de Entrada (via GENNIE):*\n"]
    for i, e in enumerate(emails, 1):
        linhas.append(f"*{i}.* {e.get('subject')}\n   👤 De: `{e.get('from')[:35]}`\n   🆔 `/email ler {e.get('id')}`\n")
    linhas.append("💡 _Para resumo completo use:_ `/email briefing`")
    await update.effective_message.reply_text("\n".join(linhas), parse_mode="Markdown")
