"""
Templates HTML e estilos CSS para o relatório de vendas
Bem Me Quer Cosméticos

Este módulo centraliza toda a estrutura HTML e CSS,
deixando o código principal mais limpo e focado em lógica.
"""


def get_css_styles() -> str:
    """Retorna todos os estilos CSS do relatório."""
    return """
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',sans-serif; background:#F5F3EC; color:#324D38; padding:20px; min-height:100vh; }
        .container { max-width:860px; margin:0 auto; }
        .header { text-align:center; padding:35px 20px 30px; background:linear-gradient(135deg,#324D38,#4a6b52); border-radius:20px; margin-bottom:20px; position:relative; overflow:hidden; }
        .header::before { content:''; position:absolute; top:-50%; right:-30%; width:400px; height:400px; background:radial-gradient(circle,rgba(199,207,158,0.15) 0%,transparent 70%); }
        .logo { width:160px; height:auto; margin-bottom:15px; filter:brightness(0) invert(1); opacity:0.95; }
        .logo-text { font-family:'Cormorant Garamond',serif; font-size:2.2em; color:#F5F3EC; font-weight:400; font-style:italic; margin-bottom:10px; }
        .logo-text span { font-size:0.4em; font-style:normal; letter-spacing:4px; text-transform:uppercase; display:block; opacity:0.7; }
        .header h1 { font-size:1.1em; font-weight:500; color:#C7CF9E; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }
        .header .subtitle { color:rgba(245,243,236,0.6); font-size:0.85em; font-weight:300; }
        .badge-fechamento { display:inline-block; background:#B84527; color:#fff; padding:4px 14px; border-radius:20px; font-size:0.75em; font-weight:700; letter-spacing:1px; margin-top:8px; }
        .meta-section { background:#fff; border-radius:18px; padding:28px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }
        .meta-numeros { display:flex; justify-content:space-between; flex-wrap:wrap; gap:15px; margin-bottom:22px; }
        .meta-item { text-align:center; flex:1; min-width:120px; padding:12px 8px; background:#fafaf6; border-radius:12px; border:1px solid rgba(50,77,56,0.06); }
        .meta-item .label { color:#8BA279; font-size:0.7em; text-transform:uppercase; letter-spacing:1.5px; font-weight:600; }
        .meta-item .value { font-size:1.4em; font-weight:700; color:#324D38; margin-top:6px; }
        .meta-item .value.destaque { color:#B84527; }
        .progress-container { background:#edeadf; border-radius:14px; height:36px; overflow:hidden; }
        .progress-bar { height:100%; border-radius:14px; background:linear-gradient(90deg,#8BA279,#324D38); transition:width 1.5s ease; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85em; color:#F5F3EC; text-shadow:0 1px 2px rgba(0,0,0,0.3); min-width:60px; }
        .comparativo { padding:14px 20px; border-radius:12px; margin-bottom:18px; font-size:0.92em; font-weight:500; }
        .comparativo.positivo { background:rgba(50,77,56,0.08); border:1px solid rgba(50,77,56,0.15); color:#324D38; }
        .comparativo.negativo { background:rgba(184,69,39,0.08); border:1px solid rgba(184,69,39,0.15); color:#B84527; }
        .comparativo-justo { background:#fff; border-radius:16px; padding:22px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:2px solid #C7CF9E; }
        .comparativo-justo h3 { font-size:0.95em; margin-bottom:14px; color:#324D38; }
        .comparativo-justo small { display:block; margin-top:10px; color:#8BA279; font-size:0.82em; }
        .justo-grid { display:flex; gap:14px; flex-wrap:wrap; }
        .justo-item { flex:1; min-width:140px; text-align:center; padding:12px; background:#fafaf6; border-radius:10px; }
        .justo-item.result { background:rgba(50,77,56,0.06); }
        .justo-label { font-size:0.72em; text-transform:uppercase; letter-spacing:1px; color:#8BA279; font-weight:600; }
        .justo-value { font-size:1.2em; font-weight:700; color:#324D38; margin-top:4px; }
        .justo-value span { font-size:0.6em; font-weight:400; color:#888; }
        .cards { display:flex; gap:16px; flex-wrap:wrap; margin-bottom:18px; }
        .card { flex:1; min-width:280px; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }
        .card-header { padding:14px 20px; background:rgba(50,77,56,0.04); font-weight:600; font-size:0.88em; color:#324D38; border-bottom:1px solid rgba(50,77,56,0.06); }
        .card-body { padding:18px 20px; }
        .stat-row { display:flex; justify-content:space-between; padding:7px 0; font-size:0.88em; color:#555; }
        .stat-value { font-weight:600; color:#324D38; }
        .stat-row.highlight { font-weight:700; font-size:0.95em; padding-top:12px; margin-top:4px; border-top:1px solid rgba(50,77,56,0.08); }
        .highlight-value { color:#B84527; font-size:1.15em; font-weight:700; }
        .motivacao { text-align:center; padding-top:12px; font-size:0.95em; color:#8BA279; font-weight:600; }
        .preview-card { border-color:rgba(184,69,39,0.15); }
        .preview-card .card-header { background:rgba(184,69,39,0.04); color:#B84527; }
        .section { background:#fff; border-radius:18px; padding:28px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }
        .section h2 { font-size:1.05em; margin-bottom:18px; color:#324D38; font-weight:700; }
        .section h3 { font-size:0.92em; margin-bottom:12px; color:#324D38; font-weight:600; }
        .table-wrapper { overflow-x:auto; }
        table { width:100%; border-collapse:collapse; font-size:0.85em; }
        thead th { text-align:left; padding:10px 12px; background:rgba(50,77,56,0.04); color:#8BA279; font-weight:600; font-size:0.8em; text-transform:uppercase; letter-spacing:1px; border-bottom:2px solid rgba(50,77,56,0.1); }
        tbody td { padding:10px 12px; border-bottom:1px solid rgba(50,77,56,0.06); }
        .num { text-align:right; font-variant-numeric:tabular-nums; }
        .fechamento-section { border:2px solid #324D38; }
        .insight-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:22px; }
        .insight-card { background:#fafaf6; border-radius:14px; padding:18px; text-align:center; border:1px solid rgba(50,77,56,0.06); }
        .insight-card.wide { grid-column:1/-1; display:flex; align-items:center; gap:18px; text-align:left; justify-content:center; }
        .insight-icon { font-size:1.5em; margin-bottom:6px; }
        .insight-label { font-size:0.72em; text-transform:uppercase; letter-spacing:1px; color:#8BA279; font-weight:600; }
        .insight-value { font-size:1.4em; font-weight:700; color:#324D38; margin:4px 0; }
        .insight-sub { font-size:0.78em; color:#999; }
        .insights-grid-2col { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:18px; }
        @media (max-width:700px) { .insights-grid-2col { grid-template-columns:1fr; } }
        .chart-section { background:#fafaf6; border-radius:14px; padding:18px; border:1px solid rgba(50,77,56,0.06); }
        .bar-row { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
        .bar-label { width:35px; font-size:0.8em; font-weight:600; color:#555; }
        .bar-track { flex:1; background:#edeadf; border-radius:8px; height:22px; overflow:hidden; }
        .bar-fill { height:100%; background:linear-gradient(90deg,#8BA279,#324D38); border-radius:8px; transition:width 1s ease; }
        .bar-value { width:90px; text-align:right; font-size:0.8em; font-weight:600; color:#324D38; }
        .mini-table { background:#fafaf6; border-radius:14px; padding:18px; border:1px solid rgba(50,77,56,0.06); margin-bottom:14px; }
        .mini-table.fraco { border-color:rgba(184,69,39,0.12); }
        .mini-table table { font-size:0.85em; }
        .mini-table td { padding:8px 10px; }
        .mensagem-section { background:#fff; border-radius:18px; padding:28px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }
        .mensagem-section h2 { font-size:1em; margin-bottom:16px; color:#324D38; font-weight:600; }
        .mensagem-texto { background:#fafaf6; border:1px solid rgba(50,77,56,0.08); border-radius:12px; padding:20px; white-space:pre-wrap; font-size:0.88em; line-height:1.7; color:#444; max-height:500px; overflow-y:auto; }
        .btn-copiar { display:block; width:100%; margin-top:16px; padding:15px; border:none; border-radius:12px; background:linear-gradient(135deg,#324D38,#4a6b52); color:#F5F3EC; font-size:0.95em; font-weight:600; cursor:pointer; transition:all 0.3s; letter-spacing:0.5px; }
        .btn-copiar:hover { transform:translateY(-2px); box-shadow:0 6px 20px rgba(50,77,56,0.3); }
        .btn-copiar.copiado { background:linear-gradient(135deg,#8BA279,#a3b88e); }
        .aviso { background:rgba(230,168,52,0.1); border:1px solid rgba(230,168,52,0.25); border-radius:12px; padding:16px 20px; margin-bottom:18px; font-size:0.88em; color:#8B6914; }
        .aviso code { background:rgba(230,168,52,0.15); padding:2px 8px; border-radius:5px; font-size:0.9em; }
        .footer { text-align:center; padding:25px 20px; color:#BBB494; font-size:0.75em; letter-spacing:1px; }
        
        /* ── RESPONSIVENESS ── */
        .collapsible-header { display:flex; justify-content:space-between; align-items:center; padding:14px; background:rgba(50,77,56,0.04); border-radius:10px; cursor:pointer; user-select:none; font-weight:600; color:#324D38; transition:all 0.2s; border-bottom:2px solid rgba(50,77,56,0.1); }
        .collapsible-header:hover { background:rgba(50,77,56,0.08); }
        .collapsible-toggle { display:inline-block; width:20px; height:20px; text-align:center; line-height:20px; font-weight:700; transition:transform 0.3s; }
        .collapsible-toggle.open { transform:rotate(180deg); }
        .collapsible-content { max-height:2000px; overflow:hidden; transition:max-height 0.3s ease; }
        .collapsible-content.collapsed { max-height:0; }
        
        /* ── TABELAS RESPONSIVAS ── */
        .responsive-table { overflow-x:auto; }
        .responsive-table table { width:100%; }
        
        @media (max-width:768px) {
            .container { padding:12px; }
            .header { padding:20px 15px; margin-bottom:12px; }
            .logo { width:120px; }
            .logo-text { font-size:1.6em; }
            .header h1 { font-size:0.95em; }
            .meta-section { padding:16px; margin-bottom:12px; }
            .meta-numeros { flex-direction:column; gap:8px; }
            .meta-item { min-width:100%; }
            .section { padding:16px; margin-bottom:12px; border-radius:12px; }
            .section h2 { font-size:0.95em; }
            .insight-grid { grid-template-columns:1fr; gap:10px; }
            .insight-card { padding:12px; }
            .cards { flex-direction:column; }
            .card { min-width:100%; }
            table { font-size:0.75em; }
            thead th { padding:6px 8px; }
            tbody td { padding:6px 8px; }
            .justo-grid { flex-direction:column; gap:8px; }
            .justo-item { min-width:100%; padding:10px; }
            .btn-copiar { padding:12px; font-size:0.9em; }
            .responsive-table { -webkit-overflow-scrolling:touch; }
            .responsive-table table { min-width:500px; }
        }
        
        @media (max-width:480px) {
            body { padding:8px; }
            .container { padding:0; }
            .header { padding:16px 12px; margin-bottom:8px; border-radius:12px; }
            .logo { width:100px; }
            .logo-text { font-size:1.3em; }
            .header h1 { font-size:0.85em; }
            .section { padding:12px; margin-bottom:8px; border-radius:10px; }
            .section h2 { font-size:0.85em; margin-bottom:10px; }
            .meta-item .value { font-size:1.1em; }
            .insight-card { padding:10px; }
            .insight-icon { font-size:1.2em; }
            .insight-value { font-size:1.1em; }
            table { font-size:0.7em; }
            thead th { padding:4px 6px; }
            tbody td { padding:4px 6px; }
            .num { font-size:0.9em; }
            .mensagem-texto { max-height:300px; font-size:0.8em; line-height:1.5; padding:12px; }
            .footer { padding:15px 12px; font-size:0.7em; }
        }
    """


