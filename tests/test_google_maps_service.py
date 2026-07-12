"""
Testes de validação do serviço Google Maps (bot/services/google_maps_service.py).
Testa inicialização, geocodificação, busca de locais, rotas e matriz de distância usando mocks do httpx.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.services.google_maps_service import GoogleMapsService


class TestGoogleMapsServiceInit:
    """Testes de inicialização do serviço."""

    def test_service_creation(self):
        """Verifica que o serviço inicializa com a chave de API fornecida."""
        service = GoogleMapsService(api_key="test_key")
        assert service.api_key == "test_key"


class TestGoogleMapsGeocode:
    """Testes para o método geocode."""

    @pytest.mark.asyncio
    async def test_geocode_no_api_key(self):
        """Verifica se retorna None quando não há API Key configurada."""
        service = GoogleMapsService(api_key="")
        result = await service.geocode("Praça da Sé")
        assert result is None

    @pytest.mark.asyncio
    async def test_geocode_success(self):
        """Testa geocodificação com sucesso."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "OK",
            "results": [{
                "geometry": {
                    "location": {"lat": -23.55052, "lng": -46.633308}
                },
                "formatted_address": "Praça da Sé, São Paulo - SP, Brasil"
            }]
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client) as mock_async_client:
            result = await service.geocode("Praça da Sé")
            assert result is not None
            assert result["lat"] == -23.55052
            assert result["lng"] == -46.633308
            assert result["formatted_address"] == "Praça da Sé, São Paulo - SP, Brasil"
            mock_async_client.assert_called_once()
            mock_client.get.assert_called_once_with(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": "Praça da Sé", "key": "mock_key", "language": "pt-BR"}
            )

    @pytest.mark.asyncio
    async def test_geocode_zero_results(self):
        """Testa geocodificação sem resultados encontrados (status diferente de OK)."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "ZERO_RESULTS",
            "results": []
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.geocode("Lugar Inexistente")
            assert result is None

    @pytest.mark.asyncio
    async def test_geocode_http_error(self):
        """Testa falha de conexão HTTP ou status de erro."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.geocode("Qualquer endereço")
            assert result is None

    @pytest.mark.asyncio
    async def test_geocode_exception(self):
        """Testa tratamento de exceção genérica no geocode."""
        service = GoogleMapsService(api_key="mock_key")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Erro de Rede"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.geocode("Endereço")
            assert result is None


