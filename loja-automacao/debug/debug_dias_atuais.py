"""
Debug: Verificar dados dos dias 23 e 24 de fevereiro
"""
import os
import sys
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import calendar

# Importar as funções do relatorio_semanal
from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, encontrar_aba, obter_dados_aba,
    ler_valor_dia, limpar_valor, NOMES_MESES, DIAS_SEMANA_PT
)

hoje = date.today()
mes, ano, dia = hoje.month, hoje.year, hoje.day

print(f"📅 Data hoje: {dia:02d}/{mes:02d}/{ano}")
print()

# Conectar ao Google Sheets
planilha = conectar()
abas = carregar_abas_disponiveis(planilha)
print(f"📂 Abas disponíveis: {abas}")

# Pegar dados atuais
nome_aba = encontrar_aba(abas, mes, ano)
print(f"📂 Aba selecionada: {nome_aba}")

dados, linhas, _ = obter_dados_aba(planilha, abas, mes, ano)
if not dados:
    print("❌ Não conseguiu ler dados da aba!")
    sys.exit(1)

print(f"\n🔍 Verificando linhas detectadas:")
for chave, idx in linhas.items():
    if idx is not None:
        print(f"   {chave}: linha {idx} → {dados[idx][:5]}...")
    else:
        print(f"   {chave}: NÃO DETECTADA")

print(f"\n💰 Valores para os dias 23 e 24:")
for dia_check in [23, 24]:
    try:
        dt = date(ano, mes, dia_check)
    except ValueError:
        print(f"   ❌ Dia {dia_check} inválido")
        continue
    
    loja = 0
    ecom = 0
    serv = 0
    
    if linhas["loja_realizado"] is not None:
        loja = ler_valor_dia(dados[linhas["loja_realizado"]], dia_check)
    if linhas["ecommerce_realizado"] is not None:
        ecom = ler_valor_dia(dados[linhas["ecommerce_realizado"]], dia_check)
    if linhas["servicos_realizado"] is not None:
        serv = ler_valor_dia(dados[linhas["servicos_realizado"]], dia_check)
    
    produtos = loja - serv + ecom
    
    print(f"\n   Dia {dia_check} ({DIAS_SEMANA_PT[dt.weekday()]}):")
    print(f"      Loja:     R$ {loja:>10,.2f}")
    print(f"      E-com:    R$ {ecom:>10,.2f}")
    print(f"      Serviços: R$ {serv:>10,.2f}")
    print(f"      Total:    R$ {produtos:>10,.2f}")

print("\n✅ Debug concluído!")
