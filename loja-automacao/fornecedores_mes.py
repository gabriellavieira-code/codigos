# ══════════════════════════════════════════════════════════
# FORNECEDORES DO MÊS — Bem Me Quer
# ══════════════════════════════════════════════════════════
#
# Edite este arquivo toda vez que for planejar compras.
# O relatório vai usar essas informações pra simular
# prazos e gerar o plano visual automaticamente.
#
# Como usar:
#   1. Edite a lista abaixo com os fornecedores do mês
#   2. Rode: python relatorio_semanal.py
#   3. O plano de compras aparece no relatório (dia 20+)
#
# ══════════════════════════════════════════════════════════

FORNECEDORES_MES = [
    {
        "nome": "Haskell (BL Distribuidora)",
        "prazos": [45, 60, 75],           # Prazos disponíveis em dias
        "prazo_livre": True,               # True = a gente escolhe o prazo
        "valor_sugerido": "R$4.000 a R$5.000",
        "valor_orcado": None,              # Preencher se tiver orçamento fechado (ex: 6102.72)
        "observacao": "",
    },
    {
        "nome": "Naturalles",
        "prazos": [45, 60, 75],
        "prazo_livre": True,
        "valor_sugerido": "Conservador (1º pedido)",
        "valor_orcado": None,
        "observacao": "Fornecedor novo — testar giro antes de escalar.",
    },
    {
        "nome": "Glatten (Elos Cosméticos)",
        "prazos": [45, 60, 75],
        "prazo_livre": False,
        "valor_sugerido": "R$4.000 a R$6.000",
        "valor_orcado": None,
        "observacao": "",
    },
    {
        "nome": "Salon Line (Lançamento)",
        "prazos": [30, 45, 60],
        "prazo_livre": False,
        "valor_sugerido": "",
        "valor_orcado": 6102.72,
        "observacao": "Lançamento = risco de encalhe. Avaliar se giro justifica o valor.",
    },
    {
        "nome": "Nutrimaxxi",
        "prazos": [30, 35, 45, 60],
        "prazo_livre": False,
        "valor_sugerido": "Baseado no giro",
        "valor_orcado": None,
        "observacao": "Prazo negociável. Se só aceitar 30d, tente: 'começa 30 mas a partir de abril?'",
    },
    {
        "nome": "DPC Distribuidora",
        "prazos": [30, 35, 40],
        "prazo_livre": False,
        "valor_sugerido": "R$1.000 a R$1.500",
        "valor_orcado": None,
        "observacao": "Se não aceitar 40d, segurar 1 semana e pedir 35.",
    },
    {
        "nome": "DRL",
        "prazos": [21, 30, 35],
        "prazo_livre": False,
        "valor_sugerido": "Mínimo necessário",
        "valor_orcado": None,
        "observacao": "Prazo ruim. Tentar 'prazo especial' começando em 30. Se não, esperar 1 semana pra liberar.",
    },
]
