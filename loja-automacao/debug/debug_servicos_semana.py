"""
Debug: Validar dados de serviços para semana 16/02-22/02
"""
import sys
sys.path.insert(0, r"C:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao")

from servicos_analise import *
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# Carregar dados - usar mesmo caminhos do relatorio_semanal.py
creds = Credentials.from_service_account_file(
    r"C:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao\credentials\service_account.json"
)
gc = gspread.authorize(creds)

# ID da planilha de serviços
PLANILHA_SERVICOS_ID = "1Q8hqrDXlN5yDzYi11pCwkOTnqLPaFHXYdBbVYMDI6Ck"

try:
    planilha = gc.open_by_key(PLANILHA_SERVICOS_ID)
except Exception as e:
    print(f"Erro ao abrir planilha: {e}")
    print(f"ID usado: {PLANILHA_SERVICOS_ID}")
    exit(1)

# Gerar análise
hoje = date.today()
ana = gerar_analise_servicos(planilha, mes=2, ano=2026, hoje=hoje)

if ana:
    print("=== RESUMO DA SEMANA 16/02-22/02 ===\n")
    
    rs = ana.get("resumo_semana")
    if rs:
        print(f"Período: {rs['inicio']} a {rs['fim']}")
        print(f"Total Atendimentos: {rs['atendimentos']}")
        print(f"  - Pagaram Sobrancelha: {rs['qtd_servico']}")
        print(f"    Receita: R${rs['receita_servico']:,.2f}")
        print(f"    Ticket médio: R${rs['ticket_servico']:,.2f}")
        print(f"  - Compraram Produto: {rs['qtd_compras']}")
        print(f"    Receita: R${rs['receita_compras']:,.2f}")
        print(f"    Ticket médio: R${rs['ticket_compra']:,.2f}")
    else:
        print("Nenhum resumo de semana encontrado")
    
    # Mostrar dados brutos da semana
    print("\n=== DADOS BRUTOS DE ATENDIMENTOS (16/02-22/02) ===\n")
    
    # Precisamos acessar os atendimentos diretamente
    from servicos_analise import ler_atendimentos_aba, NOMES_MESES
    
    nome_aba = f"{NOMES_MESES[2].upper()}{2026}"
    print(f"Lendo aba: {nome_aba}\n")
    
    try:
        atendimentos = ler_atendimentos_aba(planilha, nome_aba)
        
        # Filtrar semana
        from datetime import date
        semana_inicio = date(2026, 2, 16)
        semana_fim = date(2026, 2, 22)
        
        atend_semana = [a for a in atendimentos if semana_inicio <= a["data"] <= semana_fim]
        
        print(f"Total de atendimentos na semana: {len(atend_semana)}\n")
        
        for i, a in enumerate(atend_semana, 1):
            print(f"{i}. {a['data'].strftime('%a %d/%m')}")
            print(f"   Cliente: {a['cliente'][:30] if 'cliente' in a and a['cliente'] else 'N/A'}")
            print(f"   Tipo: {a['tipo']}")
            print(f"   Valor: R${a['valor']:,.2f}")
            if 'forma_pagamento' in a:
                print(f"   Forma: {a['forma_pagamento']}")
            print()
        
        # Contar por tipo
        from collections import Counter
        tipos_count = Counter(a['tipo'] for a in atend_semana)
        
        print("\n=== RESUMO POR TIPO ===\n")
        for tipo, count in tipos_count.items():
            total = sum(a['valor'] for a in atend_semana if a['tipo'] == tipo)
            print(f"{tipo}: {count} atendimentos = R${total:,.2f}")
        
    except Exception as e:
        print(f"Erro ao ler atendimentos: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Erro ao gerar análise de serviços")
