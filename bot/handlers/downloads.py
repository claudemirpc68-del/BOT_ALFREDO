"""
Handlers para gerenciamento da pasta Downloads e Lixeira do Windows no BOT_ALFREDO.
"""

import os
import sys
import subprocess
import ctypes
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

AGENTE_PATH = Path(r"C:\Users\FAMÍLIA\Desktop\GERENCIA_DOWLOADS\agente_downloads.py")


def executar_agente(args: list[str]) -> str:
    """Executa o script agente_downloads.py e captura a saída."""
    if not AGENTE_PATH.exists():
        return f"Erro: Script do agente não encontrado em {AGENTE_PATH}"

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        resultado = subprocess.run(
            [sys.executable, str(AGENTE_PATH)] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            cwd=str(AGENTE_PATH.parent),
            env=env,
        )
        saida = (resultado.stdout or "") + (resultado.stderr or "")
        return saida.strip() or "(Sem alterações/sem saída)"
    except subprocess.TimeoutExpired:
        return "Timeout: O script demorou muito para responder."
    except Exception as erro:
        return f"Erro ao executar o agente: {erro}"


async def organizar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Organiza a pasta Downloads (+40 extensões), remove duplicados e limpa temporários."""
    msg = await update.message.reply_text("📁 Organizando pasta Downloads, removendo duplicados e limpando temporários...")
    saida = executar_agente(["once"])
    texto_final = f"✅ *Organização Concluída!*\n\n```\n{saida[:3500]}\n```"
    await msg.edit_text(texto_final, parse_mode="Markdown")


async def relatorio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera o relatório de espaço consumido e arquivos na pasta Downloads."""
    msg = await update.message.reply_text("📊 Gerando relatório da pasta Downloads...")
    saida = executar_agente(["--relatorio"])
    texto_final = f"📊 *Relatório da Pasta Downloads*\n\n```\n{saida[:3500]}\n```"
    await msg.edit_text(texto_final, parse_mode="Markdown")


async def duplicados_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca e apaga arquivos duplicados na pasta Downloads."""
    msg = await update.message.reply_text("👯 Buscando e removendo arquivos duplicados...")
    saida = executar_agente(["--duplicados"])
    texto_final = f"👯 *Remoção de Duplicados Concluída*\n\n```\n{saida[:3500]}\n```"
    await msg.edit_text(texto_final, parse_mode="Markdown")


async def limpar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Limpa arquivos temporários (.tmp, .crdownload, etc.) antigos."""
    msg = await update.message.reply_text("🧹 Limpando arquivos temporários com mais de 7 dias...")
    saida = executar_agente(["--limpar"])
    texto_final = f"🧹 *Limpeza de Temporários Concluída*\n\n```\n{saida[:3500]}\n```"
    await msg.edit_text(texto_final, parse_mode="Markdown")


async def lixeira_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Esvazia a Lixeira do Windows."""
    msg = await update.message.reply_text("🗑️ Esvaziando a Lixeira do Windows...")
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
        await msg.edit_text("🗑️ *Lixeira do Windows esvaziada com sucesso!*", parse_mode="Markdown")
    except Exception as erro:
        await msg.edit_text(f"❌ Erro ao esvaziar a Lixeira: `{erro}`", parse_mode="Markdown")


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe o último arquivo de log gerado pelo agente."""
    log_dir = Path(os.path.expanduser("~")) / "Downloads" / "Logs_Agente"
    logs = sorted(log_dir.glob("agente_*.log")) if log_dir.exists() else []
    if not logs:
        await update.message.reply_text("📜 Nenhum log encontrado na pasta `Downloads/Logs_Agente`.", parse_mode="Markdown")
        return

    ultimo = logs[-1]
    conteudo = ultimo.read_text(encoding="utf-8", errors="ignore")
    linhas = conteudo.strip().splitlines()
    resumo = "\n".join(linhas[-25:])
    await update.message.reply_text(
        f"📜 *Último Log (`{ultimo.name}`)*:\n\n```\n{resumo[:3500] or '(log vazio)'}\n```",
        parse_mode="Markdown",
    )
