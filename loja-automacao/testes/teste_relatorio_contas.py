#!/usr/bin/env python3
"""Script para testar se as contas pagas aparecem no relatório."""

import sys
sys.path.insert(0, '.')

from financeiro_analise import carregar_financeiro

# Carregar dados financeiros
fin, erro = carregar_financeiro()
if not fin:
    print(f"Erro: {erro}")
    sys.exit(1)

# Extrair semana
semana = fin.get("semana", {})
print(f"📊 Semana carregada: {semana.get('inicio')} a {semana.get('fim')}")
print(f"✅ Total a pagar: R${semana.get('total_semana', 0):,.2f}")
print(f"✅ Total pagas: R${semana.get('total_pagas', 0):,.2f}")
print()

# Mostrar dias da semana
for d in semana.get("dias", []):
    print(f"🗓️  {d['nome_dia']} {d['data'].strftime('%d/%m')}")
    
    # Contas a pagar
    if d.get("contas"):
        print(f"  Contas pendentes ({len(d['contas'])}):")
        for c in d["contas"]:
            print(f"    - {c['descricao'][:40]}: R${c['valor']:,.2f}")
    else:
        print(f"  Contas pendentes: ZERADO")
    
    # Contas pagas
    if d.get("pagas"):
        total_pagas_dia = sum(c["valor"] for c in d["pagas"])
        print(f"  ✅ Contas já pagas ({len(d['pagas'])}): R${total_pagas_dia:,.2f}")
        for c in d["pagas"]:
            print(f"    ✓ {c['descricao'][:40]}: R${c['valor']:,.2f}")
    
    print()
