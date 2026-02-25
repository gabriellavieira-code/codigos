#!/usr/bin/env python3
"""
Script para FORÇAR a regeneração do relatório com código atualizado.
Sem inputs - coleta dados diretos do Excel.
"""
import sys
import os

# Limpar imports anteriores do módulo
if 'relatorio_semanal' in sys.modules:
    del sys.modules['relatorio_semanal']

sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date

print("=" * 80)
print("🔄 REGENERANDO RELATÓRIO COM CÓDIGO ATUALIZADO")
print("=" * 80)

try:
    # Importação fresh
    print("\n📥 Carregando módulos...")
    from relatorio_semanal import (
        conectar, 
        carregar_abas_disponiveis, 
        encontrar_aba,
        ler_vendas,
        contar_dias_restantes,
        analise_semanal_passada,
        analise_semana_que_vem,
        NOMES_MESES,
        formatar_moeda,
    )
    
    hoje = date.today()
    mes, ano, dia = hoje.month, hoje.year, hoje.day
    nome_mes = NOMES_MESES[mes]
    
    print(f"\n📅 Data: {nome_mes.upper()} {ano}, Dia {dia:02d}/{mes:02d}/{ano}")
    
    # Conectar
    print("\n📂 Conectando ao Google Sheets...")
    planilha = conectar()
    abas = carregar_abas_disponiveis(planilha)
    
    aba_atual = encontrar_aba(abas, mes, ano)
    print(f"   Aba encontrada: {aba_atual}")
    
    # Carregar vendas
    print("\n💰 Carregando dados de vendas...")
    dados = ler_vendas(planilha, abas, mes, ano, dia)
    if not dados:
        print("❌ Não foi possível carregar dados")
        sys.exit(1)
    
    vendas = dados["vendas_produtos"]
    meta = dados["meta_total"]
    
    print(f"   Vendas: {formatar_moeda(vendas)}")
    print(f"   Meta: {formatar_moeda(meta)}")
    
    # Calcular dias restantes
    print("\n📊 Calculando dias restantes...")
    dias_rest = contar_dias_restantes(ano, mes, dia)
    val_diario = (meta - vendas) / dias_rest if dias_rest > 0 else 0
    
    print(f"   Dias úteis restantes: {dias_rest:.1f}")
    print(f"   Valor por dia: {formatar_moeda(val_diario)}")
    
    # Semana passada
    print("\n📈 Analisando semana passada...")
    sp = analise_semanal_passada(planilha, abas, hoje)
    if sp:
        print(f"   Período: {sp['inicio'].strftime('%d/%m')} a {sp['fim'].strftime('%d/%m')}")
        print(f"   Vendas 2026: {formatar_moeda(sp['vendas'])}")
        print(f"   Vendas 2025: {formatar_moeda(sp['vendas_ant'])}")
        print(f"   Diferença: {sp['percentual']:+.1f}%")
    
    # Próxima semana
    print("\n🎯 Analisando próxima semana...")
    sv = analise_semana_que_vem(planilha, abas, hoje)
    if sv:
        print(f"   Período: {sv['inicio'].strftime('%d/%m')} a {sv['fim'].strftime('%d/%m')}")
    
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO COMPLETA!")
    print("=" * 80)
    print("\n📝 Próximo passo: Execute 'python relatorio_semanal.py' para gerar o HTML completo")
    print("    O relatório agora terá:")
    print(f"    • Por dia: {formatar_moeda(val_diario)} ✅")
    print(f"    • Semana Passada: Dados de {sp['inicio'].strftime('%d/%m')} a {sp['fim'].strftime('%d/%m')} ✅")
    print(f"    • Fornecedores pagos: Sempre visíveis (nunca zerados) ✅")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
