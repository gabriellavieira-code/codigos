"""
Debug: Verificar a semana 4 em 2025 - por que só R$ 2.514,10?
"""
from datetime import date
import calendar
from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, encontrar_aba, obter_dados_aba,
    extrair_vendas_diarias, DIAS_SEMANA_PT, NOMES_MESES
)

planilha = conectar()
abas = carregar_abas_disponiveis(planilha)

# FEV 2025
dados_2025, linhas_2025, aba_2025 = obter_dados_aba(planilha, abas, 2, 2025)
dias_2025 = extrair_vendas_diarias(dados_2025, linhas_2025, 2, 2025) if dados_2025 else []

# FEV 2026
dados_2026, linhas_2026, aba_2026 = obter_dados_aba(planilha, abas, 2, 2026)
dias_2026 = extrair_vendas_diarias(dados_2026, linhas_2026, 2, 2026) if dados_2026 else []

print("=" * 70)
print("🔍 ANÁLISE DA SEMANA 4 (23-24 de Fevereiro)")
print("=" * 70)

print("\n📅 Calendário - Dia da Semana:")
for ano in [2025, 2026]:
    print(f"\n   {ano}:")
    for dia in range(23, 26):
        try:
            dt = date(ano, 2, dia)
            print(f"      23/{dia}: {DIAS_SEMANA_PT[dt.weekday()]:8} (dia {dt.day})")
        except ValueError:
            pass

print("\n" + "=" * 70)
print("💰 VENDAS REAIS NA PLANILHA:")
print("=" * 70)

print(f"\n🔷 FEV 2025 - Semana 4:")
print(f"   Total de dias com vendas no mês: {len(dias_2025)}")
dias_sem4_2025 = [d for d in dias_2025 if d["dia"] >= 23]
if dias_sem4_2025:
    for d in dias_sem4_2025:
        print(f"      Dia {d['dia']:02d} ({d['dia_semana_nome']:8}): R$ {d['produtos']:>10,.2f}")
    total_sem4_2025 = sum(d["produtos"] for d in dias_sem4_2025)
    print(f"      Total semana 4: R$ {total_sem4_2025:>10,.2f}")
else:
    print("      ❌ Nenhum dado encontrado para dias 23+")

print(f"\n🔶 FEV 2026 - Semana 4:")
print(f"   Total de dias com vendas no mês: {len(dias_2026)}")
dias_sem4_2026 = [d for d in dias_2026 if d["dia"] >= 23]
if dias_sem4_2026:
    for d in dias_sem4_2026:
        print(f"      Dia {d['dia']:02d} ({d['dia_semana_nome']:8}): R$ {d['produtos']:>10,.2f}")
    total_sem4_2026 = sum(d["produtos"] for d in dias_sem4_2026)
    print(f"      Total semana 4: R$ {total_sem4_2026:>10,.2f}")
else:
    print("      ❌ Nenhum dado encontrado para dias 23+")

print("\n" + "=" * 70)
print("📊 CONCLUSÃO:")
print("=" * 70)

if dias_sem4_2025:
    dias_abertos_2025 = len(dias_sem4_2025)
    print(f"\nFEV 2025: A loja abriu apenas {dias_abertos_2025} dia(s) na semana (23-29 fev)")
    print(f"        → Dia 23 era {DIAS_SEMANA_PT[date(2025, 2, 23).weekday()]} (não abriu domingo)")
    print(f"        → Vendas: R$ {sum(d['produtos'] for d in dias_sem4_2025):,.2f}")
else:
    print(f"\nFEV 2025: A loja pode não ter aberto na semana 4 (23-29 fev)")

print(f"\nFEV 2026: A loja abriu {len(dias_sem4_2026)} dias na semana (23-29 fev)")
print(f"        → Vendas: R$ {sum(d['produtos'] for d in dias_sem4_2026):,.2f}")

print("\n✅ Debug concluído!")
