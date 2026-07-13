"""
Testes de validação do serviço Groq (bot/services/groq_service.py).
Testa inicialização, formatação de erros e chamadas simuladas da API da Groq.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.groq_service import GroqService
from bot.prompts import PERSONA, build_prompt


class TestGroqServiceInit:
    """Testes de inicialização do serviço."""

    def test_service_creation(self):
        """Verifica que o serviço inicializa corretamente."""
        service = GroqService(api_key="test_key", model="llama3-70b-8192")
        assert service.model == "llama3-70b-8192"
        assert service.client is not None

    def test_service_default_model(self):
        """Verifica o modelo padrão."""
        service = GroqService(api_key="test_key")
        assert service.model == "llama-3.3-70b-versatile"

    def test_system_prompt_exists(self):
        """Verifica que o system prompt (PERSONA) está definido e contém informações chave."""
        assert PERSONA, "PERSONA não pode estar vazia"
        assert "ALFREDO" in PERSONA, "Nome do bot deve estar no prompt"
        assert len(PERSONA) > 100, "PERSONA muito curta"


class TestGroqErrorFormatting:
    """Testes para formatação de erros amigáveis."""

    def test_rate_limit_error(self):
        """Testa mensagem para erro de rate limit."""
        msg = GroqService._format_error(Exception("Rate limit exceeded for API"))
        assert "Limite" in msg or "limite" in msg

    def test_auth_error(self):
        """Testa mensagem para erro de autenticação."""
        msg = GroqService._format_error(Exception("Invalid API key or unauthorized access"))
        assert "autenticacao" in msg.lower() or "chave" in msg.lower()

    def test_generic_error(self):
        """Testa mensagem para erro genérico."""
        msg = GroqService._format_error(Exception("Internal server error"))
        assert "Erro" in msg

    def test_long_error_truncated(self):
        """Testa que erros longos são truncados."""
        long_error = "x" * 500
        msg = GroqService._format_error(Exception(long_error))
        assert len(msg) < 500


class TestGroqAPIIntegration:
    """Testes de integração com a API Groq (usando mocks)."""

    @pytest.mark.asyncio
    async def test_chat_returns_text(self):
        """Testa que chat retorna texto do modelo."""
        service = GroqService(api_key="test_key")

        # Configura Mock para o retorno do chat completion
        mock_choice = MagicMock()
        mock_choice.message.content = "Resposta do Llama"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ) as mock_create:
            result = await service.chat("Olá", [])
            assert result == "Resposta do Llama"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_history(self):
        """Testa que chat envia histórico corretamente."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = "Resposta com contexto"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ) as mock_create:
            history = [
                {"role": "user", "content": "Msg anterior"},
                {"role": "model", "content": "Resp anterior"},
            ]
            result = await service.chat("Nova msg", history)
            assert result == "Resposta com contexto"
            mock_create.assert_called_once()
            
            # Garante que mandou o prompt do sistema + histórico + nova mensagem
            called_messages = mock_create.call_args[1]["messages"]
            assert len(called_messages) == 4
            assert called_messages[0]["role"] == "system"
            assert called_messages[1]["role"] == "user"
            assert called_messages[2]["role"] == "assistant"
            assert called_messages[3]["role"] == "user"

    @pytest.mark.asyncio
    async def test_chat_handles_none_response(self):
        """Testa fallback quando resposta é None."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.chat("Olá", [])
            assert "consegui" in result.lower()

    @pytest.mark.asyncio
    async def test_chat_handles_exception(self):
        """Testa tratamento de exceção na API."""
        service = GroqService(api_key="test_key")

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, side_effect=Exception("API Error")
        ):
            result = await service.chat("Olá", [])
            assert "Erro" in result

    @pytest.mark.asyncio
    async def test_summarize(self):
        """Testa função de resumo."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = "Resumo do texto"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.summarize("Texto longo para resumir...")
            assert result == "Resumo do texto"

    @pytest.mark.asyncio
    async def test_translate(self):
        """Testa função de tradução."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = "Hello, how are you?"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.translate("Olá, como vai?", "inglês")
            assert result == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_generate_code(self):
        """Testa função de geração de código."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = "```python\ndef hello():\n    print('Hello')\n```"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.generate_code("função hello em Python")
            assert "python" in result or "def" in result

    @pytest.mark.asyncio
    async def test_generate_linkedin_post(self):
        """Testa função de geração de posts do LinkedIn."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = "Conteúdo viral sobre IA #InteligenciaArtificial"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.generate_linkedin_post("Impacto da IA no suporte")
            assert "InteligenciaArtificial" in result


    @pytest.mark.asyncio
    async def test_analyze_image(self):
        """Testa função de análise de imagem (Groq Vision)."""
        service = GroqService(api_key="test_key")

        mock_choice = MagicMock()
        mock_choice.message.content = "A imagem mostra um gato laranja."
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            service.client.chat.completions, "create",
            new_callable=AsyncMock, return_value=mock_response
        ) as mock_create:
            result = await service.analyze_image(
                b"\x89PNG\r\n", "image/png", "O que é isso?", []
            )
            assert "gato" in result
            mock_create.assert_called_once()
            called_args = mock_create.call_args[1]
            assert called_args["model"] == "meta-llama/llama-4-scout-17b-16e-instruct"
            assert isinstance(called_args["messages"][1]["content"], list)
