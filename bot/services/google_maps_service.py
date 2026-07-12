"""
Serviço de integração assíncrona com a API do Google Maps.
Oferece suporte a Geocoding, Directions, Places e Distance Matrix.
"""

import logging
import httpx

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Classe de integração com as APIs do Google Maps."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("GoogleMapsService inicializado com sucesso.")

    async def geocode(self, address: str) -> dict | None:
        """
        Converte um endereço em formato texto em coordenadas geográficas (lat, lng).
        
        Args:
            address: Endereço a ser geocodificado.
            
        Returns:
            Dicionário contendo lat, lng e formatted_address ou None em caso de falha.
        """
        if not self.api_key:
            logger.warning("Google Maps API Key não configurada.")
            return None

        # Limpeza e normalização do endereço para CEPs brasileiros
        import re
        address_clean = address.strip()
        
        # Remove prefixo "CEP", "EP", etc. no início de forma case-insensitive
        address_clean = re.sub(r'(?i)^\b(cep|ep)\b:?', '', address_clean).strip()
        
        # Se começar com um CEP (5 ou 8 dígitos, com ou sem hífen), move o CEP para o final do endereço
        match = re.match(r'^(\d{5}-?\d{3})\s+(.+)$', address_clean)
        if match:
            cep = match.group(1)
            resto = match.group(2)
            address_clean = f"{resto}, {cep}"
        
        # Se for um CEP puro (5 ou 8 dígitos) -> adiciona ", Brasil" e formata se necessário
        if re.match(r'^\d{8}$', address_clean):
            address_clean = f"{address_clean[:5]}-{address_clean[5:]}, Brasil"
        elif re.match(r'^\d{5}-\d{3}$', address_clean):
            address_clean = f"{address_clean}, Brasil"

        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address_clean,
            "key": self.api_key,
            "language": "pt-BR"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK" and data.get("results"):
                        result = data["results"][0]
                        location = result["geometry"]["location"]
                        return {
                            "lat": location["lat"],
                            "lng": location["lng"],
                            "formatted_address": result.get("formatted_address")
                        }
                    else:
                        logger.warning(f"Geocoding retornou status: {data.get('status')}")
                        return None
                else:
                    logger.error(f"Erro na Geocoding API: Status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Exceção no geocode: {e}", exc_info=True)
            return None

    async def search_places(self, query: str, lat: float = None, lng: float = None, radius: int = 8000) -> list:
        """
        Busca estabelecimentos ou pontos de interesse usando a nova Places API (New) Text Search.
        
        Args:
            query: Termo de busca (ex: "casa de câmbio").
            lat: Latitude de referência.
            lng: Longitude de referência.
            radius: Raio de busca em metros (padrão: 8km).
            
        Returns:
            Lista de estabelecimentos encontrados.
        """
        if not self.api_key:
            logger.warning("Google Maps API Key não configurada.")
            return []

        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.location"
        }

        body = {
            "textQuery": query,
            "languageCode": "pt-BR"
        }

        if lat is not None and lng is not None:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "radius": float(radius)
                }
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=body)
                if response.status_code == 200:
                    data = response.json()
                    places = []
                    for item in data.get("places", [])[:5]: # Top 5 locais
                        places.append({
                            "name": item.get("displayName", {}).get("text"),
                            "address": item.get("formattedAddress"),
                            "rating": item.get("rating", "N/A"),
                            "user_ratings_total": item.get("userRatingCount", 0),
                            "latitude": item.get("location", {}).get("latitude"),
                            "longitude": item.get("location", {}).get("longitude")
                        })
                    return places
                else:
                    logger.error(f"Erro na Places API (New): Status {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Exceção no search_places: {e}", exc_info=True)
            return []

    async def get_directions(self, origin: str, destination: str, mode: str = "driving") -> dict | None:
        """
        Obtém a rota detalhada entre dois pontos via Directions API.
        
        Args:
            origin: Localização de partida.
            destination: Localização de destino.
            mode: Modo de transporte (driving, walking, bicycling, transit).
            
        Returns:
            Dicionário com informações do trajeto ou None em caso de falha.
        """
        if not self.api_key:
            logger.warning("Google Maps API Key não configurada.")
            return None

        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key,
            "language": "pt-BR"
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK" and data.get("routes"):
                        route = data["routes"][0]
                        leg = route["legs"][0]
                        
                        steps = []
                        for step in leg.get("steps", [])[:10]: # Top 10 passos para não estourar tokens
                            import re
                            html_inst = step.get("html_instructions", "")
                            # Remove tags HTML básicas retornadas pela API do Google
                            clean_inst = re.sub(r'<[^>]+>', '', html_inst)
                            steps.append(f"{clean_inst} ({step['distance']['text']})")

                        return {
                            "origin_address": leg.get("start_address"),
                            "destination_address": leg.get("end_address"),
                            "distance": leg["distance"]["text"],
                            "duration": leg["duration"]["text"],
                            "steps": steps
                        }
                    else:
                        logger.warning(f"Directions API retornou status: {data.get('status')}")
                        return None
                else:
                    logger.error(f"Erro na Directions API: Status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Exceção no get_directions: {e}", exc_info=True)
            return None

    async def get_distance_matrix(self, origin: str, destination: str, mode: str = "driving") -> dict | None:
        """
        Estima a distância e o tempo de viagem (considerando trânsito se possível) via Distance Matrix API.
        
        Args:
            origin: Ponto de partida.
            destination: Ponto de destino.
            mode: Modo de transporte.
            
        Returns:
            Dicionário com a distância e tempo estimado, ou None.
        """
        if not self.api_key:
            logger.warning("Google Maps API Key não configurada.")
            return None

        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "mode": mode,
            "departure_time": "now", # Habilita cálculo de trânsito em tempo real
            "key": self.api_key,
            "language": "pt-BR"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK" and data.get("rows"):
                        row = data["rows"][0]
                        element = row["elements"][0]
                        
                        if element.get("status") == "OK":
                            duration_in_traffic = element.get("duration_in_traffic", {}).get("text")
                            return {
                                "distance": element["distance"]["text"],
                                "duration": element["duration"]["text"],
                                "duration_in_traffic": duration_in_traffic or element["duration"]["text"]
                            }
                        else:
                            logger.warning(f"Distance Matrix elemento retornou status: {element.get('status')}")
                            return None
                    else:
                        logger.warning(f"Distance Matrix API retornou status: {data.get('status')}")
                        return None
                else:
                    logger.error(f"Erro na Distance Matrix API: Status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Exceção no get_distance_matrix: {e}", exc_info=True)
            return None
