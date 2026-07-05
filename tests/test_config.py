"""
Testes de validacao do modulo de configuracao (bot/config.py).
Verifica carregamento de variaveis de ambiente e constantes.
"""

import os
import pytest


class TestConfig:
    """Testes para o modulo de configuracao."""

    def test_env_file_exists(self):
        """Verifica que o arquivo .env existe."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".env"
        )
        assert os.path.exists(env_path), (
            "Arquivo .env nao encontrado. Copie .env.example para .env"
        )

    def test_env_example_exists(self):
        """Verifica que o arquivo .env.example existe."""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".env.example"
        )
        assert os.path.exists(env_path), "Arquivo .env.example nao encontrado"

    def test_telegram_token_configured(self):
        """Verifica que o token do Telegram esta configurado."""
        from bot.config import TELEGRAM_BOT_TOKEN
        assert TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN nao configurado"
        assert TELEGRAM_BOT_TOKEN != "seu_token_do_botfather_aqui", (
            "TELEGRAM_BOT_TOKEN ainda esta com o valor padrao"
        )

    def test_groq_api_key_configured(self):
        """Verifica que a chave do Groq esta configurada."""
        from bot.config import GROQ_API_KEY
        assert GROQ_API_KEY, "GROQ_API_KEY nao configurada"
        assert GROQ_API_KEY != "sua_chave_groq_aqui", (
            "GROQ_API_KEY ainda esta com o valor padrao"
        )

    def test_bot_name(self):
        """Verifica que o nome do bot esta definido."""
        from bot.config import BOT_NAME
        assert BOT_NAME == "ALFREDO"

    def test_groq_model(self):
        """Verifica que o modelo do Groq esta definido."""
        from bot.config import GROQ_MODEL
        assert GROQ_MODEL, "GROQ_MODEL nao definido"
        assert "llama" in GROQ_MODEL.lower() or "mixtral" in GROQ_MODEL.lower(), (
            f"Modelo '{GROQ_MODEL}' nao parece ser um modelo Groq esperado"
        )

    def test_constants_values(self):
        """Verifica que as constantes tem valores razoaveis."""
        from bot.config import (
            MAX_HISTORY_MESSAGES,
            MAX_MESSAGE_LENGTH,
            MAX_REMINDER_MINUTES,
            DB_PATH,
        )
        assert MAX_HISTORY_MESSAGES > 0, "MAX_HISTORY_MESSAGES deve ser > 0"
        assert MAX_MESSAGE_LENGTH == 4096, "Limite Telegram = 4096"
        assert MAX_REMINDER_MINUTES > 0, "MAX_REMINDER_MINUTES deve ser > 0"
        assert DB_PATH.endswith(".db"), "DB_PATH deve terminar com .db"
