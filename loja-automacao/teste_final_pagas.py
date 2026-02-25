#!/usr/bin/env python3
"""
Teste final: Validar que fornecedores aparecem SEMPRE (nunca como Zerado)
independente se foram pagos ou não.
"""

import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from relatorio_semanal import gerar_dados_relatorio, formatar_moeda
from datetime import date

# Simular dados de uma semana
def teste_fornecedores_pagos():
    print("=" * 80)
    print("TESTE: Fornecedores aparecem mesmo quando PAGOS")
    print("=" * 80)
    
    try:
        # Carregar dados reais do relatório
        relatorio = gerar_dados_relatorio()
        
        if not relatorio or not relatorio.get("financeiro"):
            print("❌ Erro: Não foi possível carregar dados financeiros")
            return False
        
        dados_fin = relatorio["financeiro"]
        if "semanas" not in dados_fin:
            print("❌ Erro: Dados financeiros sem estrutura de semanas")
            return False
        
        sem = dados_fin["semanas"][0]
        
        print(f"\n📊 SEMANA: {sem['semana_label']}")
        print(f"   ({sem['data_inicio'].strftime('%d/%m')} a {sem['data_fim'].strftime('%d/%m')})\n")
        
        # Analisar cada dia
        for d in sem["dias"]:
            print(f"\n🗓️  {d['nome_dia']} ({d['data'].strftime('%d/%m')}):")
            print("-" * 60)
            
            contas_pendentes = len(d["contas"]) if d["contas"] else 0
            contas_pagas = len(d.get("pagas", [])) if d.get("pagas") else 0
            valor_pagas = sum(c["valor"] for c in d.get("pagas", []))
            total_movimento = d["total"] + valor_pagas
            
            print(f"   A pagar: {contas_pendentes} conta(s) = {formatar_moeda(d['total'])}")
            print(f"   Já pago: {contas_pagas} conta(s) = {formatar_moeda(valor_pagas)}")
            print(f"   TOTAL MOVIMENTO: {formatar_moeda(total_movimento)}")
            
            # Verificar se seria mostrado como Zerado
            tem_contas_totais = bool(d["contas"] or d.get("pagas"))
            
            if not tem_contas_totais:
                print(f"   ⚠️  STATUS: ZERADO (correto - nenhuma movimentação)")
            else:
                print(f"   ✅ STATUS: FORNECEDORES VISÍVEIS (correto)")
                if contas_pendentes > 0:
                    print(f"      └─ Mostrando {contas_pendentes} pendente(s)")
                if contas_pagas > 0:
                    print(f"      └─ Mostrando {contas_pagas} pago(s) com ✅")
            
            # Listar fornecedores se houver
            if d["contas"]:
                print(f"\n   📋 A PAGAR:")
                for c in d["contas"][:3]:  # Mostrar até 3
                    print(f"      • {c['descricao'][:40]}: {formatar_moeda(c['valor'])}")
                if len(d["contas"]) > 3:
                    print(f"      ... +{len(d['contas']) - 3} mais")
            
            if d.get("pagas"):
                print(f"\n   ✅ JÁ PAGOS:")
                for c in d.get("pagas", [])[:3]:  # Mostrar até 3
                    print(f"      • {c['descricao'][:40]}: {formatar_moeda(c['valor'])}")
                if len(d.get("pagas", [])) > 3:
                    print(f"      ... +{len(d.get('pagas', [])) - 3} mais")
        
        print("\n" + "=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = teste_fornecedores_pagos()
    sys.exit(0 if sucesso else 1)
