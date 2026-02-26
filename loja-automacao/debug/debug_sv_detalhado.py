"""
Debug detalhado de analise_semana_que_vem
"""
from datetime import date
import calendar
from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, encontrar_aba,
    obter_dados_aba, calcular_semana, calcular_vendas_produtos,
    NOMES_MESES
)

hoje = date.today()
mes, ano = hoje.month, hoje.year

planilha = conectar()
abas = carregar_abas_disponiveis(planilha)

print(f"📅 Data hoje: {hoje} ({['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'][hoje.weekday()]})")

# Calcular a semana atual
inicio, fim = calcular_semana(hoje)
print(f"\n🗓️  Semana ATUAL (calcular_semana):")
print(f"   Início: {inicio} ({['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'][inicio.weekday()]})")
print(f"   Fim: {fim} ({['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'][fim.weekday()]})")

# Procurar dados do ano anterior
mes_ref, ano_ref = inicio.month, inicio.year
print(f"\n🔍 Procurando dados para {mes_ref}/{ano_ref} e {mes_ref}/{ano_ref-1}...")

dados_ant, linhas_ant, aba_ant = obter_dados_aba(planilha, abas, mes_ref, ano_ref - 1)

if dados_ant is None:
    print(f"   ❌ Dados de {mes_ref}/{ano_ref-1} NÃO ENCONTRADOS")
else:
    print(f"   ✅ Aba encontrada: {aba_ant}")
    
    # Calcular vendas do ano anterior
    ult_mes = calendar.monthrange(ano_ref, mes_ref)[1]
    fim_lim = min(fim.day, ult_mes)
    
    ult_ant = calendar.monthrange(ano_ref - 1, mes_ref)[1]
    
    print(f"   Calculando vendas de {inicio.day:02d} a {fim_lim:02d}...")
    print(f"   (Ano anterior: {ano_ref-1}, dias disponíveis até {ult_ant})")
    
    vendas_ant, _ = calcular_vendas_produtos(
        dados_ant, linhas_ant, 
        min(inicio.day, ult_ant), 
        min(fim_lim, ult_ant)
    )
    
    print(f"   Vendas ano anterior: R$ {vendas_ant:,.2f}")
    
    if vendas_ant == 0:
        print(f"   ⚠️ VENDAS ZERADAS - função retornará None")
    else:
        print(f"   ✅ Dados OK para retornar")

print("\n✅ Debug concluído!")
