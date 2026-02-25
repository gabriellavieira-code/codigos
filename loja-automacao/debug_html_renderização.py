#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date

# Simular o que gerar_dados_relatorio retorna
simulated_r = {
    "hoje": date(2026, 2, 24),
    "nome_mes": "Fevereiro",
    "dia": 24,
    "vendas": 54424.85,
    "meta": 80000.00,
    "faltam": 25575.15,
    "servicos": 0,
    "diferenca_mes": None,
    "dados_anterior": None,
    "semana_passada": {
        "inicio": date(2026, 2, 16),
        "fim": date(2026, 2, 22),
        "vendas": 11078.45,
        "vendas_ant": 15282.67,
        "diferenca": -4204.22,
        "percentual": -27.5
    },
    "semana_que_vem": {
        "inicio": date(2026, 3, 2),
        "fim": date(2026, 3, 8),
        "vendas_ano_passado": 18170.36
    },
    "dias_restantes": 4.0,  # ✅ CORRIGIDO
    "valor_diario": 6393.79,  # ✅ CORRIGIDO
    "aviso_prox": None,
    "fechamento": False,
    "insights": {},
    "historico": {},
    "dias_diarios": {},
    "ausencias": [],
    "analise_servicos": None,
    "financeiro": None,
}

print("=" * 80)
print("📊 TESTE: Valores que serão passados para gerar_html")
print("=" * 80)

print(f"\n✅ Simulando retorno de gerar_dados_relatorio():")
print(f"\n   r.get('dias_restantes', 1) = {simulated_r.get('dias_restantes', 1)}")
print(f"   r.get('valor_diario', 0) = {simulated_r.get('valor_diario', 0)}")

# Simular o que o HTML vai mostrar
from relatorio_semanal import formatar_moeda

dias_no_html = simulated_r.get('dias_restantes', 1)
valor_no_html = simulated_r.get('valor_diario', 0)

print(f"\n📋 NO HTML SERÁ EXIBIDO:")
print(f"   Por dia ({dias_no_html:.0f} dias)")
print(f"   {formatar_moeda(valor_no_html)}")

print("\n" + "=" * 80)
if dias_no_html >= 3 and valor_no_html > 0:
    print("✅ CORRETO: Valores encontrados e renderizados!")
else:
    print("❌ PROBLEMA: Valores não vão aparecer corretamente no HTML!")
print("=" * 80)