def get_html_structure(
    logo_html: str,
    modo_titulo: str,
    nome_mes: str,
    ano: int,
    dia: int,
    r: dict,
    modo_badge: str,
    aviso_html: str,
    comp_html: str,
    comp_justo_html: str,
    card_sp: str,
    card_sv: str,
    historico_html: str,
    insights_html: str,
    servicos_section_html: str,
    financeiro_section_html: str,
    mensagem_texto: str,
    msg_js: str,
    pct_meta: float,
) -> str:
    """
    Retorna o template HTML principal com todas as seções.
    
    Args:
        logo_html: HTML da logo
        modo_titulo: "📊 Fechamento Mensal" ou "📊 Relatório de Vendas"
        nome_mes: Nome do mês
        ano: Ano
        dia: Dia do mês
        r: Dicionário com dados do relatório
        modo_badge: Badge de fechamento (se houver)
        aviso_html: HTML do aviso do próximo mês
        comp_html: HTML do comparativo mensal
        comp_justo_html: HTML do comparativo justo
        card_sp: Card da semana passada
        card_sv: Card da semana que vem
        historico_html: HTML do histórico
        insights_html: HTML dos insights
        servicos_section_html: HTML da seção de serviços
        financeiro_section_html: HTML da seção financeira
        mensagem_texto: Texto da mensagem para o grupo
        msg_js: Mensagem formatada para JavaScript
        pct_meta: Percentual da meta
        
    Returns:
        String com o HTML completo
    """
    css_styles = get_css_styles()
    
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bem Me Quer — {modo_titulo}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        {css_styles}
    </style>
