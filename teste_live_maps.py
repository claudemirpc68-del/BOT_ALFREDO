import asyncio
import os
import sys
import io
import json
from dotenv import load_dotenv
from bot.services.google_maps_service import GoogleMapsService

# Garante saída em UTF-8 no Windows para evitar UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY não encontrada no .env")
        return

    maps = GoogleMapsService(api_key=api_key)
    
    print("=" * 60)
    print("🗺️ TESTE LIVE: GOOGLE MAPS SERVICE (BOT ALFREDO)")
    print("=" * 60)

    # 1. TESTE DE GEOCODIFICAÇÃO (Endereço -> Coordenadas e CEP -> Coordenadas)
    print("\n--- 1. GEOCODIFICAÇÃO (Geocoding API) ---")
    enderecos_teste = [
        "Av. Paulista, 1578, São Paulo - SP",
        "01310-200" # CEP do MASP
    ]
    
    lat_ref, lng_ref = None, None
    for end in enderecos_teste:
        print(f"\n📍 Testando endereço: '{end}'")
        res = await maps.geocode(end)
        if res:
            print(f"  ✅ Endereço Formatado: {res['formatted_address']}")
            print(f"  ✅ Coordenadas: Latitude {res['lat']}, Longitude {res['lng']}")
            if not lat_ref:
                lat_ref, lng_ref = res['lat'], res['lng']
        else:
            print("  ❌ Falha na geocodificação.")

    # 2. TESTE DE ROTAS (Directions API)
    print("\n--- 2. ROTAS E DISTÂNCIAS (Directions API) ---")
    origem = "Av. Paulista, 1578, São Paulo - SP"
    destino = "Parque Ibirapuera, São Paulo - SP"
    print(f"🚗 Calculando rota de '{origem}' até '{destino}'...")
    
    rota = await maps.get_directions(origem, destino, mode="driving")
    if rota:
        print(f"  ✅ Origem Confirmada: {rota['origin_address']}")
        print(f"  ✅ Destino Confirmado: {rota['destination_address']}")
        print(f"  📏 Distância Total: {rota['distance']}")
        print(f"  ⏱️ Tempo Estimado: {rota['duration']}")
        print("  📍 Primeiros passos do trajeto:")
        for idx, passo in enumerate(rota['steps'][:4], 1):
            print(f"     {idx}. {passo}")
    else:
        print("  ❌ Falha ao obter rotas.")

    # 3. TESTE DE PONTOS DE INTERESSE (Places API)
    print("\n--- 3. PONTOS DE INTERESSE (Places API - Novos Locais Próximos) ---")
    categorias_teste = ["farmácia", "restaurante", "banco"]
    
    for cat in categorias_teste:
        print(f"\n🔎 Buscando '{cat}' num raio de 2km próximo ao MASP (Paulista)...")
        locais = await maps.search_places(query=cat, lat=lat_ref, lng=lng_ref, radius=2000)
        if locais:
            print(f"  ✅ Encontrados {len(locais)} locais mais próximos:")
            for idx, loc in enumerate(locais[:3], 1):
                rating_str = f"⭐ {loc['rating']}" if loc['rating'] != "N/A" else "Sem avaliação"
                dist = f"({loc['distance_str']})" if loc.get('distance_str') else ""
                print(f"     {idx}. {loc['name']} {dist}")
                print(f"        Endereço: {loc['address']} | {rating_str}")
        else:
            print(f"  ⚠️ Nenhum local encontrado para '{cat}'.")

    print("\n" + "=" * 60)
    print("🎉 TESTES CONCLUÍDOS COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
