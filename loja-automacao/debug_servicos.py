"""
Debug: Verificar dados de serviços (sobrancelha) semana 16/02 a 22/02
"""
from datetime import date
from relatorio_semanal import conectar_servicos, gerar_analise_servicos, NOMES_MESES

hoje = date.today()
mes, ano = hoje.month, hoje.year

try:
    planilha_servicos, abas_servicos = conectar_servicos("credentials/service_account.json")
    
    print("=" * 70)
    print("🔍 VERIFICANDO DADOS DE SERVIÇOS: Semana 16/02 a 22/02")
    print("=" * 70)
    
    # Calcular semana passada
    from datetime import timedelta
    semana_passada_inicio = date(2026, 2, 16)
    semana_passada_fim = date(2026, 2, 22)
    
    print(f"\n📊 Analisando semana: {semana_passada_inicio} a {semana_passada_fim}")
    print(f"Abas disponíveis: {abas_servicos}\n")
    
    analise = gerar_analise_servicos(
        planilha_servicos, mes, ano, abas_servicos,
        semana_inicio=semana_passada_inicio,
        semana_fim=semana_passada_fim
    )
    
    if analise:
        print(f"✅ Análise retornou dados:")
        print(f"   Total atendimentos: {analise.get('total_atendimentos', 'N/A')}")
        print(f"   Receita total: R$ {analise.get('receita_total', 0):,.2f}")
        print(f"   Lucro: R$ {analise.get('lucro', 0):,.2f}")
        
        if 'detalhes_por_semana' in analise:
            print(f"\n   Detalhes por semana:")
            for semana, dados in analise['detalhes_por_semana'].items():
                print(f"      {semana}: {dados}")
    else:
        print(f"❌ Análise retornou None")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Debug concluído!")