</head>
<body>
<div class="container">
    <div class="header">{logo_html}<h1>{modo_titulo}</h1><div class="subtitle">{nome_mes} {ano} — Dia {dia:02d}/{r['hoje'].month:02d}/{ano}</div>{modo_badge}</div>
    {aviso_html}
    <div class="meta-section">
        <div class="meta-numeros">
            <div class="meta-item"><div class="label">Vendas</div><div class="value">{formatar_moeda(r['vendas'])}</div></div>
            <div class="meta-item"><div class="label">Meta</div><div class="value">{formatar_moeda(r['meta'])}</div></div>
            <div class="meta-item"><div class="label">{"Superou em" if r["faltam"] <= 0 else "Faltam"}</div><div class="value destaque">{formatar_moeda(abs(r['faltam']))}</div></div>
            <div class="meta-item"><div class="label">Por dia ({r['dias_restantes']:.0f} dias)</div><div class="value">{formatar_moeda(r['valor_diario'])}</div></div>
        </div>
        <div class="progress-container"><div class="progress-bar" style="width:{min(pct_meta,100):.0f}%">{pct_meta:.1f}%</div></div>
    </div>
    {comp_html}
    {comp_justo_html}
    <div class="cards">{card_sp}{card_sv}</div>
    {historico_html}
    {insights_html}
    {servicos_section_html}
    {financeiro_section_html}
    <div class="mensagem-section">
        <h2>📋 Mensagem para o Grupo</h2>
        <div class="mensagem-texto" id="msgTexto">{mensagem_texto}</div>
        <button class="btn-copiar" id="btnCopiar" onclick="copiarMensagem()">📋 Copiar Mensagem</button>
    </div>
    <div class="footer"><span style="font-size:1.2em">🌿</span><br>Bem Me Quer Cosméticos — Gerado em {dia:02d}/{r['hoje'].month:02d}/{ano}</div>
