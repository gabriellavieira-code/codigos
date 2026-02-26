#!/usr/bin/env python3
"""
Teste completo: Mostrar TODOS os dados que aparecerão no relatório
"""
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date
from relatorio_semanal import (
    calcular_semana,
    calcular_proxima_semana,
    contar_dias_restantes,
    analise_semanal_passada,
    analise_semana_que_vem,
    conectar,
    carregar_abas_disponiveis,
    ler_vendas,
    NOMES_MESES,
    formatar_moeda
)

def main():
    hoje = date.today()
    mes, ano, dia = hoje.month, hoje.year, hoje.day
    nome_mes = NOMES_MESES[mes]
    
    print("=" * 80)
    print("📊 RELATÓRIO CORRIGIDO")
    print("=" * 80)
    
    # Conectar
    planilha = conectar()
    abas = carregar_abas_disponiveis(planilha)
    
    # Cabeçalho
    print(f"\n📅 {nome_mes.upper()} {ano} — Dia {dia:02d}/{mes:02d}/{ano}")
    
    # Vendas de hoje
    dados = ler_vendas(planilha, abas, mes, ano, dia)
    if dados:
        vendas = dados["vendas_produtos"]
        meta = dados["meta_total"]
        print(f"\n💰 VENDAS:")
        print(f"   Vendas: {formatar_moeda(vendas)}")
        print(f"   Meta:   {formatar_moeda(meta)}")
        print(f"   Faltam: {formatar_moeda(meta - vendas)}")
        
        # Dias restantes
        dias_rest = contar_dias_restantes(ano, mes, dia)
        val_diario = (meta - vendas) / dias_rest if dias_rest > 0 else 0
        print(f"\n📈 POR DIA:")
        print(f"   Dias restantes: {dias_rest:.1f}")
        print(f"   Faltam por dia: {formatar_moeda(val_diario)}")
    
    # Semana passada
    print(f"\n📊 SEMANA PASSADA:")
    sp = analise_semanal_passada(planilha, abas, hoje)
    if sp:
        print(f"   Período: {sp['inicio'].strftime('%d/%m')} a {sp['fim'].strftime('%d/%m')}")
        print(f"   Esta semana:      {formatar_moeda(sp['vendas'])}")
        print(f"   Mesma semana 2025: {formatar_moeda(sp['vendas_ant'])}")
        print(f"   Diferença:        {formatar_moeda(sp['diferenca'])} ({sp['percentual']:+.1f}%)")
    else:
        print(f"   ❌ SEM DADOS")
    
    # Semana que vem
    print(f"\n📊 SEMANA QUE VEM:")
    sv = analise_semana_que_vem(planilha, abas, hoje)
    if sv:
        print(f"   Período: {sv['inicio'].strftime('%d/%m')} a {sv['fim'].strftime('%d/%m')}")
        print(f"   Mesma semana 2025: {formatar_moeda(sv['vendas_ano_passado'])}")
    else:
        print(f"   ❌ SEM DADOS")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
