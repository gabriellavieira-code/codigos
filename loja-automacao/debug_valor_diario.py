#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date
from relatorio_semanal import contar_dias_restantes, formatar_moeda

# Hoje = 24/02/2026 (terça)
hoje = date(2026, 2, 24)
mes, ano, dia = hoje.month, hoje.year, hoje.day

print("=" * 80)
print("🔍 DEBUG: Cálculo de 'Por dia'")
print("=" * 80)

print(f"\n📅 Hoje: {hoje.strftime('%A, %d/%m/%Y')}")
print(f"   Dia do mês: {dia}")
print(f"   Mês: {mes} | Ano: {ano}")

# Calcular dias restantes
dias_rest = contar_dias_restantes(ano, mes, dia)
print(f"\n📊 Dias restantes (de {dia} até fim de fevereiro):")
print(f"   {dias_rest} dias úteis")

# Dados do relatório
vendas = 54424.85
meta = 80000.00
faltam = meta - vendas

print(f"\n💰 Vendas atuais:")
print(f"   Vendas: {formatar_moeda(vendas)}")
print(f"   Meta: {formatar_moeda(meta)}")
print(f"   Faltam: {formatar_moeda(faltam)}")

# Calcular valor por dia
val_diario = (meta - vendas) / dias_rest if dias_rest > 0 else 0

print(f"\n📈 RESULTADO:")
print(f"   Cálculo: ({formatar_moeda(meta)} - {formatar_moeda(vendas)}) / {dias_rest}")
print(f"   Valor por dia: {formatar_moeda(val_diario)}")

print("\n" + "=" * 80)
if val_diario > 0:
    print(f"✅ CORRETO: Precisar vender {formatar_moeda(val_diario)} por dia")
    print(f"            para bater a meta de {formatar_moeda(meta)}")
else:
    print(f"❌ PROBLEMA: Valor zerado ou negativo!")
print("=" * 80)
