#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validador EARS (Easy Approach to Requirements Syntax) para o PRD do ALFREDO.
Garante que todos os requisitos declarados em docs/prd.md sigam a sintaxe correta.
"""

import os
import re
import sys

# Caminho do PRD
PRD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "prd.md"
)

# Regex para capturar linhas de requisitos do tipo: * **UR01:** O sistema deve...
REQ_PATTERN = re.compile(r'^\*\s+\*\*(UR|ER|SR|UB)(\d+):\*\*\s*(.*)$')

# Dicionário de regras por tipo de requisito
EARS_RULES = {
    "UR": {
        "description": "Ubiquitous (Ubiquo)",
        "allowed_start": None,
        "must_contain": r'\b(deve|devem|deverá|deverão)\b',
        "forbidden_start": r'^(quando|se|enquanto|caso|ao|após|assim que|durante)\b',
        "example": "O sistema deve executar continuamente..."
    },
    "ER": {
        "description": "Event-Driven (Orientado a Eventos)",
        "allowed_start": r'^(quando|ao|após|apos|assim que)\b',
        "must_contain": r'\b(deve|devem|deverá|deverão)\b',
        "forbidden_start": None,
        "example": "Quando o usuário enviar uma foto, o sistema deve..."
    },
    "SR": {
        "description": "State-Driven (Orientado a Estado)",
        "allowed_start": r'^(enquanto|durante|seja)\b',
        "must_contain": r'\b(deve|devem|deverá|deverão)\b',
        "forbidden_start": None,
        "example": "Enquanto houver uma sessão ativa, o sistema deve..."
    },
    "UB": {
        "description": "Unwanted Behavior (Comportamento Indesejado)",
        "allowed_start": r'^(se|caso)\b',
        "must_contain": r'\b(deve|devem|deverá|deverão)\b',
        "forbidden_start": None,
        "example": "Se a chave de API estiver ausente, o sistema deve..."
    }
}

def validar_texto_requisito(tipo, texto):
    """Valida o corpo de um requisito contra as regras do tipo EARS correspondente."""
    regra = EARS_RULES.get(tipo)
    if not regra:
        return False, f"Tipo de requisito desconhecido: {tipo}"

    texto_lower = texto.strip().lower()

    # 1. Verifica se contém o verbo modal de obrigação (deve/devem/deverá)
    if not re.search(regra["must_contain"], texto_lower):
        return False, f"Requisito deve conter um verbo de obrigação (ex: 'deve', 'deverá', 'devem')."

    # 2. Se for UR (Ubíquo), não pode começar com conectivos temporais/condicionais
    if regra["forbidden_start"]:
        if re.search(regra["forbidden_start"], texto_lower):
            conectivo = re.match(regra["forbidden_start"], texto_lower).group(0)
            return False, f"Requisito ubiquo nao deve iniciar com conectivo condicional/temporal '{conectivo}'. Exemplo: '{regra['example']}'."

    # 3. Se for ER, SR ou UB, deve iniciar com o conectivo/gatilho apropriado
    if regra["allowed_start"]:
        if not re.search(regra["allowed_start"], texto_lower):
            return False, (
                f"Requisito {regra['description']} deve iniciar com termo correspondente. "
                f"Exemplos validos de inicio: {regra['allowed_start'].replace('^', '').replace('(', '').replace(')', '').replace('|', ', ')}. "
                f"Exemplo: '{regra['example']}'"
            )

    return True, None

def validar_prd():
    """Lê e valida todos os requisitos em docs/prd.md."""
    if not os.path.exists(PRD_PATH):
        print(f"[ERRO] Arquivo do PRD nao encontrado em {PRD_PATH}")
        return False, {}

    print(f"[INFO] Lendo PRD de {PRD_PATH}...")
    
    with open(PRD_PATH, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    requisitos_encontrados = 0
    erros = []
    metricas = {"UR": 0, "ER": 0, "SR": 0, "UB": 0}

    for num_linha, linha in enumerate(linhas, 1):
        linha_clean = linha.strip()
        match = REQ_PATTERN.match(linha_clean)
        
        if match:
            requisitos_encontrados += 1
            tipo = match.group(1)
            codigo = match.group(2)
            texto = match.group(3)

            identificador = f"{tipo}{codigo}"
            metricas[tipo] += 1

            sucesso, msg_erro = validar_texto_requisito(tipo, texto)
            if not sucesso:
                erros.append({
                    "linha": num_linha,
                    "id": identificador,
                    "texto": texto,
                    "erro": msg_erro
                })

    print(f"[INFO] Total de requisitos mapeados no PRD: {requisitos_encontrados}")
    for tipo, count in metricas.items():
        print(f"   - {EARS_RULES[tipo]['description']} ({tipo}): {count}")

    if erros:
        print(f"\n[ERRO] Falha na validacao EARS! Encontrados {len(erros)} erro(s):")
        for err in erros:
            print(f"   [Linha {err['linha']}] {err['id']}: \"{err['texto']}\"")
            print(f"       Erro: {err['erro']}")
        return False, metricas

    print("\n[OK] Todos os requisitos do PRD estao validos no formato EARS!")
    return True, metricas

if __name__ == "__main__":
    sucesso, _ = validar_prd()
    if not sucesso:
        sys.exit(1)
    sys.exit(0)
