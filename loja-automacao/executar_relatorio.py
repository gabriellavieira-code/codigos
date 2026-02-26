#!/usr/bin/env python3
"""
Executar relatorio_semanal.py automaticamente sem inputs
Simula respostas padrão para as perguntas interativas
"""
import sys
import os
from unittest.mock import patch
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🚀 EXECUTANDO relatorio_semanal.py COM CÓDIGO ATUALIZADO")
print("=" * 80)

try:
    # Simular inputs vazios (ENTER) para pular as perguntas
    mock_input_responses = [
        "",  # "Houve algum dia EXTRA?"
        "",  # "Quer registrar ausência?"
        "",  # Qualquer outra pergunta
    ]
    
    input_iter = iter(mock_input_responses)
    
    def mock_input_func(prompt=""):
        """Mock do input() que retorna strings vazias"""
        try:
            return next(input_iter)
        except StopIteration:
            return ""
    
    print("\n⏳ Executando relatorio_semanal.py...")
    print("   (Respondendo automaticamente com ENTER)\n")
    
    # Patch do input
    with patch('builtins.input', side_effect=mock_input_func):
        # Importar e executar main
        from relatorio_semanal import main
        main()
    
    print("\n" + "=" * 80)
    print("✅ RELATÓRIO GERADO COM SUCESSO!")
    print("=" * 80)
    
    # Verificar se o arquivo foi criado
    relatorio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'relatorio.html')
    
    if os.path.exists(relatorio_path):
        tamanho = os.path.getsize(relatorio_path)
        print(f"\n📄 Arquivo: relatorio.html")
        print(f"   Tamanho: {tamanho:,} bytes")
        print(f"   Local: {relatorio_path}")
        
        # Verificar se contém os valores corretos
        with open(relatorio_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        print(f"\n🔍 VALIDAÇÃO DO HTML:")
        
        if "Por dia (4 dias)" in conteudo:
            print(f"   ✅ 'Por dia (4 dias)' encontrado")
        else:
            print(f"   ❌ 'Por dia (4 dias)' NÃO encontrado")
        
        if "R$6.393,79" in conteudo or "R$ 6.393,79" in conteudo or "6393" in conteudo:
            print(f"   ✅ Valor diário (R$6.393,79) encontrado")
        else:
            print(f"   ❌ Valor diário NÃO encontrado")
        
        if "16/02 a 22/02" in conteudo or "22/02" in conteudo:
            print(f"   ✅ Semana passada (16/02 a 22/02) encontrada")
        else:
            print(f"   ❌ Semana passada NÃO encontrada corretamente")
        
        if "✅" in conteudo:
            print(f"   ✅ Checkmarks de contas pagas encontrados")
        else:
            print(f"   ⚠️ Checkmarks de contas pagas não encontrados (esperado se sem dados)")
        
        print(f"\n🌐 HTML salvo em: {relatorio_path}")
    else:
        print(f"⚠️ Arquivo relatorio.html não foi criado")
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