</div>
<script>
function copiarMensagem() {{
    const msg = `{msg_js}`;
    navigator.clipboard.writeText(msg).then(() => {{
        const btn = document.getElementById('btnCopiar');
        btn.textContent = '✅ Copiado!';
        btn.classList.add('copiado');
        setTimeout(() => {{ btn.textContent = '📋 Copiar Mensagem'; btn.classList.remove('copiado'); }}, 2500);
    }});
}}
function copiarFinanceiro() {{
    const el = document.getElementById('msgFinTexto');
    if (el) {{
        navigator.clipboard.writeText(el.textContent).then(() => {{
            const btn = document.getElementById('btnCopiarFin');
            btn.textContent = '✅ Copiado!';
            btn.classList.add('copiado');
            setTimeout(() => {{ btn.textContent = '📋 Copiar Contas a Pagar'; btn.classList.remove('copiado'); }}, 2500);
        }});
    }}
}}
function toggleCollapsible(headerElement) {{
    const content = headerElement.nextElementSibling;
    const toggle = headerElement.querySelector('.collapsible-toggle');
    if (content && content.classList.contains('collapsible-content')) {{
        content.classList.toggle('collapsed');
        toggle.classList.toggle('open');
    }}
}}
document.addEventListener('DOMContentLoaded', () => {{
    const bar = document.querySelector('.progress-bar');
    if (bar) {{
        const w = bar.style.width; bar.style.width = '0%';
        setTimeout(() => {{ bar.style.width = w; }}, 300);
    }}
    
    // Inicializar seções colapsáveis
    const headers = document.querySelectorAll('.collapsible-header');
    headers.forEach(header => {{
        header.addEventListener('click', () => toggleCollapsible(header));
    }});
}});
</script>
</body></html>"""


def formatar_moeda(valor: float) -> str:
    """Formata um valor como moeda brasileira."""
    return f"R${valor:,.2f}".replace(",", "PLACEHOLDER").replace(".", ",").replace("PLACEHOLDER", ".")
