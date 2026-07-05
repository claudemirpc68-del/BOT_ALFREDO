import requests

class AlfredoSkillOlharDigitalAI:
    def __init__(self, tavily_api_key):
        self.api_key = tavily_api_key
        self.endpoint = "https://api.tavily.com/search"

    def executar(self, preferencias=None, max_results=10):
        payload = {
            "query": "site:olhardigital.com.br Inteligência Artificial",
            "max_results": max_results,
            "include_domains": ["olhardigital.com.br"],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        response = requests.post(self.endpoint, json=payload, headers=headers)

        if response.status_code == 200:
            resultados = response.json().get("results", [])

            if preferencias:
                filtrados = [
                    artigo for artigo in resultados
                    if any(pref.lower() in artigo["title"].lower() or pref.lower() in artigo.get("content", "").lower()
                           for pref in preferencias)
                ]
            else:
                filtrados = resultados

            return [
                {
                    "titulo": artigo["title"],
                    "link": artigo["url"],
                    "resumo": artigo.get("content", "")[:200] + "..."
                }
                for artigo in filtrados
            ]
        else:
            return {"erro": f"Falha na requisição: {response.status_code}"}
