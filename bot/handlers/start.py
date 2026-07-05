"""
Handlers para os comandos /start e /help.
Mensagens de boas-vindas e guia de uso do bot.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import BOT_NAME


WELCOME_MESSAGE = f"""
👋 *Olá! Eu sou o {BOT_NAME}!*

Sou seu assistente pessoal inteligente, alimentado por IA de última geração.

🧠 *O que posso fazer por você:*

💬  Conversar sobre qualquer assunto
📷  Analisar imagens — _envie uma foto!_
📝  Resumir textos — `/resumir`
🌐  Traduzir textos — `/traduzir`
💻  Gerar código — `/codigo`
🔍  Pesquisar na internet — `/pesquisar`
🚀  Posts virais para o LinkedIn — `/linkedin`
📸  Posts otimizados para o Instagram — `/instagram`
⏰  Criar lembretes — `/lembrete`

⚙️ *Comandos úteis:*
• `/nova` — Iniciar nova conversa
• `/status` — Ver informações da sessão
• `/help` — Ver esta mensagem novamente

_Manda sua mensagem, estou pronto para ajudar!_ 🚀
"""

HELP_MESSAGE = f"""
📖 *Guia de Comandos — {BOT_NAME}*

*💬 Conversa:*
• Envie qualquer texto para conversar
• Envie uma 📷 foto para eu analisar
• `/nova` — Limpa histórico e inicia nova conversa

*🛠️ Ferramentas:*
• `/resumir <texto>` — Resume um texto longo
• `/traduzir <idioma> <texto>` — Traduz um texto
• `/codigo <descrição>` — Gera código
• `/linkedin <ideia>` — Cria um post viral para o LinkedIn
• `/instagram <ideia>` — Cria um post para o Instagram (ideias de foto + legenda)
• `/pesquisar <termo>` — Pesquisa na internet em tempo real
• `/lembrete <minutos> <mensagem>` — Cria lembrete

*⚙️ Sistema:*
• `/status` — Informações da sessão
• `/help` — Mostra esta ajuda

💡 *Dica:* Responda a uma mensagem com `/resumir` ou `/traduzir` para aplicar a ferramenta ao texto respondido!
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia mensagem de boas-vindas quando /start é chamado."""
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia o guia de comandos quando /help é chamado."""
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
