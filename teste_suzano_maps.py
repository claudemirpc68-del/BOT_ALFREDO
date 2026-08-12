import asyncio
import os
import sys
import io
from dotenv import load_dotenv
from bot.services.google_maps_service import GoogleMapsService

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ API Key não encontrada.")
        return

    maps = GoogleMapsService(api_key=api_key)
    cep_user = "08625-572"
    
    print("=" * 60)
    print(f"🗺️ TESTE GOOGLE MAPS PARA A LOCALIZAÇÃO DO USUÁRIO ({cep_user})")
    print("=" * 60)

    # 1. GEOCODIFICAÇÃO DO CEP DO USUÁRIO
    print("\n--- 1. GEOCODIFICAÇÃO E COORDENADAS ---")
    print(f"📍 Geocodificando CEP '{cep_user}'...")
    res = await maps.geocode(cep_user)
    
    if res:
        print(f"  ✅ Endereço Reconhecido: {res['formatted_address']}")
        print(f"  ✅ Coordenadas Exatas: Lat {res['lat']}, Lng {res['lng']}")
        lat, lng = res['lat'], res['lng']
    else:
        print("  ❌ Não foi possível resolver as coordenadas do CEP.")
        return

    # 2. ROTAS A PARTIR DO CEP DO USUÁRIO
    print("\n--- 2. CÁLCULO DE ROTAS (Navegação) ---")
    destinos = [
        "Estação CPTM Suzano, Suzano - SP",
        "Suzano Shopping, Suzano - SP"
    ]
    
    for dest in destinos:
        print(f"\n🚗 Rota de '{res['formatted_address']}' para '{dest}':")
        rota = await maps.get_directions(origin=f"{lat},{lng}", destination=dest, mode="driving")
        if rota:
            print(f"  📏 Distância: {rota['distance']}")
            print(f"  ⏱️ Tempo Estimado: {rota['duration']}")
            print("  📍 Primeiros passos:")
            for idx, p in enumerate(rota['steps'][:3], 1):
                print(f"     {idx}. {p}")
        else:
            print("  ❌ Rota não encontrada.")

    # 3. LOCAIS PRÓXIMOS AO CEP 08625-572 (Raio de 3km a 5km)
    print("\n--- 3. PONTOS DE INTERESSE PRÓXIMOS ---")
    buscas = ["supermercado", "farmácia", "banco", "restaurante"]
    
    for b in buscas:
        print(f"\n🔎 Buscando '{b}' mais próximo do CEP {cep_user}...")
        locais = await maps.search_places(query=b, lat=lat, lng=lng, radius=5000)
        if locais:
            print(f"  ✅ {len(locais)} estabelecimentos mais próximos:")
            for idx, loc in enumerate(locais[:3], 1):
                dist = f"({loc['distance_str']})" if loc.get('distance_str') else ""
                rating = f"⭐ {loc['rating']}" if loc['rating'] != "N/A" else "Sem avaliação"
                print(f"     {idx}. {loc['name']} {dist}")
                print(f"        Endereço: {loc['address']} | {rating}")
        else:
            print(f"  ⚠️ Nenhum local encontrado para '{b}'.")

    print("\n" + "=" * 60)
    print("🎉 TESTE PARA SUZANO (08625-572) CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
