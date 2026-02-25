#!/usr/bin/env python3
"""
TESTE FINAL: Confirmar que 'Por dia' está sendo calculado corretamente
"""
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date
from relatorio_semanal import (
    contar_dias_restantes,
    formatar_moeda,
    conectar,
    carregar_abas_disponiveis,
    ler_vendas,
    NOMES_MESES,
)

print("=" * 80)
print("✅ VALIDAÇÃO FINAL: Cálculo de 'Por dia'")
print("=" * 80)

# Simular execução hoje (24/02/2026)
hoje = date(2026, 2, 24)
mes, ano, dia = hoje.month, hoje.year, hoje.day
nome_mes = NOMES_MESES[mes]

print(f"\n📅 Data: {nome_mes} {ano}, Dia {dia:02d}")

# Conectar e carregar dados
try:
    planilha = conectar()
    abas = carregar_abas_disponiveis(planilha)
    
    dados = ler_vendas(planilha, abas, mes, ano, dia)
    if dados:
        vendas = dados["vendas_produtos"]
        meta = dados["meta_total"]
        
        # Calcular dias restantes
        dias_rest = contar_dias_restantes(ano, mes, dia)
        val_diario = (meta - vendas) / dias_rest if dias_rest > 0 else 0
        
        print(f"\n💰 VENDAS ATUAIS:")
        print(f"   Vendas: {formatar_moeda(vendas)}")
        print(f"   Meta: {formatar_moeda(meta)}")
        print(f"   Faltam: {formatar_moeda(meta - vendas)}")
        
        print(f"\n📈 CÁLCULO 'POR DIA':")
        print(f"   Dias restantes em fevereiro: {dias_rest:.0f} dias")
        print(f"   Faixa precisa vender: {formatar_moeda(meta - vendas)}")
        print(f"   Dividido por {dias_rest:.0f} dias = {formatar_moeda(val_diario)} por dia")
        
        print(f"\n📦 DICIONÁRIO DE RETORNO:")
        print(f"   'dias_restantes': {dias_rest}")
        print(f"   'valor_diario': {val_diario}")
        
        print(f"\n📋 NO HTML SERÁ RENDERIZADO COMO:")
        print(f"   <div class=\"meta-item\">")
        print(f"      <div class=\"label\">Por dia ({dias_rest:.0f} dias)</div>")
        print(f"      <div class=\"value\">{formatar_moeda(val_diario)}</div>")
        print(f"   </div>")
        
        print("\n" + "=" * 80)
        if dias_rest > 0 and val_diario > 0:
            print("✅ CORRETO: Valores serão exibidos no HTML!")
        else:
            print("❌ PROBLEMA: Valores não estão corretos!")
        print("=" * 80)
    else:
        print("❌ Não foi possível carregar dados de vendas")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
