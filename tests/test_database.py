"""
Testes de validacao do banco de dados (bot/database/db.py).
Testa operacoes CRUD com SQLite assincrono usando banco temporario.
"""

import os
import tempfile
import pytest

from bot.database.db import Database


@pytest.fixture
async def db():
    """Cria um banco de dados temporario para testes."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    database = Database(tmp.name)
    await database.initialize()
    yield database
    await database.close()
    os.unlink(tmp.name)


class TestDatabase:
    """Testes para operacoes do banco de dados."""

    @pytest.mark.asyncio
    async def test_initialize(self, db):
        """Verifica que o banco inicializa sem erros."""
        assert db._db is not None

    @pytest.mark.asyncio
    async def test_save_and_get_user(self, db):
        """Testa salvar e recuperar informacoes de usuario."""
        await db.save_user(12345, "testuser", "Test", "User")
        # Verifica que nao levanta excecao ao salvar novamente (upsert)
        await db.save_user(12345, "testuser_updated", "Test2", None)

    @pytest.mark.asyncio
    async def test_save_message(self, db):
        """Testa salvar mensagens no historico."""
        await db.save_user(100, "user1", "Nome", None)
        await db.save_message(100, "user", "Ola bot!")
        await db.save_message(100, "model", "Ola! Como posso ajudar?")

        history = await db.get_history(100)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Ola bot!"
        assert history[1]["role"] == "model"
        assert history[1]["content"] == "Ola! Como posso ajudar?"

    @pytest.mark.asyncio
    async def test_get_history_order(self, db):
        """Verifica que o historico retorna na ordem cronologica."""
        await db.save_user(200, "user2", "Nome2", None)
        await db.save_message(200, "user", "Mensagem 1")
        await db.save_message(200, "model", "Resposta 1")
        await db.save_message(200, "user", "Mensagem 2")
        await db.save_message(200, "model", "Resposta 2")

        history = await db.get_history(200)
        assert len(history) == 4
        assert history[0]["content"] == "Mensagem 1"
        assert history[-1]["content"] == "Resposta 2"

    @pytest.mark.asyncio
    async def test_get_history_limit(self, db):
        """Verifica que o limite de historico funciona."""
        await db.save_user(300, "user3", "Nome3", None)
        for i in range(10):
            await db.save_message(300, "user", f"Msg {i}")

        history = await db.get_history(300, limit=3)
        assert len(history) == 3
        # Deve retornar as 3 mais recentes
        assert history[-1]["content"] == "Msg 9"

    @pytest.mark.asyncio
    async def test_clear_history(self, db):
        """Testa limpeza do historico."""
        await db.save_user(400, "user4", "Nome4", None)
        await db.save_message(400, "user", "Msg A")
        await db.save_message(400, "model", "Resp A")
        await db.save_message(400, "user", "Msg B")

        count = await db.clear_history(400)
        assert count == 3

        history = await db.get_history(400)
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_clear_history_empty(self, db):
        """Testa limpeza quando nao ha historico."""
        count = await db.clear_history(999)
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_message_count(self, db):
        """Testa contagem de mensagens."""
        await db.save_user(500, "user5", "Nome5", None)
        assert await db.get_message_count(500) == 0

        await db.save_message(500, "user", "Msg 1")
        await db.save_message(500, "model", "Resp 1")
        assert await db.get_message_count(500) == 2

    @pytest.mark.asyncio
    async def test_user_isolation(self, db):
        """Verifica que historicos de usuarios diferentes sao isolados."""
        await db.save_user(601, "userA", "A", None)
        await db.save_user(602, "userB", "B", None)

        await db.save_message(601, "user", "Msg do A")
        await db.save_message(602, "user", "Msg do B")

        hist_a = await db.get_history(601)
        hist_b = await db.get_history(602)

        assert len(hist_a) == 1
        assert len(hist_b) == 1
        assert hist_a[0]["content"] == "Msg do A"
        assert hist_b[0]["content"] == "Msg do B"

    @pytest.mark.asyncio
    async def test_close_and_reopen(self, db):
        """Testa que dados persistem apos fechar e reabrir."""
        await db.save_user(700, "user7", "Nome7", None)
        await db.save_message(700, "user", "Dados persistentes")

        db_path = db.db_path
        await db.close()

        # Reabre
        db2 = Database(db_path)
        await db2.initialize()

        history = await db2.get_history(700)
        assert len(history) == 1
        assert history[0]["content"] == "Dados persistentes"

        await db2.close()
