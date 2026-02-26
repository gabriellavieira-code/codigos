"""
Debug: Ver quais dias foram preenchidos em fevereiro
"""
import sys
sys.path.insert(0, r"C:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao")

from relatorio_semanal import *
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import calendar

# Carregar planilha
creds = Credentials.from_service_account_file(
    r"C:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao\credentials\service_account.json"
)
gc = gspread.authorize(creds)
planilha = gc.open_by_key("1prgwX-C8v4cGFpRjVEDxAW2QRddlB_gvl8x1E0AK0CU")

abas = [sh.title for sh in planilha.worksheets()]
mes = 2
ano = 2026

print(f"=== DIAS PREENCHIDOS EM FEVEREIRO 2026 ===\n")

dados = ler_vendas(planilha, abas, mes, ano)
if dados:
    dias_diarios = extrair_vendas_diarias(dados["dados_brutos"], dados["linhas_detectadas"], mes, ano)
    
    print(f"Total de dias com vendas: {len(dias_diarios)}\n")
    
    print("Dias preenchidos:")
    for d in dias_diarios:
        print(f"  Dia {d['dia']:02d}: {d['dia_semana_nome']} - R${d['total']:,.2f}")
    
    print(f"\nÚltimo dia preenchido: {dias_diarios[-1]['dia'] if dias_diarios else 'Nenhum'}")
    
    print("\n=== CÁLCULO DE DIAS RESTANTES ===\n")
    
    hoje = date.today()
    print(f"Data de hoje: {hoje.day:02d}/{hoje.month:02d}/{hoje.year}")
    print(f"Dia atual preenchido? {any(d['dia'] == hoje.day for d in dias_diarios)}")
    
    dias_rest = contar_dias_restantes(ano, mes, hoje.day, dias_diarios)
    print(f"Dias restantes: {dias_rest}")
    
    # Mostrar manualmente quais dias deveriam contar
    print(f"\nDias úteis de {hoje.day:02d} a 28 de fevereiro:")
    feriados = get_feriados(ano)
    meios = get_meios_periodos(ano)
    
    for dia in range(hoje.day, 29):
        dt = date(ano, mes, dia)
        eh_domingo = dt.weekday() == 6
        eh_feriado = (dia, mes) in feriados
        eh_meio = (dia, mes) in meios
        
        preenchido = any(d['dia'] == dia for d in dias_diarios)
        
        status = []
        if eh_domingo:
            status.append("domingo")
        if eh_feriado:
            status.append("feriado")
        if eh_meio:
            status.append("meio período")
        if preenchido:
            status.append("preenchido")
        
        contável = not eh_domingo and not eh_feriado
        
        print(f"  {dia:02d}: {dt.strftime('%A')[:3]:3s} - Contável: {contável} - {', '.join(status) if status else 'normal'}")
