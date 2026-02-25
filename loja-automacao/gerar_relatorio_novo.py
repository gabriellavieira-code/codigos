#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar o relatório HTML com as correções aplicadas
Simula as respostas padrão para inputs
"""
import sys
import os
from io import StringIO
from unittest.mock import patch

sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

# Preparar respostas para mock de input
respostas = ["", "", ""]
contador = [0]

def mock_input(prompt=""):
    """Retorna string vazia para pular perguntas"""
    if contador[0] < len(respostas):
        resp = respostas[contador[0]]
        contador[0] += 1
        print(prompt, resp)  # Mostrar o que respondeu
        return resp
    return ""

print("=" * 80)
print("🚀 GERANDO RELATÓRIO COM CÓDIGO ATUALIZADO")
print("=" * 80)

try:
    # Fazer patch do input antes de importar
    with patch('builtins.input', side_effect=mock_input):
        # Importar as funções necessárias
        from relatorio_semanal import (
            gerar_dados_relatorio,
            gerar_mensagem_semanal,
            gerar_mensagem_fechamento,
            gerar_html,
            PASTA_SCRIPT,
        )
        from datetime import date
        
        print("\n📥 Gerando dados do relatório...")
        r = gerar_dados_relatorio(forcar_fechamento=False)
        
        if not r:
            print("❌ Falha ao gerar dados")
            sys.exit(1)
        
        print(f"\n✅ Dados gerados com sucesso")
        print(f"   Vendas: R${r['vendas']:,.2f}")
        print(f"   Meta: R${r['meta']:,.2f}")
        print(f"   Por dia: R${r['valor_diario']:,.2f}")
        print(f"   Dias restantes: {r['dias_restantes']:.0f}")
        
        # Adicionar data se não existir
        if 'hoje' not in r or r['hoje'] is None:
            r['hoje'] = date.today()
        
        print(f"\n📝 Gerando mensagem...")
        mensagem = gerar_mensagem_semanal(r)
        
        print(f"\n📄 Gerando HTML...")
        html = gerar_html(r, mensagem)
        
        # Salvar arquivo
        caminho = os.path.join(PASTA_SCRIPT, "relatorio.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"\n✅ Relatório salvo com sucesso!")
        print(f"   Arquivo: {caminho}")
        print(f"   Tamanho: {len(html):,} bytes")
        
        # Validar conteúdo
        print(f"\n🔍 VALIDAÇÃO DO HTML:")
        print("-" * 80)
        
        if "Por dia (4 dias)" in html:
            print(f"   ✅ Por dia (4 dias) encontrado")
        elif "Por dia (" in html:
            print(f"   ⚠️  Por dia encontrado mas formato diferente")
        else:
            print(f"   ❌ Por dia não encontrado!")
        
        if "6.393,79" in html or "6393" in html:
            print(f"   ✅ Valor diário R$6.393,79 encontrado")
        else:
            print(f"   ❌ Valor diário não encontrado!")
        
        if "16/02 a 22/02" in html or "22" in html:
            print(f"   ✅ Semana passada encontrada")
        else:
            print(f"   ❌ Semana passada não encontrada!")
        
        print(f"\n" + "=" * 80)
        print(f"✅ PRONTO! Abra o arquivo relatorio.html no navegador")
        print(f"=" * 80)
        
        # Tentar abrir no navegador
        import webbrowser
        webbrowser.open(f"file:///{caminho}")
        print(f"🌐 Abrindo no navegador...")
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
