"""
Configurações do Bot ALFREDO.
Carrega variáveis de ambiente e define constantes do sistema.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# --- Credenciais ---
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

# --- Configurações do Bot ---
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
if not GROQ_MODEL or not GROQ_MODEL.strip():
    GROQ_MODEL = "llama-3.3-70b-versatile"

BOT_NAME: str = os.getenv("BOT_NAME", "ALFREDO")
if not BOT_NAME or not BOT_NAME.strip():
    BOT_NAME = "ALFREDO"

# --- Constantes ---
MAX_HISTORY_MESSAGES: int = 20
MAX_MESSAGE_LENGTH: int = 4096  # Limite do Telegram por mensagem
MAX_REMINDER_MINUTES: int = 1440  # 24 horas

# --- Caminhos ---
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "alfredo.db")

# --- Validação de variáveis obrigatórias ---
_REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "GROQ_API_KEY": GROQ_API_KEY,
    "TAVILY_API_KEY": TAVILY_API_KEY,
}

_missing = [name for name, value in _REQUIRED_VARS.items() if not value]
if _missing:
    for var in _missing:
        print(f"[ERRO] Variavel de ambiente obrigatoria nao configurada: {var}")
    print("\n[DICA] Copie o arquivo .env.example para .env e preencha os valores:")
    print("   copy .env.example .env")
    sys.exit(1)
