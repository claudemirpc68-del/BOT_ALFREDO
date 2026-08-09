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
⏰  Criar lembretes — `/lembrete`

📁 *Downloads & Sistema:*
📁  Organizar Downloads — `/organizar`
📊  Relatório de espaço — `/relatorio`
👯  Remover duplicados — `/duplicados`
🧹  Limpar temporários — `/limpar`
🗑️  Esvaziar Lixeira — `/lixeira`
📜  Ver logs recentes — `/logs`

⚙️ *Comandos úteis:*
• `/nova` — Iniciar nova conversa
• `/status` — Ver informações da sessão
• `/help` — Ver esta mensagem novamente

_Manda sua mensagem, estou pronto para ajudar!_ 🚀
"""

HELP_MESSAGE = f"""
📖 *Guia de Comandos — {BOT_NAME}*

*💬 Conversa & IA:*
• Envie qualquer texto para conversar
• Envie uma 📷 foto para eu analisar
• `/nova` — Limpa histórico e inicia nova conversa
• `/resumir <texto>` — Resume um texto longo
• `/traduzir <idioma> <texto>` — Traduz um texto
• `/codigo <descrição>` — Gera código
• `/linkedin <ideia>` — Cria um post viral para o LinkedIn
• `/pesquisar <termo>` — Pesquisa na internet em tempo real
• `/lembrete <minutos> <mensagem>` — Cria lembrete

*📁 Automação de Downloads & Lixeira:*
• `/organizar` — Categoriza +40 extensões, apaga duplicados e temporários
• `/relatorio` — Mostra ocupação da pasta Downloads e espaço livre em C:
• `/duplicados` — Busca e apaga apenas arquivos duplicados
• `/limpar` — Limpa temporários (.tmp, .crdownload, etc.) antigos (>7 dias)
• `/lixeira` — Esvazia a Lixeira do Windows
• `/logs` — Exibe as últimas linhas do último log gerado

*⚙️ Sistema:*
• `/status` — Informações da sessão
• `/help` — Mostra esta ajuda
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia mensagem de boas-vindas quando /start é chamado."""
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia o guia de comandos quando /help é chamado."""
    await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
