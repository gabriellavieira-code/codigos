#!/usr/bin/env python3
"""
Teste: Gerar relatório e mostrar os dados estruturados
"""
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date

# Simular nova execução sem input
def main():
    print("=" * 80)
    print("🔄 GERANDO RELATÓRIO COM CORREÇÕES")
    print("=" * 80)
    
    # Importar apenas o que precisa
    from relatorio_semanal import (
        gerar_dados_relatorio, 
        analise_semanal_passada,
        contar_dias_restantes,
        calcular_semana,
        conectar,
        carregar_abas_disponiveis,
        encontrar_aba
    )
    
    hoje = date.today()
    print(f"\n📅 Data: {hoje.strftime('%A, %d/%m/%Y')}")
    print(f"   (hoje.weekday() = {hoje.weekday()})\n")
    
    # Teste das funções de semana
    inicio, fim = calcular_semana(hoje)
    print(f"📊 SEMANA ATUAL:")
    print(f"   {inicio.strftime('%A, %d/%m')} a {fim.strftime('%A, %d/%m')}")
    print(f"   Duração: {(fim - inicio).days + 1} dias")
    
    # Teste dias restantes
    dias_rest = contar_dias_restantes(hoje.year, hoje.month, hoje.day)
    print(f"\n📊 DIAS RESTANTES EM {hoje.strftime('%B').upper()}:")
    print(f"   {dias_rest} dias úteis")
    print(f"   Cálculo de por dia: (meta - vendas) / {dias_rest:.1f}")
    
    # Teste análise semana passada
    try:
        planilha = conectar()
        abas = carregar_abas_disponiveis(planilha)
        sp = analise_semanal_passada(planilha, abas, hoje)
        
        if sp:
            print(f"\n📊 SEMANA PASSADA:")
            print(f"   Período: {sp['inicio'].strftime('%d/%m')} a {sp['fim'].strftime('%d/%m')}")
            print(f"   Vendas 2026: R${sp['vendas']:,.2f}")
            print(f"   Vendas 2025: R${sp['vendas_ant']:,.2f}")
            print(f"   Diferença: R${sp['diferenca']:,.2f} ({sp['percentual']:.1f}%)")
            
            if sp['percentual'] < 0:
                print(f"   ⚠️ ATENÇÃO: Semana passada foi PIOR que 2025!")
            else:
                print(f"   ✅ Semana passada foi MELHOR que 2025!")
        else:
            print(f"\n⚠️ Semana passada: SEM DADOS")
            
    except Exception as e:
        print(f"⚠️ Erro ao carregar semana passada: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
