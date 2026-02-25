#!/usr/bin/env python3
"""Teste simulando contas pagas na segunda-feira."""

import sys
sys.path.insert(0, '.')

from financeiro_analise import carregar_financeiro
from datetime import date

# Carregar financeiro
fin, erro = carregar_financeiro()
if not fin:
    print(f"❌ Erro: {erro}")
    sys.exit(1)

semana = fin.get("semana", {})

print("=" * 80)
print("📊 SIMULANDO CONTAS PAGAS NA SEGUNDA-FEIRA")
print("=" * 80)

# Verificar segunda-feira
seg = semana.get("dias", [])[0] if semana.get("dias") else {}
print(f"\n🗓️  {seg.get('nome_dia')} {seg.get('data')}")
print(f"   Contas a pagar: {len(seg.get('contas', []))}")
print(f"   Contas PAGAS:   {len(seg.get('pagas', []))}")

if seg.get('pagas'):
    print("\n✅ CONTAS PAGAS ENCONTRADAS:")
    for c in seg.get('pagas', []):
        print(f"   ✓ {c['descricao'][:40]}: R${c['valor']:,.2f}")
else:
    print("\n⚠️  Nenhuma conta paga na segunda (esperado)")
    print("   Quando você ADD contas com status 'Pago'/'Realizado', aparecerão aqui!")

print("\n" + "=" * 80)
print("📝 ESTRUTURA PRONTA PARA QUE VOCÊ TESTE:")
print("=" * 80)
print("""
1. Abra a planilha: ok(BMQ 2025) - GESTÃO FINANCEIRA.xlsx
2. Vá para a aba LP
3. Adicione uma linha com:
   - Col C (Descrição): Depósito Fornecedor X
   - Col 7 (Data Pag): 23/02/2026
   - Col 8 (Status): Pago (ou Realizado, Paga, Liquidado)
   - Col 10 (Valor): 3000
4. Salve a planilha
5. Rode: python teste_render_html.py
6. Abra relatorio_teste.html no navegador
7. SEGUNDA-FEIRA 23/02 agora mostrará:
   
   ┌─ SEGUNDA-FEIRA 23/02 ────────────── R$3.000,00 ──┐
   │  ✅ Depósito Fornecedor X         R$3.000,00      │
   │  ✅ +R$3.000,00                                   │
   │  Caixa antes: R$7.928,15 → Caixa após: R$10.928,15
   └──────────────────────────────────────────────────┘
""")
print("=" * 80)
