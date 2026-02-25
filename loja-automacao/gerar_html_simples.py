#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from unittest.mock import patch

sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

respostas = ["", "", ""]
contador = [0]

def mock_input(prompt=""):
    if contador[0] < len(respostas):
        resp = respostas[contador[0]]
        contador[0] += 1
        return resp
    return ""

try:
    with patch('builtins.input', side_effect=mock_input):
        from relatorio_semanal import (
            gerar_dados_relatorio,
            gerar_mensagem_semanal,
            gerar_html,
            PASTA_SCRIPT,
        )
        from datetime import date
        
        print("Gerando dados do relatorio...")
        r = gerar_dados_relatorio(forcar_fechamento=False)
        
        if not r:
            print("ERRO: Falha ao gerar dados")
            sys.exit(1)
        
        print(f"OK: Dados gerados")
        print(f"   Valor diario: R${r['valor_diario']:,.2f}")
        print(f"   Dias restantes: {r['dias_restantes']:.0f}")
        
        if 'hoje' not in r or r['hoje'] is None:
            r['hoje'] = date.today()
        
        print(f"Gerando mensagem...")
        mensagem = gerar_mensagem_semanal(r)
        
        print(f"Gerando HTML...")
        html = gerar_html(r, mensagem)
        
        caminho = os.path.join(PASTA_SCRIPT, "relatorio.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"OK: Relatorio salvo em {caminho}")
        
        # Validar conteudo
        if "Por dia (4 dias)" in html:
            print(f"OK: 'Por dia (4 dias)' encontrado no HTML")
        elif "Por dia (" in html:
            print(f"AVISO: 'Por dia' encontrado mas com diferenca:")
            # Procurar o padrão
            import re
            match = re.search(r'Por dia \(([^)]+) dias\)', html)
            if match:
                print(f"       Encontround: Por dia ({match.group(1)} dias)")
        
        if "6.393" in html or "6393" in html:
            print(f"OK: Valor diario R$6.393,79 encontrado no HTML")
        else:
            print(f"ERRO: Valor diario NAO encontrado!")
            if "R$0,00" in html and "Por dia" in html:
                print(f"      Ainda tem R$0,00 no 'Por dia'!")
        
        print(f"\nHTML pronto para visualizar em: {caminho}")
        
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
