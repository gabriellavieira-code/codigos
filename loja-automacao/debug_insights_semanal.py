"""
Debug: Verificar dados sem interação
"""
import os
import sys
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import calendar

from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, encontrar_aba, obter_dados_aba,
    extrair_vendas_diarias, gerar_insights, NOMES_MESES
)

hoje = date.today()
mes, ano = hoje.month, hoje.year

# Conectar
planilha = conectar()
abas = carregar_abas_disponiveis(planilha)

# Dados 2026
dados_2026, linhas_2026, aba_2026 = obter_dados_aba(planilha, abas, mes, ano)
dias_2026 = extrair_vendas_diarias(dados_2026, linhas_2026, mes, ano) if dados_2026 else []

# Dados 2025
dados_2025, linhas_2025, aba_2025 = obter_dados_aba(planilha, abas, mes, ano - 1)
dias_2025 = extrair_vendas_diarias(dados_2025, linhas_2025, mes, ano - 1) if dados_2025 else []

# Gerar insights (sem serem inclusos, apenas dados brutos)
insights = gerar_insights(dias_2026, dias_2025, mes, ano)

print("\n" + "=" * 70)
print("📊 DADOS PARA O RELATÓRIO")
print("=" * 70)

print(f"\n🔷 Comparativo Semanal (será exibido na tabela):")
comp = insights.get("comparativo_semanal", [])
if comp:
    print(f"   Total: {len(comp)} semanas\n")
    for cs in comp:
        print(f"   Semana {cs['semana']:d}: {cs['dia_inicio']:02d}/{mes:02d} a {cs['dia_fim']:02d}/{mes:02d}")
        print(f"      2026: R$ {cs['vendas']:>12,.2f}")
        print(f"      2025: R$ {cs['vendas_ant']:>12,.2f}")
        print(f"      Dif:  {cs['percentual']:+.1f}%")
        print()
else:
    print("   ❌ VAZIO!")

print("\n✅ Debug concluído!")
