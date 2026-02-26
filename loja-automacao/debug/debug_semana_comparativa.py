"""
Debug: Verificar dados de dias 23 e 24 para ambos os anos
"""
import os
import sys
from datetime import date
import calendar
from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, encontrar_aba, obter_dados_aba,
    extrair_vendas_diarias, NOMES_MESES, DIAS_SEMANA_PT
)

hoje = date.today()
mes, ano = hoje.month, hoje.year

print("=" * 60)
print(f"📊 COMPARATIVO: Vendas dias 23-24 (Fevereiro 2026 vs 2025)")
print("=" * 60)

# Conectar ao Google Sheets
planilha = conectar()
abas = carregar_abas_disponiveis(planilha)

# ═══════════════════════════════════════════════════════════
# DADOS 2026 (ATUAL)
# ═══════════════════════════════════════════════════════════
print(f"\n🔷 FEVEREIRO 2026 (Atual):")
dados_2026, linhas_2026, aba_2026 = obter_dados_aba(planilha, abas, mes, ano)
if dados_2026:
    dias_2026 = extrair_vendas_diarias(dados_2026, linhas_2026, mes, ano)
    print(f"   Aba: {aba_2026}")
    print(f"   Total de dias com vendas: {len(dias_2026)}")
    
    dias_23_24_2026 = [d for d in dias_2026 if d["dia"] in [23, 24]]
    print(f"\n   Dias 23-24:")
    for d in dias_2026:
        if d["dia"] in [23, 24]:
            print(f"      Dia {d['dia']} ({d['dia_semana_nome']}): R$ {d['produtos']:>10,.2f}")
    
    if not dias_23_24_2026:
        print(f"      ❌ Nenhum dado encontrado para dias 23-24")
else:
    print(f"   ❌ Não conseguiu ler dados!")

# ═══════════════════════════════════════════════════════════
# DADOS 2025 (ANO ANTERIOR)
# ═══════════════════════════════════════════════════════════
print(f"\n🔶 FEVEREIRO 2025 (Anterior):")
dados_2025, linhas_2025, aba_2025 = obter_dados_aba(planilha, abas, mes, ano - 1)
if dados_2025:
    dias_2025 = extrair_vendas_diarias(dados_2025, linhas_2025, mes, ano - 1)
    print(f"   Aba: {aba_2025}")
    print(f"   Total de dias com vendas: {len(dias_2025)}")
    
    dias_23_24_2025 = [d for d in dias_2025 if d["dia"] in [23, 24]]
    print(f"\n   Dias 23-24:")
    for d in dias_2025:
        if d["dia"] in [23, 24]:
            print(f"      Dia {d['dia']} ({d['dia_semana_nome']}): R$ {d['produtos']:>10,.2f}")
    
    if not dias_23_24_2025:
        print(f"      ⚠️  Nenhum dado encontrado para dias 23-24")
else:
    print(f"   ❌ Não conseguiu ler dados!")

# ═══════════════════════════════════════════════════════════
# ANÁLISE
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("💡 ANÁLISE:")
print("=" * 60)

if dias_2026:
    sem_4_dias_2026 = [d for d in dias_2026 if d["dia"] >= 23 and d["dia"] <= 29]  # Semana 4
    total_sem_4_2026 = sum(d["produtos"] for d in sem_4_dias_2026)
    print(f"\n2026 - Semana 4 (23 a 29): R$ {total_sem_4_2026:,.2f}")
    print(f"       Dias: {[d['dia'] for d in sem_4_dias_2026]}")

if dias_2025:
    sem_4_dias_2025 = [d for d in dias_2025 if d["dia"] >= 23 and d["dia"] <= 29]  # Semana 4  
    total_sem_4_2025 = sum(d["produtos"] for d in sem_4_dias_2025)
    print(f"\n2025 - Semana 4 (23 a 29): R$ {total_sem_4_2025:,.2f}")
    print(f"       Dias: {[d['dia'] for d in sem_4_dias_2025]}")

print("\n✅ Debug concluído!")
