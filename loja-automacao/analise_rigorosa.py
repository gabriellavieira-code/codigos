#!/usr/bin/env python3
"""
ANÁLISE RIGOROSA: Verificar se todos os fornecedores caem no mesmo dia
Simula os prazos dos fornecedores atuais e mostra EXATAMENTE onde será o pico
"""

from datetime import date, timedelta
from fornecedores_mes import FORNECEDORES_MES

hoje = date.today()
print(f"🚀 ANÁLISE RIGOROSA DE PRAZOS")
print(f"Data atual: {hoje.strftime('%d/%m/%Y (%A)')}")
print("=" * 80)

# Simular prazos
prazos_por_data = {}
fornecedores_simulacao = []

for f in FORNECEDORES_MES:
    nome = f['nome']
    prazos = f['prazos']
    
    print(f"\n📦 {nome}")
    print(f"   Prazos disponíveis: {'/'.join(str(p) for p in prazos)} dias")
    
    # Calcular onde cada prazo vence
    datas_vencimento = []
    for p in prazos:
        d = hoje + timedelta(days=p)
        # Pula fim de semana
        while d.weekday() >= 5:
            d += timedelta(days=1)
        
        datas_vencimento.append({
            "prazo": p,
            "data": d,
            "dia": ['Seg','Ter','Qua','Qui','Sex','Sab','Dom'][d.weekday()],
            "semana": f"Semana {d.isocalendar()[1]}"
        })
        
        # Registrar
        if d not in prazos_por_data:
            prazos_por_data[d] = []
        prazos_por_data[d].append(nome)
        
        print(f"      {p}d: {d.strftime('%d/%m/%Y')} ({['Seg','Ter','Qua','Qui','Sex','Sab','Dom'][d.weekday()]})")
    
    fornecedores_simulacao.append({
        "nome": nome,
        "prazos_opcoes": datas_vencimento
    })

print("\n" + "=" * 80)
print("🔍 DETECÇÃO DE PICOS\n")

todos_mesmo_dia = len(prazos_por_data) == 1
if todos_mesmo_dia:
    data_unica = list(prazos_por_data.keys())[0]
    fornecedores = prazos_por_data[data_unica]
    print(f"🚨 PROBLEMA CRÍTICO DETECTADO!")
    print(f"   TODOS os prazos caem no MESMO DIA: {data_unica.strftime('%d/%m/%Y (%A)')}")
    print(f"   Fornecedores: {', '.join(fornecedores)}")
    print(f"\n   ⚠️  IMPACTO: Semana inteira com MÚLTIPLOS vencimentos = RISCO ALTO de problemas")
else:
    print("📊 Distribuição por data:")
    for data in sorted(prazos_por_data.keys()):
        forts = prazos_por_data[data]
        print(f"   {data.strftime('%d/%m')} ({['Seg','Ter','Qua','Qui','Sex','Sab','Dom'][data.weekday()]}): {len(forts)} fornecedor(es)")
        for f in forts:
            print(f"      • {f}")

print("\n" + "=" * 80)
print("💡 RECOMENDAÇÕES RIGOROSAS\n")

if todos_mesmo_dia:
    print("Como TODOS vencimentos caem no mesmo dia, você DEVE fazer uma de 3 coisas:\n")
    
    forts = fornecedores_simulacao
    for i, f in enumerate(forts, 1):
        print(f"{i}. FORNECEDOR: {f['nome']}")
        print(f"   Opção A: Negocie prazo DIFERENTE (ex: 45 em vez de 60 dias)")
        print(f"   Opção B: Adie a liberação do pedido em 1-2 semanas")
        print(f"   Opção C: Reduza o valor do pedido (menor folego de estoque)")
        datas = f["prazos_opcoes"]
        if len(datas) > 1:
            datas_str = ', '.join(f"{d['prazo']}d = {d['data'].strftime('%d/%m')}" for d in datas)
            print(f"   Datas se negociar: {datas_str}")
        print()

else:
    print("✅ Prazos estão distribuídos em múltiplas datas (BOM SINAL)")
    print("   Mas verifique AINDA SE há picos de carga na semana:")
    for data, forts in sorted(prazos_por_data.items()):
        if len(forts) > 1:
            print(f"   ⚠️  {data.strftime('%d/%m')}: {len(forts)} fornecedores juntos = CONSIDERE DISTRIBUIR")

print("\n" + "=" * 80)  
