"""
Testes de unidade para o validador EARS (scripts/valida_ears.py).
Valida que as regras sintáticas identificam corretamente os requisitos certos e errados,
e que o arquivo docs/prd.md de produção está em total conformidade.
"""

import pytest
from scripts.valida_ears import validar_texto_requisito, validar_prd

class TestValidadorEARS:
    """Testa a lógica de validação sintática do formato EARS em português."""

    @pytest.mark.parametrize("tipo,texto", [
        ("UR", "O sistema deve executar continuamente em segundo plano."),
        ("UR", "O bot ALFREDO deve responder as mensagens de texto em portugues."),
        ("UR", "As credenciais devem ser carregadas a partir de um arquivo .env."),
        ("ER", "Quando o usuario enviar uma foto, o sistema deve descrever a imagem."),
        ("ER", "Ao receber um comando /nova, o bot deve resetar o historico do chat."),
        ("ER", "Após o lembrete disparar, o bot deve enviar a mensagem de aviso."),
        ("SR", "Enquanto a sessao estiver ativa, o sistema deve manter o historico no prompt."),
        ("SR", "Durante a execucao, o bot deve salvar logs de auditoria."),
        ("UB", "Se a chave do Tavily estiver ausente, o sistema deve desativar a busca."),
        ("UB", "Caso o tempo seja invalido, o bot deve avisar o usuario."),
    ])
    def test_requisitos_validos(self, tipo, texto):
        """Verifica se requisitos válidos passam pela verificação sintática."""
        sucesso, erro = validar_texto_requisito(tipo, texto)
        assert sucesso is True, f"Requisito valido '{texto}' falhou: {erro}"
        assert erro is None

    @pytest.mark.parametrize("tipo,texto,erro_esperado", [
        ("UR", "O sistema executará em segundo plano.", "deve conter um verbo de obrigação"),
        ("UR", "Quando o sistema iniciar, ele deve carregar as configs.", "nao deve iniciar com conectivo condicional/temporal"),
        ("UR", "Se o bot rodar, ele deve responder.", "nao deve iniciar com conectivo condicional/temporal"),
        ("ER", "O usuário envia uma foto e o sistema deve descrever.", "deve iniciar com termo correspondente"),
        ("ER", "Quando o usuario envia uma foto, ele mostra o resultado.", "deve conter um verbo de obrigação"),
        ("SR", "O sistema deve resetar o histórico enquanto estiver inativo.", "deve iniciar com termo correspondente"),
        ("UB", "O token está ausente e o sistema deve falhar.", "deve iniciar com termo correspondente"),
    ])
    def test_requisitos_invalidos(self, tipo, texto, erro_esperado):
        """Verifica se requisitos mal formatados são devidamente rejeitados."""
        sucesso, erro = validar_texto_requisito(tipo, texto)
        assert sucesso is False, f"Requisito invalido '{texto}' passou inesperadamente."
        assert erro_esperado in erro.lower()

    def test_prd_producao_valido(self):
        """Valida que o arquivo docs/prd.md oficial do projeto está 100% correto."""
        sucesso, metricas = validar_prd()
        assert sucesso is True, "O docs/prd.md contem erros sintaticos de EARS. Execute 'python scripts/valida_ears.py' para ver os detalhes."
        assert metricas["UR"] > 0
        assert metricas["ER"] > 0
        assert metricas["SR"] > 0
        assert metricas["UB"] > 0
