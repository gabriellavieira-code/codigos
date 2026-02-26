#!/usr/bin/env python3
"""Teste simples da renderização de contas pagas."""

import sys
import os
sys.path.insert(0, '.')
os.chdir('.')

from financeiro_analise import carregar_financeiro
from relatorio_semanal import gerar_html, analise_semanal_passada, analise_semana_que_vem
from datetime import date

print("🔧 Testando renderização de contas pagas...\n")

# Carregar dados financeiros
fin, erro = carregar_financeiro()
if not fin:
    print(f"❌ Erro ao carregar financeiro: {erro}")
    sys.exit(1)

# Preparar dados para gerar_html (conforme gerar_dados_relatorio retorna)
hoje = date(2026, 2, 24)
mes, ano, dia = hoje.month, hoje.year, hoje.day

sp = analise_semanal_passada(None, [], hoje)
sv = analise_semana_que_vem(None, [], hoje)

r = {
    "hoje": hoje,
    "nome_mes": "FEVEREIRO",
    "dia": dia,
    "ano": ano,
    "vendas": 54424.85,
    "meta": 80000.00,
    "faltam": 25575.15,
    "servicos": 0,
    "diferenca_mes": 5000.00,
    "dados_anterior": None,
    "semana_passada": sp,
    "semana_que_vem": sv,
    "dias_restantes": 4,
    "valor_diario": 6393.79,
    "aviso_prox": None,
    "fechamento": False,
    "insights": [],
    "historico": {},
    "dias_diarios": [],
    "ausencias": {},
    "analise_servicos": None,
    "financeiro": fin,
}

# Gerar HTML
mensagem_simples = "Teste de renderização"
try:
    html = gerar_html(r, mensagem_simples)
    
    # Salvar arquivo de teste
    with open("relatorio_teste.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ HTML gerado com sucesso!")
    print(f"📄 Arquivo salvo: relatorio_teste.html")
    
    # Procurar por "pagas" no HTML gerado
    if "✅" in html:
        print("✅ Badge de contas pagas está no HTML!")
    else:
        print("⚠️  Badge de contas pagas não encontrado (esperado - planilha atual tem R$0 pagas)")
    
except Exception as e:
    print(f"❌ Erro ao gerar HTML: {e}")
    import traceback
    traceback.print_exc()
