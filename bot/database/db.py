"""
Banco de dados SQLite assíncrono para persistência de conversas.
Armazena usuários e histórico de mensagens.
"""

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Gerencia o banco de dados SQLite assíncrono do bot."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Conecta ao banco e cria tabelas se necessário."""
        # Garante que o diretório existe
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()
        logger.info(f"Banco de dados inicializado: {self.db_path}")

    async def _create_tables(self) -> None:
        """Cria as tabelas do sistema."""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                last_name   TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                role        TEXT NOT NULL CHECK(role IN ('user', 'model')),
                content     TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_user
            ON messages(user_id, created_at DESC);
        """)
        await self._db.commit()

    # ── Usuários ──────────────────────────────────────────────

    async def save_user(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        """Cria ou atualiza informações do usuário."""
        await self._db.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, last_active)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username    = COALESCE(excluded.username, username),
                first_name  = COALESCE(excluded.first_name, first_name),
                last_name   = COALESCE(excluded.last_name, last_name),
                last_active = CURRENT_TIMESTAMP
            """,
            (user_id, username, first_name, last_name),
        )
        await self._db.commit()

    # ── Mensagens ─────────────────────────────────────────────

    async def save_message(self, user_id: int, role: str, content: str) -> None:
        """Salva uma mensagem no histórico."""
        await self._db.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await self._db.commit()

    async def get_history(self, user_id: int, limit: int = 20) -> list[dict]:
        """
        Retorna o histórico de conversa do usuário.
        As mensagens mais recentes são retornadas na ordem cronológica.
        """
        cursor = await self._db.execute(
            """
            SELECT role, content
            FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        # Inverte para ordem cronológica (mais antiga primeiro)
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    async def clear_history(self, user_id: int) -> int:
        """Limpa o histórico de conversa. Retorna quantidade removida."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        count = row[0] if row else 0

        await self._db.execute(
            "DELETE FROM messages WHERE user_id = ?",
            (user_id,),
        )
        await self._db.commit()
        return count

    async def get_message_count(self, user_id: int) -> int:
        """Retorna a quantidade total de mensagens do usuário."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    # ── Lifecycle ─────────────────────────────────────────────

    async def close(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self._db:
            await self._db.close()
            logger.info("Banco de dados fechado.")
