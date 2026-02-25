import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO
SHEET_ID = "1oEHfYvcQiNMNgCW-N_RLZ1bRY7UjBSLrPDT8yCED5ZE"

def precisa_mensagem_simples(pendencias):
    """
    Verifica se deve enviar mensagem simples (sem checklist)
    """
    # Se está vazio ou NaN
    if pd.isna(pendencias) or not str(pendencias).strip():
        return True
    
    # Se é exatamente "Mensagem da semana - alinhamento" (ignora maiúsculas/minúsculas)
    texto = str(pendencias).strip().lower()
    if texto in ['mensagem da semana - alinhamento', 
                 'mensagem da semana', 
                 'alinhamento',
                 'mensagem simples']:
        return True
    
    return False

def criar_checklist(pendencias_raw):
    """Transforma pendências em checklist"""
    pendencias_raw = str(pendencias_raw)
    
    if '\n' in pendencias_raw:
        linhas = pendencias_raw.split('\n')
    else:
        pendencias_raw = pendencias_raw.replace('. ', '\n').replace(', ', '\n')
        linhas = pendencias_raw.split('\n')
    
    checklist = ""
    for linha in linhas:
        linha = linha.strip()
        if linha and linha.lower() != 'nan':
            if linha.startswith('-'):
                linha = linha[1:].strip()
            if linha.endswith('.'):
                linha = linha[:-1]
            checklist += f"☑️ {linha}\n"
    
    return checklist.strip()

def criar_mensagem(nome, pendencias):
    """
    Cria a mensagem personalizada
    Detecta se deve ser mensagem simples ou com checklist
    """
    # Verificar se precisa mensagem simples
    if precisa_mensagem_simples(pendencias):
        # MENSAGEM SIMPLES
        mensagem = f"""Olá, {nome}! Bom dia! 😊

Passando para desejar uma ótima semana e verificar se precisam de algo.

Estou à disposição para qualquer dúvida ou demanda!

Vamos juntos! 🚀"""
    else:
        # MENSAGEM COM CHECKLIST
        checklist = criar_checklist(pendencias)
        mensagem = f"""Olá, {nome}! Bom dia! 😊

Espero que tenha uma ótima semana!

Segue nossos alinhamentos:

{checklist}

Qualquer dúvida ou informação, só me chamar.

Vamos juntos! 🚀"""
    
    return mensagem

def gerar_html(clientes):
    """Gera página HTML com todas as mensagens"""
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mensagens de Segunda-feira</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; min-height: 100vh; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ background: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.2); }}
        .header h1 {{ color: #667eea; font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ color: #666; font-size: 1.1em; }}
        .message-card {{ background: white; padding: 30px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 5px 20px rgba(0,0,0,0.2); transition: transform 0.3s ease; }}
        .message-card:hover {{ transform: translateY(-5px); }}
        .client-name {{ color: #667eea; font-size: 1.8em; font-weight: bold; margin-bottom: 10px; }}
        .group-name {{ color: #999; font-size: 1em; margin-bottom: 20px; font-style: italic; }}
        .message-type {{ display: inline-block; background: #4caf50; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; }}
        .message-type-simple {{ background: #ff9800; }}
        .message-preview {{ background: #25D366; color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .message-content {{ background: white; color: #333; padding: 20px; border-radius: 10px; white-space: pre-line; line-height: 1.8; font-size: 1.05em; margin-bottom: 15px; }}
        .copy-button {{ background: #667eea; color: white; border: none; padding: 15px 30px; border-radius: 8px; font-size: 1.1em; font-weight: bold; cursor: pointer; transition: all 0.3s ease; width: 100%; }}
        .copy-button:hover {{ background: #5568d3; transform: scale(1.02); }}
        .copied {{ background: #4caf50 !important; }}
        .instructions {{ background: #fff9e6; border-left: 5px solid #ffd700; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .instructions h3 {{ color: #f57c00; margin-bottom: 15px; }}
        .instructions ol {{ margin-left: 20px; line-height: 2; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Mensagens de Segunda-feira</h1>
            <p>Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>
        </div>
        
        <div class="instructions">
            <h3>💡 Como usar:</h3>
            <ol>
                <li>Clique no botão "COPIAR MENSAGEM" abaixo de cada cliente</li>
                <li>Abra o grupo correspondente no WhatsApp</li>
                <li>Cole a mensagem (Ctrl+V ou Cmd+V)</li>
                <li>Envie! 🚀</li>
            </ol>
            <p style="margin-top: 15px; color: #666;"><strong>Dica:</strong> Abra o WhatsApp Web em outra aba para ir mais rápido!</p>
        </div>
"""
    
    # Adicionar card para cada cliente
    for _, cliente in clientes.iterrows():
        mensagem = criar_mensagem(cliente['nome'], cliente['pendencias'])
        grupo = cliente.get('grupo_whatsapp', 'Grupo não especificado')
        
        # Detectar tipo de mensagem para label
        is_simple = precisa_mensagem_simples(cliente['pendencias'])
        tipo_label = "Mensagem Simples" if is_simple else "Mensagem com Pendências"
        tipo_class = "message-type-simple" if is_simple else "message-type"
        
        msg_escaped = mensagem.replace('`', '\\`').replace('$', '\\$')
        
        html += f"""
        <div class="message-card">
            <div class="client-name">{cliente['nome']}</div>
            <div class="group-name">📱 {grupo}</div>
            <span class="{tipo_class}">{tipo_label}</span>
            <div class="message-preview">
                <div class="message-content">{mensagem}</div>
                <button class="copy-button" onclick="copyMessage(this, `{msg_escaped}`)">
                    COPIAR MENSAGEM
                </button>
            </div>
        </div>
"""
    
    html += """
    </div>
    <script>
        function copyMessage(button, text) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = button.textContent;
                button.textContent = '✅ COPIADO!';
                button.classList.add('copied');
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }, 2000);
            });
        }
    </script>
</body>
</html>"""
    return html

def main():
    print("=" * 60)
    print("🚀 GERADOR DE MENSAGENS PARA GRUPOS (v2)")
    print("=" * 60)
    print()
    
    if SHEET_ID == "COLE_SEU_ID_AQUI":
        print("❌ ERRO: Configure o ID da planilha!")
        print("Edite a linha 5 do script e cole o ID.")
        return
    
    try:
        print("🔄 Carregando planilha do Google Sheets...")
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        clientes = pd.read_csv(url)
        print(f"✅ {len(clientes)} clientes carregados!")
        print()
        
        # Mostrar preview
        simples = sum(1 for _, c in clientes.iterrows() if precisa_mensagem_simples(c['pendencias']))
        com_pendencias = len(clientes) - simples
        
        print(f"📊 Tipos de mensagem:")
        print(f"   • {com_pendencias} mensagens COM pendências")
        print(f"   • {simples} mensagens SIMPLES")
        print()
        
        print("📝 Gerando página HTML...")
        html = gerar_html(clientes)
        
        filename = f"mensagens_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Arquivo: {filename}")
        print()
        print("🎉 PRONTO!")
        print(f"   1. Abra '{filename}' no navegador")
        print("   2. Clique em 'COPIAR' para cada cliente")
        print("   3. Cole no grupo do WhatsApp")
        print()
        print("💡 Dica: Mensagens simples têm label LARANJA")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print()
        print("Verifique se:")
        print("- A planilha está compartilhada como 'Qualquer pessoa com o link'")
        print("- O ID está correto")
        print("- Você tem conexão com internet")

if __name__ == "__main__":
    main()