class TestGoogleMapsSearchPlaces:
    """Testes para o método search_places."""

    @pytest.mark.asyncio
    async def test_search_places_no_api_key(self):
        """Verifica se retorna lista vazia sem API key."""
        service = GoogleMapsService(api_key="")
        result = await service.search_places("restaurante")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_places_success_no_location(self):
        """Testa busca de locais com sucesso sem coordenadas de referência."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "places": [
                {
                    "displayName": {"text": "Restaurante A"},
                    "formattedAddress": "Rua A, 123",
                    "rating": 4.5,
                    "userRatingCount": 120,
                    "location": {"latitude": -23.5, "longitude": -46.6}
                },
                {
                    "displayName": {"text": "Restaurante B"},
                    "formattedAddress": "Rua B, 456",
                    "rating": 4.0,
                    "userRatingCount": 80,
                    "location": {"latitude": -23.6, "longitude": -46.7}
                }
            ]
        })

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client) as mock_async_client:
            result = await service.search_places("restaurante")
            assert len(result) == 2
            assert result[0]["name"] == "Restaurante A"
            assert result[0]["rating"] == 4.5
            assert result[0]["latitude"] == -23.5
            assert result[1]["name"] == "Restaurante B"
            mock_async_client.assert_called_once()
            mock_client.post.assert_called_once_with(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": "mock_key",
                    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.location"
                },
                json={"textQuery": "restaurante", "languageCode": "pt-BR"}
            )

    @pytest.mark.asyncio
    async def test_search_places_success_with_location(self):
        """Testa busca de locais com coordenadas de referência."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "places": [
                {
                    "displayName": {"text": "Café Central"},
                    "formattedAddress": "Rua Central, 1",
                    "rating": 4.8,
                    "userRatingCount": 200,
                    "location": {"latitude": -23.55, "longitude": -46.63}
                }
            ]
        })

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.search_places("café", lat=-23.55, lng=-46.63, radius=5000)
            assert len(result) == 1
            assert result[0]["name"] == "Café Central"
            mock_client.post.assert_called_once_with(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": "mock_key",
                    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.location"
                },
                json={
                    "textQuery": "café",
                    "languageCode": "pt-BR",
                    "locationBias": {
                        "circle": {
                            "center": {
                                "latitude": -23.55,
                                "longitude": -46.63
                            },
                            "radius": 5000.0
                        }
                    }
                }
            )

    @pytest.mark.asyncio
    async def test_search_places_zero_results(self):
        """Testa busca de locais retornando lista vazia."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "places": []
        })

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.search_places("lugar improbavel")
            assert result == []

    @pytest.mark.asyncio
    async def test_search_places_http_error(self):
        """Testa busca de locais retornando erro HTTP."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.search_places("lugar")
            assert result == []

    @pytest.mark.asyncio
    async def test_search_places_exception(self):
        """Testa busca de locais com exceção na rede."""
        service = GoogleMapsService(api_key="mock_key")

        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=Exception("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.search_places("lugar")
            assert result == []


class TestGoogleMapsGetDirections:
    """Testes para o método get_directions."""

    @pytest.mark.asyncio
    async def test_get_directions_no_api_key(self):
        """Verifica se retorna None sem API key."""
        service = GoogleMapsService(api_key="")
        result = await service.get_directions("Origem", "Destino")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_directions_success(self):
        """Testa obtenção de rotas com sucesso."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "OK",
            "routes": [{
                "legs": [{
                    "start_address": "Rua Inicial, 100",
                    "end_address": "Rua Final, 200",
                    "distance": {"text": "5,2 km"},
                    "duration": {"text": "12 min"},
                    "steps": [
                        {
                            "html_instructions": "Siga na direção <b>norte</b>",
                            "distance": {"text": "100 m"}
                        },
                        {
                            "html_instructions": "Vire à esquerda na <i>Rua Central</i>",
                            "distance": {"text": "5 km"}
                        }
                    ]
                }]
            }]
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_directions("Origem", "Destino", mode="driving")
            assert result is not None
            assert result["origin_address"] == "Rua Inicial, 100"
            assert result["destination_address"] == "Rua Final, 200"
            assert result["distance"] == "5,2 km"
            assert result["duration"] == "12 min"
            # As instruções devem vir limpas de HTML
            assert result["steps"][0] == "Siga na direção norte (100 m)"
            assert result["steps"][1] == "Vire à esquerda na Rua Central (5 km)"
            
            mock_client.get.assert_called_once_with(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": "Origem",
                    "destination": "Destino",
                    "mode": "driving",
                    "key": "mock_key",
                    "language": "pt-BR"
                }
            )

    @pytest.mark.asyncio
    async def test_get_directions_api_error(self):
        """Testa Directions API com status JSON diferente de OK."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "NOT_FOUND",
            "routes": []
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_directions("Origem", "Destino")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_directions_exception(self):
        """Testa get_directions tratando exceção."""
        service = GoogleMapsService(api_key="mock_key")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Erro de conexão"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_directions("Origem", "Destino")
            assert result is None


class TestGoogleMapsGetDistanceMatrix:
    """Testes para o método get_distance_matrix."""

    @pytest.mark.asyncio
    async def test_get_distance_matrix_no_api_key(self):
        """Verifica se retorna None sem API key."""
        service = GoogleMapsService(api_key="")
        result = await service.get_distance_matrix("Origem", "Destino")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_distance_matrix_success(self):
        """Testa cálculo de distância e duração com sucesso."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "OK",
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"text": "15,5 km"},
                    "duration": {"text": "25 min"},
                    "duration_in_traffic": {"text": "32 min"}
                }]
            }]
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_distance_matrix("Origem", "Destino")
            assert result is not None
            assert result["distance"] == "15,5 km"
            assert result["duration"] == "25 min"
            assert result["duration_in_traffic"] == "32 min"

            mock_client.get.assert_called_once_with(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params={
                    "origins": "Origem",
                    "destinations": "Destino",
                    "mode": "driving",
                    "departure_time": "now",
                    "key": "mock_key",
                    "language": "pt-BR"
                }
            )

    @pytest.mark.asyncio
    async def test_get_distance_matrix_no_traffic(self):
        """Testa cálculo sem tempo de trânsito retornado."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "OK",
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"text": "10 km"},
                    "duration": {"text": "15 min"}
                    # Sem duration_in_traffic
                }]
            }]
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_distance_matrix("Origem", "Destino")
            assert result is not None
            assert result["distance"] == "10 km"
            assert result["duration"] == "15 min"
            assert result["duration_in_traffic"] == "15 min" # Deve fazer o fallback

    @pytest.mark.asyncio
    async def test_get_distance_matrix_element_error(self):
        """Testa quando o status do elemento interno não é OK."""
        service = GoogleMapsService(api_key="mock_key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "status": "OK",
            "rows": [{
                "elements": [{
                    "status": "ZERO_RESULTS"
                }]
            }]
        })

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_distance_matrix("Origem", "Destino")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_distance_matrix_exception(self):
        """Testa get_distance_matrix tratando exceção de rede."""
        service = GoogleMapsService(api_key="mock_key")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Erro"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await service.get_distance_matrix("Origem", "Destino")
            assert result is None
