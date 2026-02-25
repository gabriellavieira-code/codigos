#!/usr/bin/env python3
"""Teste da mensagem WhatsApp com contas pagas."""

import sys
sys.path.insert(0, '.')

from financeiro_analise import carregar_financeiro

# Carregar dados financeiros
fin, erro = carregar_financeiro()
if not fin:
    print(f"❌ Erro: {erro}")
    sys.exit(1)

# Extrair mensagem
msg = fin.get("mensagem_wpp", "")

if msg:
    print("=" * 70)
    print("📱 MENSAGEM WHATSAPP GERADA:")
    print("=" * 70)
    print(msg)
    print("=" * 70)
    
    # Verificar se contas pagas aparecem
    if "✅ *JÁ PAGO:*" in msg:
        print("\n✅ Contas pagas APARECEM na mensagem!")
    else:
        print("\n⚠️  Contas pagas NÃO aparecem (esperado - planilha tem R$0 pagas)")
        print("   Quando você marcar contas como 'Pago'/'Realizado', aparecerão aqui.")
else:
    print("❌ Mensagem não foi gerada")
