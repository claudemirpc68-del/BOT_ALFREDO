import requests

class AlfredoSkillAutomacaoPlanilha:
    def __init__(self, webhook_url="https://adesao.docescakemanias.cloud/adesao"):
        self.webhook_url = webhook_url

    def executar(self, nome, cpf, plano, data_adesao, email):
        payload = {
            "nome": nome,
            "cpf": cpf,
            "plano": plano,
            "data_adesao": data_adesao,
            "email": email
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                return {"sucesso": True, "mensagem": response.text}
            else:
                return {"sucesso": False, "mensagem": response.text}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro de conexão com o servidor: {str(e)}"}
