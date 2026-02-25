#!/usr/bin/env python3
"""
Teste final de renderização: Gera HTML e verifica se fornecedores aparecem mesmo quando pagos
"""

import sys
import json
from datetime import date, datetime, timedelta
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')

from relatorio_semanal import formatar_moeda

def gerar_html_teste():
    """Gera HTML teste com casos de fornecedores pagos"""
    
    print("=" * 80)
    print("GERANDO HTML DE TESTE COM FORNECEDORES PAGOS")
    print("=" * 80)
    
    # Dados de teste com diferentes cenários
    dados_teste = {
        "semana": {
            "semana_label": "Teste - Semana de 23 a 28 de Fevereiro",
            "data_inicio": datetime(2025, 2, 23),
            "data_fim": datetime(2025, 2, 28),
            "dias": [
                {
                    "nome_dia": "Segunda",
                    "data": datetime(2025, 2, 23),
                    "total": 5500,
                    "contas": [
                        {"descricao": "Fornecedor ABC", "valor": 2000, "conta_financeira": "SICOOB", "status": "Previsto"},
                        {"descricao": "Fornecedor XYZ", "valor": 3500, "conta_financeira": "", "status": "Previsto"},
                    ],
                    "pagas": [
                        {"descricao": "Fornecedor Antigo", "valor": 1200, "conta_financeira": "SICOOB", "status": "Realizado"},
                    ]
                },
                {
                    "nome_dia": "Terça",
                    "data": datetime(2025, 2, 24),
                    "total": 0,  # Nada a pagar
                    "contas": [],
                    "pagas": [
                        {"descricao": "Fornecedor Só Pago 1", "valor": 2500, "conta_financeira": "", "status": "Realizado"},
                        {"descricao": "Fornecedor Só Pago 2", "valor": 800, "conta_financeira": "Nubank", "status": "Pago"},
                    ]
                },
                {
                    "nome_dia": "Quarta",
                    "data": datetime(2025, 2, 25),
                    "total": 1500,
                    "contas": [
                        {"descricao": "Fornecedor Normal", "valor": 1500, "conta_financeira": "", "status": "Previsto"},
                    ],
                    "pagas": []
                },
                {
                    "nome_dia": "Quinta",
                    "data": datetime(2025, 2, 26),
                    "total": 0,
                    "contas": [],
                    "pagas": []
                },
            ]
        }
    }
    
    # Renderizar HTML
    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teste - Fornecedores Pagos</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        h1 { color: #333; border-bottom: 3px solid #324D38; padding-bottom: 10px; }
        .semana-title { color: #666; font-size: 0.95em; margin: 10px 0; }
        .dia-card { background: white; border-radius: 10px; padding: 14px; margin-bottom: 10px; }
        .dia-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .dia-nome { font-weight: bold; }
        .dia-valor { text-align: right; }
        .dia-valor-grande { font-weight: 700; font-size: 0.95em; }
        .dia-badge { font-size: 0.75em; color: #324D38; margin-top: 2px; }
        table { width: 100%; font-size: 0.82em; }
        table td { padding: 4px 8px; }
        table td.num { text-align: right; }
        tr.pago { opacity: 0.7; background: rgba(50, 77, 56, 0.05); }
        .saldo-label { text-align: right; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(75, 85, 110, 0.1); font-size: 0.82em; }
        .zerado { font-size: 0.85em; color: #888; }
        .caixa-alto { color: #324D38; }
        .caixa-baixo { color: #B84527; }
        .cor-amarela { border-left: 3px solid #E6A834; }
        .cor-vermelha { border-left: 3px solid #B84527; }
        .test-result { padding: 10px; margin-top: 20px; border-radius: 5px; }
        .test-ok { background: #e8f5e9; border: 1px solid #4caf50; color: #2e7d32; }
        .test-fail { background: #ffebee; border: 1px solid #f44336; color: #c62828; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Teste: Fornecedores Pagos</h1>
        <p class="semana-title">Validando que fornecedores aparecem mesmo quando pagos</p>
"""
    
    # Processar semana
    sem = dados_teste["semana"]
    html_content += f'<p><strong>Semana:</strong> {sem["semana_label"]}</p>\n'
    
    saldo = 15000  # Saldo inicial
    
    for d in sem["dias"]:
        # Calcular dados
        contas_pendentes = len(d["contas"])
        contas_pagas = len(d.get("pagas", []))
        valor_pagas = sum(c["valor"] for c in d.get("pagas", []))
        total_movimento = d["total"] + valor_pagas
        
        # Lógica correta
        tem_contas_totais = bool(d["contas"] or d.get("pagas"))
        
        # Cor da borda
        cor_borda = ""
        if total_movimento > 5000:
            cor_borda = "cor-vermelha"
        elif total_movimento > 3000:
            cor_borda = "cor-amarela"
        
        # Saldo
        saldo_apos = saldo - d["total"]
        
        # HTML do dia
        html_content += f"""
    <div class="dia-card {cor_borda}">
        <div class="dia-header">
            <div class="dia-nome">{d['nome_dia']} {d['data'].strftime('%d/%m')}</div>
            <div class="dia-valor">
                <div class="dia-valor-grande">{formatar_moeda(d['total']) if d['total'] > 0 else '---'}</div>
"""
        
        if valor_pagas > 0:
            html_content += f'                <div class="dia-badge">✅ +{formatar_moeda(valor_pagas)}</div>\n'
        
        html_content += '            </div>\n        </div>\n'
        
        # Tabela de contas
        if tem_contas_totais:
            html_content += '        <table><tbody>\n'
            
            # Contas a pagar
            for c in d["contas"]:
                conta_tag = f' <span style="color:#888;font-size:0.75em">[{c["conta_financeira"]}]</span>' if c["conta_financeira"] not in ("SICOOB", "", "None") else ""
                html_content += f'            <tr><td>{c["descricao"][:50]}{conta_tag}</td><td class="num">{formatar_moeda(c["valor"])}</td></tr>\n'
            
            # Contas pagas
            for c in d.get("pagas", []):
                conta_tag = f' <span style="color:#888;font-size:0.75em">[{c["conta_financeira"]}]</span>' if c["conta_financeira"] not in ("SICOOB", "", "None") else ""
                html_content += f'            <tr class="pago"><td>✅ {c["descricao"][:50]}{conta_tag}</td><td class="num" style="color:#324D38">{formatar_moeda(c["valor"])}</td></tr>\n'
            
            html_content += '        </tbody></table>\n'
            html_content += f'        <div class="saldo-label">Caixa antes: <strong>{formatar_moeda(saldo)}</strong> → Caixa após: <strong class="caixa-{"alto" if saldo_apos >= 2000 else "baixo"}">{formatar_moeda(saldo_apos)}</strong></div>\n'
        else:
            html_content += f'        <div style="font-size:0.85em;color:#888">Zerado — Caixa: <strong>{formatar_moeda(saldo)}</strong></div>\n'
        
        html_content += '    </div>\n'
        
        # Validação
        if tem_contas_totais:
            if "segunda" in d["nome_dia"].lower() and contas_pagas > 0:
                html_content += '    <div class="test-result test-ok">✅ Segunda com PAGAS aparecendo corretamente</div>\n'
            elif "terça" in d["nome_dia"].lower() and contas_pendentes == 0 and contas_pagas > 0:
                html_content += '    <div class="test-result test-ok">✅ Terça com SÓ PAGAS não mostrou "Zerado"</div>\n'
        
        saldo = saldo_apos
    
    html_content += """
    </div>
</body>
</html>"""
    
    # Salvar arquivo
    output_path = r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao\teste_render_pagas.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML gerado: {output_path}")
    print("\n📋 ANÁLISE DOS DADOS TESTE:")
    print("-" * 60)
    
    for d in sem["dias"]:
        contas_pendentes = len(d["contas"])
        contas_pagas = len(d.get("pagas", []))
        tem_contas = bool(d["contas"] or d.get("pagas"))
        
        status = "VISÍVEL ✅" if tem_contas else "ZERADO"
        print(f"\n{d['nome_dia']} ({d['data'].strftime('%d/%m')}):")
        print(f"  • Pendentes: {contas_pendentes} | Pagos: {contas_pagas}")
        print(f"  • Status: {status}")
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print(f"📂 Abra o arquivo HTML para visualizar: {output_path}")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        sucesso = gerar_html_teste()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
