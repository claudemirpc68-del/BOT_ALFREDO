import os
import sys
from dotenv import load_dotenv

# Garante que o diretório atual está no path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Carrega o .env
load_dotenv()

from skills.alfredo_olhardigital import AlfredoSkillOlharDigitalAI
from actions.actions import ActionBuscarOlharDigitalAI
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

def validar_tudo():
    print("====================================================")
    print("   SCRIPT DE VALIDAÇÃO: SKILL & RASA CUSTOM ACTION   ")
    print("====================================================")
    
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("[ERRO] Chave TAVILY_API_KEY não encontrada no arquivo .env.")
        sys.exit(1)
        
    print("[OK] 1. Chave TAVILY_API_KEY encontrada no ambiente.")
    
    # 2. Testa a Skill diretamente
    print("\n--- [Teste 1/2] Executando Skill OlharDigitalAI ---")
    try:
        skill = AlfredoSkillOlharDigitalAI(tavily_api_key=tavily_key)
        resultados = skill.executar(preferencias=["IA generativa"])
        
        if isinstance(resultados, dict) and "erro" in resultados:
            print(f"[ERRO] Falha ao executar a skill: {resultados['erro']}")
            sys.exit(1)
            
        print(f"[OK] Skill executada com sucesso! Encontrados {len(resultados)} artigos.")
        for i, art in enumerate(resultados[:3], 1):
            print(f"   [{i}] {art['titulo']}")
            print(f"       Link: {art['link']}")
    except Exception as e:
        print(f"[ERRO] Inesperado ao testar a skill: {e}")
        sys.exit(1)
        
    # 3. Testa a Custom Action do Rasa de forma offline
    print("\n--- [Teste 2/2] Executando Rasa Custom Action (offline) ---")
    try:
        action = ActionBuscarOlharDigitalAI()
        print(f"[OK] Action instanciada. Nome da Action: '{action.name()}'")
        
        # Mocks do Rasa
        dispatcher = CollectingDispatcher()
        # Inicializa um tracker com o slot de preferências configurado
        tracker = Tracker(
            sender_id="user_teste",
            slots={"preferencias": "IA generativa"},
            latest_message={},
            events=[],
            paused=False,
            followup_action=None,
            active_loop={},
            latest_action_name=None
        )
        domain = {}
        
        print("Executando o método run() da Custom Action...")
        events = action.run(dispatcher, tracker, domain)
        
        print(f"[OK] Execução da Action concluída. Eventos retornados: {events}")
        print("\nMensagens enviadas pelo Dispatcher:")
        for msg in dispatcher.messages:
            text = msg.get("text")
            print(f"   Rasa diz: {text}")
            
    except Exception as e:
        print(f"[ERRO] Falha ao testar a Custom Action: {e}")
        sys.exit(1)
        
    print("\n====================================================")
    print("[OK] VALIDAÇÃO CONCLUÍDA COM SUCESSO! TUDO OPERACIONAL!")
    print("====================================================")

if __name__ == "__main__":
    validar_tudo()
