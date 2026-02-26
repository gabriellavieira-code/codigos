"""
Debug: Verificar o que é passado para o template HTML
"""
import os
import sys
from datetime import date
from relatorio_semanal import gerar_dados_relatorio

# Gerar os dados sem fechamento
r = gerar_dados_relatorio(forcar_fechamento=False)

if not r:
    print("❌ Não foi possível gerar dados!")
    sys.exit(1)

print("=" * 60)
print("📊 Dados que serão mostrados no relatório:")
print("=" * 60)

# Insights
print(f"\n🔍 Insights - Comparativo Semanal:")
if r.get("insights"):
    comp = r["insights"].get("comparativo_semanal", [])
    if comp:
        for cs in comp:
            print(f"   Semana {cs['semana']}: {cs['dia_inicio']:02d}-{cs['dia_fim']:02d} → Vendas R${cs['vendas']:>10,.2f} | Ano ant. R${cs['vendas_ant']:>10,.2f}")
    else:
        print("   ❌ Comparativo semanal VAZIO!")
else:
    print("   ❌ Sem insights!")

# Verificar o que está no comparativo_semanal original
print(f"\n📋 Dias diários (atual):")
dias_diarios = r.get("dias_diarios", [])
if dias_diarios:
    for dia in dias_diarios:
        if dia["dia"] >= 23:
            print(f"   Dia {dia['dia']:02d}: R$ {dia['produtos']:>10,.2f}")
else:
    print("   ❌ Sem dados diários!")

print("\n✅ Debug concluído!")
