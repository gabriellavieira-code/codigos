"""
Gerar relatório sem interação do usuário
"""
import sys
import os
from io import StringIO
from datetime import date

# Redirecionar input para retornar vazio (skip nas prompts)
class EmptyInput:
    def __call__(self, *args, **kwargs):
        return ""

original_input = __builtins__.input
__builtins__.input = EmptyInput()

from relatorio_semanal import gerar_dados_relatorio, gerar_html, gerar_mensagem_semanal, PASTA_SCRIPT
import webbrowser

try:
    print("=" * 55)
    print("  🌿 BEM ME QUER — RELATÓRIO DE VENDAS")
    print("=" * 55)
    print()

    r = gerar_dados_relatorio(forcar_fechamento=False)
    
    if not r:
        print("❌ Não foi possível gerar o relatório.")
        sys.exit(1)

    r['hoje'] = date.today()
    mensagem = gerar_mensagem_semanal(r)
    html = gerar_html(r, mensagem)

    caminho = os.path.join(PASTA_SCRIPT, "relatorio.html")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)

    print()
    print(f"✅ Relatório salvo: {caminho}")
    print("🌐 Abrindo no navegador...")
    webbrowser.open(f"file:///{caminho}")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()

finally:
    __builtins__.input = original_input
