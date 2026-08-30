"""
Serviço de Comunicação do ALFREDO com o GENNIE BOT via Bridge REST API.
Permite ao ALFREDO consultar e-mails, briefings, leitura completa e preparação de rascunhos.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class GennieService:
    def __init__(
        self,
        api_url: Optional[str] = None,
        secret_key: Optional[str] = None,
        timeout: float = 15.0
    ):
        self.api_url = (api_url or os.environ.get("GENNIE_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.secret_key = secret_key or os.environ.get("GENNIE_BRIDGE_KEY", "gennie_alfredo_secret_token_2026")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "User-Agent": "BotAlfredo-BridgeClient/1.0"
        }

    async def verificar_saude(self) -> Dict[str, Any]:
        """Verifica se o Bridge Server da GENNIE está online."""
        url = f"{self.api_url}/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "erro", "codigo": resp.status_code, "msg": resp.text}
        except Exception as e:
            logger.warning(f"GENNIE Bridge offline ou inacessível em {url}: {e}")
            return {"status": "offline", "erro": str(e)}

    async def listar_emails(self, query: str = "in:inbox", max_results: int = 5) -> Dict[str, Any]:
        """Consulta a lista de e-mails recentes."""
        url = f"{self.api_url}/api/v1/emails/recentes"
        params = {"query": query, "max_results": max_results}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                if resp.status_code == 200:
                    return resp.json()
                return {"sucesso": False, "erro": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"Erro ao consultar listar_emails na GENNIE: {e}")
            return {"sucesso": False, "erro": str(e)}

    async def obter_briefing(self, query: str = "in:inbox is:unread", max_emails: int = 8, sintetizar: bool = True) -> Dict[str, Any]:
        """Obtém o briefing executivo em lote com síntese da IA."""
        url = f"{self.api_url}/api/v1/emails/briefing"
        params = {"query": query, "max_emails": max_emails, "sintetizar": str(sintetizar).lower()}
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                if resp.status_code == 200:
                    return resp.json()
                return {"sucesso": False, "erro": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"Erro ao obter briefing na GENNIE: {e}")
            return {"sucesso": False, "erro": str(e)}

    async def ler_email(self, msg_id: str) -> Dict[str, Any]:
        """Lê o conteúdo e lista os anexos de um e-mail específico."""
        url = f"{self.api_url}/api/v1/emails/ler"
        params = {"msg_id": msg_id}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                if resp.status_code == 200:
                    return resp.json()
                return {"sucesso": False, "erro": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"Erro ao ler e-mail {msg_id} na GENNIE: {e}")
            return {"sucesso": False, "erro": str(e)}

    async def preparar_rascunho(self, dest: str, assunto: str, corpo: str) -> Dict[str, Any]:
        """Solicita a preparação de um rascunho seguro (HITL)."""
        url = f"{self.api_url}/api/v1/emails/preparar"
        body = {"dest": dest, "assunto": assunto, "corpo": corpo}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=body, headers=self._headers())
                if resp.status_code == 200:
                    return resp.json()
                return {"sucesso": False, "erro": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.error(f"Erro ao preparar rascunho na GENNIE: {e}")
            return {"sucesso": False, "erro": str(e)}
