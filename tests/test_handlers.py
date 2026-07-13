"""
Testes de validacao dos handlers (bot/handlers/).
Testa comandos, utilidades de texto e logica dos handlers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.chat import _split_text, send_long_message
from bot.handlers.tools import _get_text, _LANGUAGES


class TestSplitText:
    """Testes para a funcao de divisao de texto longo."""

    def test_short_text_no_split(self):
        """Texto curto nao deve ser dividido."""
        result = _split_text("Hello World", 4096)
        assert len(result) == 1
        assert result[0] == "Hello World"

    def test_exact_limit(self):
        """Texto no limite exato nao deve ser dividido."""
        text = "a" * 4096
        result = _split_text(text, 4096)
        assert len(result) == 1

    def test_long_text_splits(self):
        """Texto longo deve ser dividido em chunks."""
        text = "Palavra " * 1000  # ~8000 caracteres
        result = _split_text(text, 100)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 100

    def test_split_on_newline(self):
        """Deve preferir dividir em quebras de linha."""
        text = "Linha 1\n" * 50 + "Linha final"
        result = _split_text(text, 50)
        assert len(result) > 1
        # Chunks devem terminar em linhas completas quando possivel

    def test_split_on_space(self):
        """Quando nao ha newline, deve dividir no espaco."""
        text = "palavra " * 20
        result = _split_text(text, 50)
        assert len(result) > 1
        # Nenhum chunk deve cortar uma palavra no meio
        for chunk in result:
            assert not chunk.startswith(" ")

    def test_empty_text(self):
        """Texto vazio retorna lista vazia."""
        result = _split_text("", 100)
        assert result == []

    def test_no_spaces_forces_hard_split(self):
        """Texto sem espacos forca divisao no limite."""
        text = "a" * 200
        result = _split_text(text, 100)
        assert len(result) == 2
        assert len(result[0]) == 100
        assert len(result[1]) == 100


class TestGetText:
    """Testes para a funcao utilitaria _get_text."""

    def test_get_text_from_args(self):
        """Deve retornar texto dos argumentos do comando."""
        update = MagicMock()
        context = MagicMock()
        context.args = ["ola", "mundo"]

        result = _get_text(update, context)
        assert result == "ola mundo"

    def test_get_text_from_reply(self):
        """Deve retornar texto da mensagem respondida."""
        update = MagicMock()
        update.message.reply_to_message.text = "Texto da resposta"
        context = MagicMock()
        context.args = []

        result = _get_text(update, context)
        assert result == "Texto da resposta"

    def test_get_text_none(self):
        """Deve retornar None quando nao ha texto."""
        update = MagicMock()
        update.message.reply_to_message = None
        context = MagicMock()
        context.args = []

        result = _get_text(update, context)
        assert result is None

    def test_get_text_args_priority(self):
        """Args devem ter prioridade sobre reply."""
        update = MagicMock()
        update.message.reply_to_message.text = "Texto reply"
        context = MagicMock()
        context.args = ["Texto", "args"]

        result = _get_text(update, context)
        assert result == "Texto args"


class TestLanguages:
    """Testes para o mapeamento de idiomas."""

    def test_languages_has_common_languages(self):
        """Verifica que idiomas comuns estao mapeados."""
        assert "en" in _LANGUAGES
        assert "es" in _LANGUAGES
        assert "fr" in _LANGUAGES
        assert "pt" in _LANGUAGES
        assert "de" in _LANGUAGES
        assert "ja" in _LANGUAGES

    def test_languages_values_are_portuguese(self):
        """Verifica que os nomes dos idiomas estao em portugues."""
        assert _LANGUAGES["en"] == "ingles" or _LANGUAGES["en"] == u"ingl\u00eas"
        assert _LANGUAGES["es"] == "espanhol"
        assert _LANGUAGES["fr"] == "frances" or _LANGUAGES["fr"] == u"franc\u00eas"

    def test_languages_count(self):
        """Verifica que ha pelo menos 10 idiomas suportados."""
        assert len(_LANGUAGES) >= 10


class TestHandlerMessages:
    """Testes para mensagens dos handlers."""

    def test_welcome_message_contains_bot_name(self):
        """Verifica que a mensagem de boas-vindas contem o nome do bot."""
        from bot.handlers.start import WELCOME_MESSAGE
        assert "ALFREDO" in WELCOME_MESSAGE

    def test_welcome_message_contains_commands(self):
        """Verifica que a mensagem de boas-vindas lista os comandos."""
        from bot.handlers.start import WELCOME_MESSAGE
        assert "/resumir" in WELCOME_MESSAGE
        assert "/traduzir" in WELCOME_MESSAGE
        assert "/codigo" in WELCOME_MESSAGE
        assert "/linkedin" in WELCOME_MESSAGE
        assert "/lembrete" in WELCOME_MESSAGE

    def test_help_message_contains_all_commands(self):
        """Verifica que o help lista todos os comandos."""
        from bot.handlers.start import HELP_MESSAGE
        commands = ["/resumir", "/traduzir", "/codigo", "/linkedin", "/lembrete",
                    "/nova", "/status", "/help"]
        for cmd in commands:
            assert cmd in HELP_MESSAGE, f"Comando {cmd} ausente no help"

    def test_help_message_has_examples(self):
        """Verifica que o help contem dica de uso."""
        from bot.handlers.start import HELP_MESSAGE
        assert "Dica" in HELP_MESSAGE or "dica" in HELP_MESSAGE.lower()


class TestMainImports:
    """Testes para verificar que todos os modulos importam corretamente."""

    def test_import_config(self):
        """Testa import do modulo config."""
        from bot.config import (
            TELEGRAM_BOT_TOKEN, GROQ_API_KEY, GROQ_MODEL,
            BOT_NAME, DB_PATH, MAX_HISTORY_MESSAGES, MAX_MESSAGE_LENGTH,
        )

    def test_import_database(self):
        """Testa import do modulo database."""
        from bot.database.db import Database

    def test_import_groq_service(self):
        """Testa import do servico Groq."""
        from bot.services.groq_service import GroqService

    def test_import_handlers(self):
        """Testa import de todos os handlers."""
        from bot.handlers.start import start_command, help_command
        from bot.handlers.chat import handle_text, handle_photo
        from bot.handlers.settings import nova_command, status_command
        from bot.handlers.tools import (
            resumir_command, traduzir_command,
            codigo_command, lembrete_command,
            linkedin_command,
        )

    def test_import_main(self):
        """Testa import do main."""
        from bot.main import main
