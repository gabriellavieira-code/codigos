"""
Debug: Verificar se sv (Esta Semana) está sendo retornado
"""
from datetime import date
from relatorio_semanal import (
    conectar, carregar_abas_disponiveis, analise_semana_que_vem,
    NOMES_MESES
)

hoje = date.today()
mes, ano = hoje.month, hoje.year

planilha = conectar()
abas = carregar_abas_disponiveis(planilha)

sv = analise_semana_que_vem(planilha, abas, hoje)

print(f"Data hoje: {hoje} ({['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom'][hoje.weekday()]})")
print(f"\nResultado de analise_semana_que_vem:")
if sv:
    print(f"  ✅ Retornou dados!")
    print(f"  Início: {sv['inicio']}")
    print(f"  Fim: {sv['fim']}")
    print(f"  Vendas ano passado: R$ {sv['vendas_ano_passado']:,.2f}")
else:
    print(f"  ❌ Retornou None")

print("\n✅ Debug concluído!")
