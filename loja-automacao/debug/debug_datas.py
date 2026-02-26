#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from relatorio_semanal import calcular_semana, calcular_proxima_semana, contar_dias_restantes

# Hoje é 24/02/2026 (segunda-feira)
hoje = date(2026, 2, 24)

print("=" * 80)
print(f"📅 HOJE: {hoje.strftime('%A')} {hoje.day:02d}/{hoje.month:02d}/{hoje.year}")
print(f"   (weekday: {hoje.weekday()}) 0=seg, 1=ter, 2=qua, 3=qui, 4=sex, 5=sab, 6=dom")
print("=" * 80)

# Semana atual
inicio, fim = calcular_semana(hoje)
print(f"\n📊 SEMANA ATUAL (calcular_semana):")
print(f"   Início: {inicio.strftime('%A')} {inicio.day:02d}/{inicio.month:02d}/{inicio.year}")
print(f"   Fim:    {fim.strftime('%A')} {fim.day:02d}/{fim.month:02d}/{fim.year}")
print(f"   Dias:   {(fim - inicio).days + 1} dias")

# Próxima semana
prox_inicio, prox_fim = calcular_proxima_semana(hoje)
print(f"\n📊 PRÓXIMA SEMANA (calcular_proxima_semana):")
print(f"   Início: {prox_inicio.strftime('%A')} {prox_inicio.day:02d}/{prox_inicio.month:02d}/{prox_inicio.year}")
print(f"   Fim:    {prox_fim.strftime('%A')} {prox_fim.day:02d}/{prox_fim.month:02d}/{prox_fim.year}")

# Dias restantes
dias_rest = contar_dias_restantes(hoje.year, hoje.month, hoje.day)
print(f"\n📊 DIAS RESTANTES EM FEVEREIRO:")
print(f"   De 24/02 até 28/02: {dias_rest} dias úteis")
print(f"   Cálculo: (meta - vendas) / {dias_rest if dias_rest > 0 else 'ERRO: 0!'}")

print("\n" + "=" * 80)
print("PROBLEMA IDENTIFICADO:")
print("-" * 80)
if (fim - inicio).days + 1 < 5:
    print("❌ SEMANA ATUAL tem menos de 5 dias (deve ter 7 ou mais)")
if dias_rest == 0 or dias_rest < 2:
    print("❌ DIAS RESTANTES está zerado ou muito baixo (deve ter ~4 dias úteis)")
print("=" * 80)
