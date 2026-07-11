"""
Serviço de cotação de moedas em tempo real via Finexly API.
"""

import logging
import httpx

logger = logging.getLogger(__name__)


class FinexlyService:
    """Serviço de integração com a API da Finexly."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.finexly.com/v1"
        logger.info("Finexly Service inicializado com sucesso.")

    async def get_rates(self, base: str = "USD", symbols: str = "BRL,EUR") -> dict:
        """
        Busca as taxas de câmbio atuais via Finexly API e retorna no formato {"BRL": valor, "EUR": valor}.

        Args:
            base: A moeda de base (ex: "USD" - ignorado pois usamos os pares fixos).
            symbols: Moedas de destino (ex: "BRL,EUR" - ignorado pois usamos os pares fixos).

        Returns:
            Dicionário contendo {"BRL": taxa, "EUR": taxa} ou dicionário vazio em caso de erro.
        """
        if not self.api_key:
            logger.warning("Finexly API Key não configurada. Ignorando busca de cotações.")
            return {}

        url = f"{self.base_url}/convert"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"q": "USD_BRL,USD_EUR"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    rates = {}
                    if "USD_BRL" in data and isinstance(data["USD_BRL"], dict):
                        rates["BRL"] = data["USD_BRL"].get("rate")
                    if "USD_EUR" in data and isinstance(data["USD_EUR"], dict):
                        rates["EUR"] = data["USD_EUR"].get("rate")
                    
                    logger.info(f"Cotações mapeadas com sucesso da Finexly: {rates}")
                    return rates
                else:
                    logger.error(f"Erro na API Finexly: Status {response.status_code} - {response.text}")
                    return {}
        except Exception as e:
            logger.error(f"Erro ao buscar cotações da Finexly: {e}", exc_info=True)
            return {}
