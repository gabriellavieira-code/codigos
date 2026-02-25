#!/usr/bin/env python3
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from datetime import date
from relatorio_semanal import gerar_dados_relatorio, formatar_moeda

print("=" * 80)
print("🔍 TESTE: Gerar dados completos do relatório")
print("=" * 80)

try:
    # Gerar dados (vai pedir confirmações)
    r = gerar_dados_relatorio(forcar_fechamento=False)
    
    if not r:
        print("❌ Falha ao gerar dados")
        sys.exit(1)
    
    print(f"\n✅ Dados gerados com sucesso!")
    print(f"\n📊 VALORES NO DICIONÁRIO 'r':")
    print("-" * 80)
    print(f"  'dias_restantes': {r.get('dias_restantes', 'NÃO ENCONTRADO')}")
    print(f"  'valor_diario': {r.get('valor_diario', 'NÃO ENCONTRADO')}")
    
    if 'dias_restantes' in r and 'valor_diario' in r:
        print(f"\n✅ Valores encontrados no dicionário!")
        print(f"   Dias: {r['dias_restantes']:.1f}")
        print(f"   Valor por dia: {formatar_moeda(r['valor_diario'])}")
    else:
        print(f"\n❌ PROBLEMA: Valores não estão no dicionário!")
        print(f"   Chaves disponíveis:")
        for k in sorted(r.keys()):
            print(f"      - {k}")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
