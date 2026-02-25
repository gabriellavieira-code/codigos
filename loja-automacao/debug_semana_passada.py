"""
Debug: Verificar dados da semana passada (16/02 a 22/02)
"""
from datetime import date
from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, obter_dados_aba,
    calcular_vendas_produtos, extrair_vendas_diarias,
    NOMES_MESES
)

planilha = conectar()
abas = carregar_abas_disponiveis(planilha)

print("=" * 70)
print("🔍 VERIFICANDO DADOS: Semana 16/02 a 22/02")
print("=" * 70)

# FEV 2026 - semana passada
print(f"\n🔷 FEVEREIRO 2026 (16/02 a 22/02):")
dados_2026, linhas_2026, aba_2026 = obter_dados_aba(planilha, abas, 2, 2026)
if dados_2026:
    dias_2026 = extrair_vendas_diarias(dados_2026, linhas_2026, 2, 2026)
    
    semana_2026 = [d for d in dias_2026 if 16 <= d["dia"] <= 22]
    total_2026 = sum(d["produtos"] for d in semana_2026)
    
    print(f"   Aba: {aba_2026}")
    print(f"   Dias na semana:")
    for d in semana_2026:
        print(f"      Dia {d['dia']:02d} ({d['dia_semana_nome']:6}): R$ {d['produtos']:>10,.2f}")
    print(f"   TOTAL: R$ {total_2026:,.2f}")
else:
    print(f"   ❌ Não conseguiu ler dados!")

# FEV 2025 - mesma semana
print(f"\n🔶 FEVEREIRO 2025 (16/02 a 22/02):")
dados_2025, linhas_2025, aba_2025 = obter_dados_aba(planilha, abas, 2, 2025)
if dados_2025:
    dias_2025 = extrair_vendas_diarias(dados_2025, linhas_2025, 2, 2025)
    
    semana_2025 = [d for d in dias_2025 if 16 <= d["dia"] <= 22]
    total_2025 = sum(d["produtos"] for d in semana_2025)
    
    print(f"   Aba: {aba_2025}")
    print(f"   Dias na semana:")
    for d in semana_2025:
        print(f"      Dia {d['dia']:02d} ({d['dia_semana_nome']:6}): R$ {d['produtos']:>10,.2f}")
    print(f"   TOTAL: R$ {total_2025:,.2f}")
else:
    print(f"   ❌ Não conseguiu ler dados!")

# Comparação
print("\n" + "=" * 70)
print("📊 COMPARAÇÃO:")
print("=" * 70)
if dados_2026 and dados_2025:
    print(f"\n2026 (16/02-22/02): R$ {total_2026:>12,.2f}  ← HTML diz: R$11.078,45")
    print(f"2025 (16/02-22/02): R$ {total_2025:>12,.2f}  ← HTML diz: R$15.282,67")
    
    if abs(total_2026 - 11078.45) < 0.01:
        print(f"\n✅ 2026: Valor CORRETO")
    else:
        print(f"\n❌ 2026: Valor INCORRETO (diferença: R$ {abs(total_2026 - 11078.45):,.2f})")
    
    if abs(total_2025 - 15282.67) < 0.01:
        print(f"✅ 2025: Valor CORRETO")
    else:
        print(f"❌ 2025: Valor INCORRETO (diferença: R$ {abs(total_2025 - 15282.67):,.2f})")

print("\n✅ Debug concluído!")
