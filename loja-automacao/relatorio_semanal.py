"""
BLOCO 1+2 — Relatório de Vendas Semanal + Fechamento Mensal
Bem Me Quer Cosméticos

Uso:
  python relatorio_semanal.py              → Relatório semanal (acumula histórico)
  python relatorio_semanal.py --fechamento → Força fechamento mensal com insights
  python relatorio_semanal.py --auto       → Modo automático (sem prompts)

O histórico fica salvo em historico_MES_ANO.json na mesma pasta.
"""
import os
import webbrowser
import traceback
import datetime # <- Adicione esta linha no topo do seu arquivo

import gspread
from google.oauth2.service_account import Credentials
from datetime import date, timedelta
import calendar
import webbrowser
import base64
import json
import os
import sys

# Módulo de serviços
try:
    from servicos_analise import conectar_servicos, gerar_analise_servicos
    SERVICOS_DISPONIVEL = True
except ImportError:
    SERVICOS_DISPONIVEL = False
    print("⚠️ Módulo servicos_analise.py não encontrado. Seção de serviços desativada.")

# Módulo financeiro
try:
    from financeiro_analise import carregar_financeiro, CMV_TETO_PCT, META_NUBANK
    FINANCEIRO_DISPONIVEL = True
except ImportError:
    FINANCEIRO_DISPONIVEL = False
    print("⚠️ Módulo financeiro_analise.py não encontrado. Seção financeira desativada.")

# Módulo de templates HTML
try:
    from html_templates import get_html_structure
    TEMPLATES_DISPONIVEL = True
except ImportError:
    TEMPLATES_DISPONIVEL = False
    print("⚠️ Módulo html_templates.py não encontrado. Seção financeira desativada.")

# =====================================================
# CONFIGURAÇÕES
# =====================================================

CREDENCIAIS = "credentials/service_account.json"
PLANILHA_VENDAS_ID = "1Gdr6WSrf3SaL9WkvASIRcBi5nYKZDUK7FysPDzwI_HU"
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))

NOMES_MESES_VARIACOES = {
    1:  ["JANEIRO", "JAN"],
    2:  ["FEVEREIRO", "FEV"],
    3:  ["MARÇO", "MARCO", "MAR"],
    4:  ["ABRIL", "ABR"],
    5:  ["MAIO", "MAI"],
    6:  ["JUNHO", "JUN"],
    7:  ["JULHO", "JUL"],
    8:  ["AGOSTO", "AGO"],
    9:  ["SETEMBRO", "SET"],
    10: ["OUTUBRO", "OUT"],
    11: ["NOVEMBRO", "NOV"],
    12: ["DEZEMBRO", "DEZ"],
}

NOMES_MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",
    4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",
    10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

DIAS_SEMANA_PT = {
    0: "Segunda", 1: "Terça", 2: "Quarta",
    3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"
}

# ── FERIADOS / FECHAMENTOS ──
# Formato: (dia, mês) — a loja fecha nesses dias
# Inclui: feriados nacionais + carnaval (seg+ter) + dia após Corpus Christi
# Quarta de Cinzas é MEIO PERÍODO (contada como 0.5 dia útil, tratada separadamente)

FERIADOS_2025 = [
    (1, 1),                # Confraternização
    (3, 3), (4, 3),        # Carnaval seg+ter (2025: março)
    (18, 4),               # Sexta-feira Santa
    (21, 4),               # Tiradentes
    (1, 5),                # Dia do Trabalho
    (20, 6),               # Corpus Christi (2025)
    (7, 9),                # Independência
    (12, 10),              # N.S. Aparecida
    (2, 11),               # Finados
    (15, 11),              # Proclamação República
    (25, 12),              # Natal
]

FERIADOS_2026 = [
    (1, 1),                # Confraternização
    (16, 2), (17, 2),      # Carnaval seg+ter (2026: fevereiro)
    (3, 4),                # Sexta-feira Santa
    (21, 4),               # Tiradentes
    (1, 5),                # Dia do Trabalho
    (5, 6),                # Corpus Christi (2026)
    (7, 9),                # Independência
    (12, 10),              # N.S. Aparecida
    (2, 11),               # Finados
    (15, 11),              # Proclamação República
    (25, 12),              # Natal
]

# Quarta de Cinzas — meio período (0.5 dia útil)
MEIOS_PERIODOS_2025 = [(5, 3)]    # 5/mar/2025
MEIOS_PERIODOS_2026 = [(18, 2)]   # 18/fev/2026

def get_feriados(ano):
    if ano == 2025:
        return FERIADOS_2025
    elif ano == 2026:
        return FERIADOS_2026
    return FERIADOS_2026  # fallback

def get_meios_periodos(ano):
    if ano == 2025:
        return MEIOS_PERIODOS_2025
    elif ano == 2026:
        return MEIOS_PERIODOS_2026
    return []


# =====================================================
# DIAS ÚTEIS (ajustado)
# =====================================================

def contar_dias_uteis_mes(ano, mes, ate_dia=None):
    """Conta dias úteis no mês, descontando domingos, feriados e meios períodos."""
    ultimo_dia = ate_dia or calendar.monthrange(ano, mes)[1]
    feriados = get_feriados(ano)
    meios = get_meios_periodos(ano)
    dias = 0.0
    for dia in range(1, ultimo_dia + 1):
        dt = date(ano, mes, dia)
        if dt.weekday() == 6:  # domingo
            continue
        if (dia, mes) in feriados:
            continue
        if (dia, mes) in meios:
            dias += 0.5
        else:
            dias += 1.0
    return dias


def contar_dias_restantes(ano, mes, dia_atual, dias_diarios=None):
    """Conta dias úteis restantes no mês a partir de hoje.
    
    Um dia é contado como "preenchido" se:
    - É <= hoje (data passou)
    - Ou está na lista dias_diarios com vendas registradas
    
    Args:
        ano, mes, dia_atual: Data de referência
        dias_diarios: Lista de dicts com vendas diárias (opcional, não usado mas mantido para compatibilidade)
    """
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    feriados = get_feriados(ano)
    meios = get_meios_periodos(ano)
    
    hoje = date.today()
    # Um dia é considerado "preenchido" se já passou (é <= hoje)
    primeiro_dia = dia_atual + 1 if date(ano, mes, dia_atual) < hoje else dia_atual
    
    dias = 0.0
    for dia in range(primeiro_dia, ultimo_dia + 1):
        dt = date(ano, mes, dia)
        if dt.weekday() == 6:  # Domingo
            continue
        if (dia, mes) in feriados:
            continue
        if (dia, mes) in meios:
            dias += 0.5
        else:
            dias += 1.0
    return dias


# =====================================================
# FECHAMENTOS EXTRAS (interativo)
# =====================================================

def caminho_fechamentos_extras(mes, ano):
    return os.path.join(PASTA_SCRIPT, f"fechamentos_extras_{NOMES_MESES[mes].upper()}{str(ano)[-2:]}.json")


def carregar_fechamentos_extras(mes, ano):
    caminho = caminho_fechamentos_extras(mes, ano)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_fechamentos_extras(mes, ano, lista):
    caminho = caminho_fechamentos_extras(mes, ano)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False)


def perguntar_fechamentos_extras(mes, ano, auto=False):
    """Pergunta se houve dias extras que a loja fechou."""
    extras = carregar_fechamentos_extras(mes, ano)
    nome_mes = NOMES_MESES[mes]

    if extras and not auto:
        print(f"\n📅 Fechamentos extras já registrados em {nome_mes}:")
        for d in extras:
            print(f"   → Dia {d}")

    if auto:
        return extras

    print(f"\n❓ Houve algum dia EXTRA que a loja fechou em {nome_mes}?")
    print("   (Além dos feriados e domingos já configurados)")
    print("   Digite os dias separados por vírgula (ex: 5,12,20)")
    print("   Ou pressione ENTER para pular: ", end="")

    resp = input().strip()
    if resp:
        novos = []
        for parte in resp.split(","):
            parte = parte.strip()
            if parte.isdigit():
                d = int(parte)
                if 1 <= d <= calendar.monthrange(ano, mes)[1]:
                    if d not in extras:
                        novos.append(d)
        if novos:
            extras.extend(novos)
            extras.sort()
            salvar_fechamentos_extras(mes, ano, extras)
            print(f"   ✅ Adicionados: {novos}")

    return extras


# =====================================================
# AUSÊNCIAS DA EQUIPE
# =====================================================

def caminho_ausencias():
    return os.path.join(PASTA_SCRIPT, "equipe_ausencias.json")


def carregar_ausencias():
    caminho = caminho_ausencias()
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_ausencias(lista):
    with open(caminho_ausencias(), "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


def perguntar_ausencias(mes, ano, auto=False):
    """Pergunta se há ausências da equipe para registrar."""
    ausencias = carregar_ausencias()
    nome_mes = NOMES_MESES[mes]

    # Filtrar ausências do mês atual
    aus_mes = [a for a in ausencias if a.get("mes") == mes and a.get("ano") == ano]

    if aus_mes and not auto:
        print(f"\n👥 Ausências já registradas em {nome_mes}:")
        for a in aus_mes:
            print(f"   → {a['nome']}: {a['motivo']} (dias {a['dia_inicio']}-{a['dia_fim']})")

    if auto:
        return [a for a in ausencias if a.get("mes") == mes and a.get("ano") == ano]

    print(f"\n❓ Quer registrar ausência de algum colaborador em {nome_mes}?")
    print("   Formato: Nome, motivo, dia_inicio, dia_fim")
    print("   Ex: Gabriel, férias, 1, 28")
    print("   Ou pressione ENTER para pular: ", end="")

    resp = input().strip()
    if resp:
        partes = [p.strip() for p in resp.split(",")]
        if len(partes) >= 4:
            nova = {
                "nome": partes[0],
                "motivo": partes[1],
                "dia_inicio": int(partes[2]),
                "dia_fim": int(partes[3]),
                "mes": mes,
                "ano": ano,
            }
            ausencias.append(nova)
            salvar_ausencias(ausencias)
            print(f"   ✅ Registrado: {nova['nome']} — {nova['motivo']}")
        else:
            print("   ⚠️ Formato inválido. Use: Nome, motivo, dia_inicio, dia_fim")

    return [a for a in ausencias if a.get("mes") == mes and a.get("ano") == ano]


# =====================================================
# DETECÇÃO INTELIGENTE DE ABAS
# =====================================================

def carregar_abas_disponiveis(planilha):
    return [ws.title for ws in planilha.worksheets()]


def encontrar_aba(abas_disponiveis, mes, ano):
    ano_curto = str(ano)[-2:]
    for nome in NOMES_MESES_VARIACOES.get(mes, []):
        if f"{nome}{ano_curto}" in abas_disponiveis:
            return f"{nome}{ano_curto}"
    return None


def verificar_proximo_mes(abas_disponiveis, hoje):
    ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
    dias_faltando = ultimo_dia - hoje.day
    if dias_faltando > 7:
        return None
    prox_mes = hoje.month % 12 + 1
    prox_ano = hoje.year + (1 if hoje.month == 12 else 0)
    if encontrar_aba(abas_disponiveis, prox_mes, prox_ano):
        return None
    ano_curto = str(prox_ano)[-2:]
    return {
        "dias_faltando": dias_faltando,
        "mes_nome": NOMES_MESES[prox_mes],
        "ano": prox_ano,
        "sugestoes": [f"{v}{ano_curto}" for v in NOMES_MESES_VARIACOES[prox_mes]],
    }


# =====================================================
# FUNÇÕES DE DADOS
# =====================================================

def conectar():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_file(CREDENCIAIS, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(PLANILHA_VENDAS_ID)


def limpar_valor(texto):
    if not texto or texto.strip() in ["-", "", "R$", "$"]:
        return 0.0
    texto = texto.replace("R$", "").replace("$", "").strip()
    if "," in texto and "." in texto:
        if texto.rfind(".") > texto.rfind(","):
            texto = texto.replace(",", "")
        else:
            texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def formatar_moeda(valor):
    negativo = valor < 0
    valor = abs(valor)
    inteiro = int(valor)
    decimal = round((valor - inteiro) * 100)
    if decimal >= 100:
        inteiro += 1
        decimal = 0
    s_inteiro = f"{inteiro:,}".replace(",", ".")
    resultado = f"R${s_inteiro},{decimal:02d}"
    return f"-{resultado}" if negativo else resultado


def encontrar_linhas(dados):
    resultado = {
        "loja_meta": None, "loja_realizado": None,
        "ecommerce_meta": None, "ecommerce_realizado": None,
        "servicos_realizado": None,
    }
    secao_atual = None
    for i, linha in enumerate(dados):
        texto = " ".join(str(c).upper().strip() for c in linha[:4])
        if "LOJA" in texto and ("FÍSICA" in texto or "FISICA" in texto):
            secao_atual = "loja"
        elif "ECOM" in texto or "E-COM" in texto:
            secao_atual = "ecommerce"
        elif "SERVI" in texto:
            secao_atual = "servicos"
        if "META" in texto and "VS" not in texto:
            if secao_atual == "loja":
                resultado["loja_meta"] = i
            elif secao_atual == "ecommerce":
                resultado["ecommerce_meta"] = i
        elif "REALIZADO" in texto and "VS" not in texto:
            if secao_atual == "loja":
                resultado["loja_realizado"] = i
            elif secao_atual == "ecommerce":
                resultado["ecommerce_realizado"] = i
            elif secao_atual == "servicos":
                resultado["servicos_realizado"] = i
    return resultado


def somar_linha_periodo(linha, dia_inicio, dia_fim):
    total = 0.0
    for dia in range(dia_inicio, dia_fim + 1):
        col = dia + 2
        if col < len(linha):
            total += limpar_valor(linha[col])
    return total


def ler_valor_dia(linha, dia):
    col = dia + 2
    return limpar_valor(linha[col]) if col < len(linha) else 0.0


def ler_meta_total(linha):
    for i in range(len(linha) - 1, 2, -1):
        v = limpar_valor(linha[i])
        if v > 0:
            return v
    return 0.0


def obter_dados_aba(planilha, abas, mes, ano):
    nome_aba = encontrar_aba(abas, mes, ano)
    if not nome_aba:
        return None, None, None
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.exceptions.WorksheetNotFound:
        return None, None, None
    dados = aba.get_all_values()
    if len(dados) < 3:
        return None, None, None
    return dados, encontrar_linhas(dados), nome_aba


def calcular_vendas_produtos(dados, linhas, dia_inicio, dia_fim):
    loja = ecom = serv = 0.0
    if linhas["loja_realizado"] is not None:
        loja = somar_linha_periodo(dados[linhas["loja_realizado"]], dia_inicio, dia_fim)
    if linhas["ecommerce_realizado"] is not None:
        ecom = somar_linha_periodo(dados[linhas["ecommerce_realizado"]], dia_inicio, dia_fim)
    if linhas["servicos_realizado"] is not None:
        serv = somar_linha_periodo(dados[linhas["servicos_realizado"]], dia_inicio, dia_fim)
    return loja - serv + ecom, serv


def ler_vendas(planilha, abas, mes, ano, ate_dia=None):
    dados, linhas, nome_aba = obter_dados_aba(planilha, abas, mes, ano)
    if dados is None:
        return None
    if ate_dia is None:
        ate_dia = calendar.monthrange(ano, mes)[1]
    vendas, servicos = calcular_vendas_produtos(dados, linhas, 1, ate_dia)
    meta_loja = meta_ecom = 0.0
    if linhas["loja_meta"] is not None:
        meta_loja = ler_meta_total(dados[linhas["loja_meta"]])
    if linhas["ecommerce_meta"] is not None:
        meta_ecom = ler_meta_total(dados[linhas["ecommerce_meta"]])
    return {
        "vendas_produtos": vendas, "servicos": servicos,
        "meta_total": meta_loja + meta_ecom, "nome_aba": nome_aba,
        "linhas_detectadas": linhas, "dados_brutos": dados,
    }


# =====================================================
# DADOS DIÁRIOS (PARA INSIGHTS)
# =====================================================

def extrair_vendas_diarias(dados, linhas, mes, ano):
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    hoje = date.today()
    dias = []
    for dia in range(1, ultimo_dia + 1):
        try:
            dt = date(ano, mes, dia)
        except ValueError:
            continue
        if dt > hoje and ano == hoje.year:
            break
        if dt.weekday() == 6:
            continue
        loja = serv = ecom = 0.0
        if linhas["loja_realizado"] is not None:
            loja = ler_valor_dia(dados[linhas["loja_realizado"]], dia)
        if linhas["servicos_realizado"] is not None:
            serv = ler_valor_dia(dados[linhas["servicos_realizado"]], dia)
        if linhas["ecommerce_realizado"] is not None:
            ecom = ler_valor_dia(dados[linhas["ecommerce_realizado"]], dia)
        produtos = loja - serv + ecom
        if produtos == 0 and serv == 0:
            continue
        dias.append({
            "dia": dia, "data": dt.isoformat(),
            "dia_semana": dt.weekday(),
            "dia_semana_nome": DIAS_SEMANA_PT[dt.weekday()],
            "produtos": round(produtos, 2),
            "servicos": round(serv, 2),
            "total": round(produtos + serv, 2),
        })
    return dias


def gerar_insights(dias_atual, dias_anterior, mes, ano):
    if not dias_atual:
        return {}

    total_vendas = sum(d["produtos"] for d in dias_atual)
    dias_com_venda = len([d for d in dias_atual if d["produtos"] > 0])
    ticket_medio = total_vendas / dias_com_venda if dias_com_venda > 0 else 0

    # Média por dia da semana
    vendas_ds = {}
    contagem_ds = {}
    for d in dias_atual:
        ds = d["dia_semana"]
        vendas_ds[ds] = vendas_ds.get(ds, 0) + d["produtos"]
        contagem_ds[ds] = contagem_ds.get(ds, 0) + 1
    media_ds = {ds: vendas_ds[ds] / contagem_ds[ds] for ds in vendas_ds}
    melhor_ds = max(media_ds, key=media_ds.get) if media_ds else None
    pior_ds = min(media_ds, key=media_ds.get) if media_ds else None

    # TOP 5 e Bottom 3
    top5 = sorted(dias_atual, key=lambda x: x["produtos"], reverse=True)[:5]
    bottom3 = sorted([d for d in dias_atual if d["produtos"] > 0], key=lambda x: x["produtos"])[:3]

    # Tendência
    meio = len(dias_atual) // 2
    if meio > 0:
        media_1a = sum(d["produtos"] for d in dias_atual[:meio]) / meio
        media_2a = sum(d["produtos"] for d in dias_atual[meio:]) / len(dias_atual[meio:])
        tendencia_pct = ((media_2a - media_1a) / media_1a * 100) if media_1a > 0 else 0
    else:
        media_1a = media_2a = tendencia_pct = 0

    # Serviços
    total_servicos = sum(d["servicos"] for d in dias_atual)
    serv_por_semana = {}
    for d in dias_atual:
        sn = (d["dia"] - 1) // 7 + 1
        serv_por_semana[sn] = serv_por_semana.get(sn, 0) + d["servicos"]
    sem_mais_serv = max(serv_por_semana, key=serv_por_semana.get) if serv_por_semana else None

    # Impacto da profissional: dias COM serviço (ter/qui/sex) vs SEM (seg/qua/sáb)
    DIAS_COM_PROF = {1, 3, 4}  # Terça, Quinta, Sexta
    vendas_com_prof = [d["produtos"] for d in dias_atual if d["dia_semana"] in DIAS_COM_PROF and d["produtos"] > 0]
    vendas_sem_prof = [d["produtos"] for d in dias_atual if d["dia_semana"] not in DIAS_COM_PROF and d["produtos"] > 0]
    media_com_prof = sum(vendas_com_prof) / len(vendas_com_prof) if vendas_com_prof else 0
    media_sem_prof = sum(vendas_sem_prof) / len(vendas_sem_prof) if vendas_sem_prof else 0
    diff_prof = media_com_prof - media_sem_prof
    pct_prof = (diff_prof / media_sem_prof * 100) if media_sem_prof > 0 else 0

    # Dias úteis REAIS (contados pela planilha: dias com vendas)
    dias_uteis_atual = len(dias_atual)
    dias_uteis_anterior = len(dias_anterior) if dias_anterior else contar_dias_uteis_mes(ano - 1, mes)

    # Comparativo semanal
    comparativo_semanal = []
    if dias_anterior:
        vendas_ant_dia = {d["dia"]: d["produtos"] for d in dias_anterior}
        semanas = {}
        for d in dias_atual:
            sem = (d["dia"] - 1) // 7 + 1
            if sem not in semanas:
                semanas[sem] = {"vendas": 0, "vendas_ant": 0, "dias": []}
            semanas[sem]["vendas"] += d["produtos"]
            semanas[sem]["dias"].append(d["dia"])
            semanas[sem]["vendas_ant"] += vendas_ant_dia.get(d["dia"], 0)
        for sn in sorted(semanas):
            s = semanas[sn]
            diff = s["vendas"] - s["vendas_ant"]
            pct = (diff / s["vendas_ant"] * 100) if s["vendas_ant"] > 0 else 0
            comparativo_semanal.append({
                "semana": sn, "dia_inicio": min(s["dias"]), "dia_fim": max(s["dias"]),
                "vendas": round(s["vendas"], 2), "vendas_ant": round(s["vendas_ant"], 2),
                "diferenca": round(diff, 2), "percentual": round(pct, 1),
            })

    # Vendas por dia útil (comparação justa)
    vendas_ant_total = sum(d["produtos"] for d in dias_anterior) if dias_anterior else 0
    venda_por_dia_util_atual = total_vendas / dias_uteis_atual if dias_uteis_atual > 0 else 0
    venda_por_dia_util_ant = vendas_ant_total / dias_uteis_anterior if dias_uteis_anterior > 0 else 0
    diff_por_dia_util = venda_por_dia_util_atual - venda_por_dia_util_ant
    pct_por_dia_util = (diff_por_dia_util / venda_por_dia_util_ant * 100) if venda_por_dia_util_ant > 0 else 0

    # Dias fracos — abaixo de 30% do ticket médio (vale a pena abrir?)
    dias_fracos = []
    limiar_fraco = ticket_medio * 0.3
    for d in dias_atual:
        if 0 < d["produtos"] < limiar_fraco:
            dias_fracos.append({
                "dia": d["dia"],
                "dia_semana_nome": d["dia_semana_nome"],
                "produtos": d["produtos"],
                "pct_do_ticket": round((d["produtos"] / ticket_medio * 100) if ticket_medio > 0 else 0, 1),
            })

    # Dias que a loja NÃO abriu (sem vendas, excluindo domingos e dias futuros)
    dias_fechados = []
    for dia_num in range(1, calendar.monthrange(ano, mes)[1] + 1):
        try:
            dt = date(ano, mes, dia_num)
        except ValueError:
            continue
        if dt > date.today() and ano == date.today().year:
            break
        if dt.weekday() == 6:
            continue
        if not any(d["dia"] == dia_num for d in dias_atual):
            dias_fechados.append({
                "dia": dia_num,
                "dia_semana_nome": DIAS_SEMANA_PT[dt.weekday()],
            })

    return {
        "ticket_medio": round(ticket_medio, 2),
        "dias_trabalhados": dias_com_venda,
        "melhor_dia_semana": DIAS_SEMANA_PT.get(melhor_ds, "—"),
        "melhor_dia_semana_media": round(media_ds.get(melhor_ds, 0), 2),
        "pior_dia_semana": DIAS_SEMANA_PT.get(pior_ds, "—"),
        "pior_dia_semana_media": round(media_ds.get(pior_ds, 0), 2),
        "media_por_dia_semana": {DIAS_SEMANA_PT[k]: round(v, 2) for k, v in sorted(media_ds.items())},
        "top5": top5, "bottom3": bottom3,
        "tendencia_pct": round(tendencia_pct, 1),
        "media_1a_metade": round(media_1a, 2),
        "media_2a_metade": round(media_2a, 2),
        "total_servicos": round(total_servicos, 2),
        "semana_mais_servicos": sem_mais_serv,
        "servicos_por_semana": {str(k): round(v, 2) for k, v in serv_por_semana.items()},
        "comparativo_semanal": comparativo_semanal,
        "dias_uteis_atual": dias_uteis_atual,
        "dias_uteis_anterior": dias_uteis_anterior,
        "venda_por_dia_util_atual": round(venda_por_dia_util_atual, 2),
        "venda_por_dia_util_ant": round(venda_por_dia_util_ant, 2),
        "diff_por_dia_util": round(diff_por_dia_util, 2),
        "pct_por_dia_util": round(pct_por_dia_util, 1),
        "dias_fracos": dias_fracos,
        "dias_fechados": dias_fechados,
        "impacto_profissional": {
            "media_com": round(media_com_prof, 2),
            "media_sem": round(media_sem_prof, 2),
            "diferenca": round(diff_prof, 2),
            "percentual": round(pct_prof, 1),
            "dias_com": len(vendas_com_prof),
            "dias_sem": len(vendas_sem_prof),
        },
    }


# =====================================================
# HISTÓRICO JSON
# =====================================================

def caminho_historico(mes, ano):
    return os.path.join(PASTA_SCRIPT, f"historico_{NOMES_MESES[mes].upper()}{str(ano)[-2:]}.json")


def carregar_historico(mes, ano):
    caminho = caminho_historico(mes, ano)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"semanas": [], "fechamento": None}


def salvar_historico(mes, ano, historico):
    with open(caminho_historico(mes, ano), "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def registrar_semana(historico, dados_semana):
    chave = dados_semana["periodo"]
    for i, sem in enumerate(historico["semanas"]):
        if sem["periodo"] == chave:
            historico["semanas"][i] = dados_semana
            return
    historico["semanas"].append(dados_semana)


# =====================================================
# ANÁLISES SEMANAIS
# =====================================================

def calcular_semana(hoje):
    """Retorna a SEMANA COMPLETA (segunda a domingo) em que hoje se encontra."""
    ds = hoje.weekday()
    # Retornar segunda até domingo da semana ATUAL
    segunda = hoje - timedelta(days=ds)  # volta até segunda
    domingo = segunda + timedelta(days=6)  # avança 6 dias até domingo
    return segunda, domingo


def calcular_proxima_semana(hoje):
    """Retorna a PRÓXIMA SEMANA COMPLETA (segunda a domingo)."""
    ds = hoje.weekday()
    # Calcular quantos dias até próxima segunda
    dias_ate_prox_seg = (7 - ds) % 7
    if dias_ate_prox_seg == 0:
        dias_ate_prox_seg = 7  # Se hoje é segunda, próxima é em 7 dias
    prox_segunda = hoje + timedelta(days=dias_ate_prox_seg)
    prox_domingo = prox_segunda + timedelta(days=6)
    return prox_segunda, prox_domingo


def analise_semanal_passada(planilha, abas, hoje):
    inicio, fim = calcular_semana(hoje)
    
    # Retroceder 7 dias para obter a semana anterior completa
    inicio_anterior = inicio - timedelta(days=7)
    fim_anterior = fim - timedelta(days=7)
    
    # Determinar mês/ano da semana anterior
    mes, ano = inicio_anterior.month, inicio_anterior.year
    
    dados_atual, linhas_atual, _ = obter_dados_aba(planilha, abas, mes, ano)
    if dados_atual is None:
        return None
    vendas, _ = calcular_vendas_produtos(dados_atual, linhas_atual, inicio_anterior.day, fim_anterior.day)
    
    dados_ant, linhas_ant, _ = obter_dados_aba(planilha, abas, mes, ano - 1)
    if dados_ant is None:
        return None
    ult = calendar.monthrange(ano - 1, mes)[1]
    vendas_ant, _ = calcular_vendas_produtos(dados_ant, linhas_ant, min(inicio_anterior.day, ult), min(fim_anterior.day, ult))
    if vendas_ant == 0:
        return None
    dif = vendas - vendas_ant
    return {"inicio": inicio_anterior, "fim": fim_anterior, "vendas": vendas, "vendas_ant": vendas_ant,
            "diferenca": dif, "percentual": (dif / vendas_ant) * 100}


def analise_semana_que_vem(planilha, abas, hoje):
    """Retorna análise da semana ATUAL (Esta Semana)."""
    inicio, fim = calcular_semana(hoje)  # Semana ATUAL, não próxima
    mes_ref, ano_ref = inicio.month, inicio.year
    
    # Se a semana cruza meses (ex: 23/02 a 01/03), usar apenas o mês atual para cálculos de vendas
    if fim.month != inicio.month:
        ult_mes = calendar.monthrange(ano_ref, mes_ref)[1]
        fim_calc = ult_mes  # Usar até o último dia do mês
    else:
        fim_calc = fim.day
    
    dados_ant, linhas_ant, _ = obter_dados_aba(planilha, abas, mes_ref, ano_ref - 1)
    if dados_ant is None:
        return None
    ult_ant = calendar.monthrange(ano_ref - 1, mes_ref)[1]
    vendas_ant, _ = calcular_vendas_produtos(dados_ant, linhas_ant, min(inicio.day, ult_ant), min(fim_calc, ult_ant))
    if vendas_ant == 0:
        return None
    # Retornar datas ORIGINAIS - servicos_analise.py truncará internamente se cruzar mês
    return {"inicio": inicio, "fim": fim, "vendas_ano_passado": vendas_ant}


def eh_ultimo_dia_util(hoje):
    return contar_dias_restantes(hoje.year, hoje.month, hoje.day) == 0


# =====================================================
# GERAÇÃO DOS DADOS
# =====================================================

def gerar_dados_relatorio(forcar_fechamento=False, auto=False):
    hoje = date.today()
    mes, ano, dia = hoje.month, hoje.year, hoje.day
    nome_mes = NOMES_MESES[mes]

    planilha = conectar()
    abas = carregar_abas_disponiveis(planilha)

    aba_atual = encontrar_aba(abas, mes, ano)
    print(f"📅 Data: {dia:02d}/{mes:02d}/{ano}")
    print(f"📂 Aba: {aba_atual or '❌ NÃO ENCONTRADA'}")

    aviso_prox = verificar_proximo_mes(abas, hoje)
    dados = ler_vendas(planilha, abas, mes, ano, dia)
    if not dados:
        return None

    vendas = dados["vendas_produtos"]
    meta = dados["meta_total"]
    print(f"   Vendas: {formatar_moeda(vendas)} | Meta: {formatar_moeda(meta)}")

    dados_ant = ler_vendas(planilha, abas, mes, ano - 1, dia)
    dif_mes = (vendas - dados_ant["vendas_produtos"]) if dados_ant else None

    sp = analise_semanal_passada(planilha, abas, hoje)
    sv = analise_semana_que_vem(planilha, abas, hoje)
    
    # Extrair dados diários ANTES de calcular dias restantes (pra saber se dia atual foi preenchido)
    dias_diarios = extrair_vendas_diarias(dados["dados_brutos"], dados["linhas_detectadas"], mes, ano)
    
    # Agora calcular dias restantes levando em conta se o dia atual foi preenchido
    dias_rest = contar_dias_restantes(ano, mes, dia, dias_diarios)
    val_diario = (meta - vendas) / dias_rest if dias_rest > 0 else 0

    fechamento = forcar_fechamento or eh_ultimo_dia_util(hoje)
    if fechamento:
        print("   📊 MODO FECHAMENTO MENSAL!")

    # Perguntar fechamentos extras
    extras = perguntar_fechamentos_extras(mes, ano, auto=auto)

    # Perguntar ausências da equipe
    ausencias = perguntar_ausencias(mes, ano, auto=auto)

    # Dados diários anterior e insights
    dias_diarios_ant = None
    if dados_ant:
        dias_diarios_ant = extrair_vendas_diarias(
            dados_ant["dados_brutos"], dados_ant["linhas_detectadas"], mes, ano - 1
        )
    insights = gerar_insights(dias_diarios, dias_diarios_ant, mes, ano) if dias_diarios else {}

    # Histórico
    historico = carregar_historico(mes, ano)
    if sp:
        # Comentado para evitar duplicatas - registrar_semana adiciona entradas conflitantes
        pass
        # registrar_semana(historico, {
        #     "periodo": f"{sp['inicio'].day:02d}/{sp['inicio'].month:02d} a {sp['fim'].day:02d}/{sp['fim'].month:02d}",
        #     "vendas": round(sp["vendas"], 2), "vendas_ant": round(sp["vendas_ant"], 2),
        #     "diferenca": round(sp["diferenca"], 2), "percentual": round(sp["percentual"], 1),
        #     "data_registro": hoje.isoformat(),
        # })
    if fechamento:
        historico["fechamento"] = {
            "data": hoje.isoformat(), "vendas_total": round(vendas, 2),
            "meta": round(meta, 2), "servicos_total": round(dados["servicos"], 2),
            "insights": insights,
        }
    salvar_historico(mes, ano, historico)

    if aviso_prox:
        print(f"   ⚠️ Criar aba de {aviso_prox['mes_nome']}/{aviso_prox['ano']}!")
    print(f"   ✅ Dados coletados!")

    # Análise de serviços
    analise_serv = None
    if SERVICOS_DISPONIVEL:
        try:
            print(f"\n💆‍♀️ Carregando dados de serviços...")
            plan_serv, abas_serv = conectar_servicos(CREDENCIAIS)
            analise_serv = gerar_analise_servicos(plan_serv, mes, ano, abas_serv,
                semana_inicio=sv["inicio"] if sv else None,
                semana_fim=sv["fim"] if sv else None)
            if analise_serv:
                print(f"   Atendimentos: {analise_serv['total_atendimentos']} | Receita: R${analise_serv['receita_total']:,.2f}")
                print(f"   Lucro serviços: R${analise_serv['lucro']:,.2f}")
                print(f"   ✅ Serviços carregados!")
            else:
                print(f"   ⚠️ Aba de serviços não encontrada para {nome_mes}/{ano}")
        except Exception as e:
            import traceback
            print(f"   ❌ Erro ao carregar serviços: {e}")
            traceback.print_exc()

    # Dados financeiros (planilha offline)
    dados_financeiro = None
    if FINANCEIRO_DISPONIVEL:
        try:
            print(f"\n💰 Carregando dados financeiros...")
            fin, erro_fin = carregar_financeiro(fechamento=fechamento)
            if fin:
                dados_financeiro = fin
                sem = fin["semana"]
                print(f"   Contas da semana: {sem['qtd_contas']} | Total: R${sem['total_semana']:,.2f}")
                print(f"   Saldo em caixa: R${fin['saldo']['saldo']:,.2f}")
                print(f"   ✅ Financeiro carregado!")
            else:
                print(f"   ⚠️ {erro_fin}")
        except Exception as e:
            import traceback
            print(f"   ❌ Erro ao carregar financeiro: {e}")
            traceback.print_exc()

    return {
        "hoje": hoje, "nome_mes": nome_mes, "dia": dia,
        "vendas": vendas, "meta": meta, "faltam": meta - vendas,
        "servicos": dados["servicos"],
        "diferenca_mes": dif_mes, "dados_anterior": dados_ant,
        "semana_passada": sp, "semana_que_vem": sv,
        "dias_restantes": dias_rest, "valor_diario": val_diario,
        "aviso_prox": aviso_prox,
        "fechamento": fechamento, "insights": insights,
        "historico": historico, "dias_diarios": dias_diarios,
        "ausencias": ausencias,
        "analise_servicos": analise_serv,
        "financeiro": dados_financeiro,
    }


# =====================================================
# MENSAGEM TEXTO — SEMANAL
# =====================================================

import random

def escolher_frase_incentivo(r):
    """Escolhe uma frase de incentivo baseada no contexto atual."""
    pct_meta = (r["vendas"] / r["meta"] * 100) if r["meta"] > 0 else 0
    dia = r["dia"]
    acima_ano_ant = r["diferenca_mes"] is not None and r["diferenca_mes"] > 0
    sp = r["semana_passada"]
    semana_boa = sp and sp["diferenca"] > 0

    # Meta batida
    if r["faltam"] <= 0:
        return random.choice([
            "Que orgulho desse time! Agora é superar ainda mais! 🏆",
            "Meta batida e o mês nem acabou! Vocês são incríveis! ✨",
            "Resultado de um time que não desiste! Parabéns a cada uma! 🌟",
        ])

    # Reta final do mês (últimos 7 dias)
    if r["dias_restantes"] <= 7:
        return random.choice([
            "Reta final! Cada atendimento conta. Vamos com tudo! 🏁",
            "Últimos dias do mês — é agora que a gente mostra do que é feito! 💪",
            "Faltam poucos dias! Foco total e bora fechar esse mês com chave de ouro! 🔑",
            "A reta final é onde o time se destaca. Bora com tudo! 🚀",
        ])

    # Acima do ano anterior E semana boa
    if acima_ano_ant and semana_boa:
        return random.choice([
            "O time está voando! Manter esse ritmo e a meta vem! ✈️",
            "Números lindos! Cada dia de dedicação faz diferença. Continuem assim! 💚",
            "Essa energia tá contagiante! Bora manter! 🔥",
        ])

    # Acima do ano anterior mas semana fraca
    if acima_ano_ant and not semana_boa:
        return random.choice([
            "No acumulado estamos bem! Semana que vem a gente recupera. Confiamos no time! 💚",
            "Uma semana não define o mês. O saldo continua positivo, bora focar! 💪",
            "Estamos no caminho certo! Cada cliente que entra é uma oportunidade. 🌿",
        ])

    # Abaixo do ano anterior mas semana boa
    if not acima_ano_ant and semana_boa:
        return random.choice([
            "A semana mostrou que estamos reagindo! Bora manter esse ritmo! 📈",
            "O time está se superando! Se manter assim, a virada vem! 💪🔥",
            "Essa semana provou: quando o time se une, os resultados aparecem! 🌟",
        ])

    # Abaixo do ano anterior E semana fraca
    if not acima_ano_ant and not semana_boa:
        return random.choice([
            "Mês desafiador, mas nada que esse time não consiga virar! Juntas somos mais fortes! 💪💚",
            "Cada dia é uma página nova. Bora escrever uma história bonita essa semana! 📖✨",
            "Não é sobre o tropeço, é sobre levantar. E esse time sempre levanta! 🌱",
            "Desafios existem pra mostrar a força do time. Bora com tudo! 💚",
        ])

    # Genérico (começo do mês, poucos dados)
    return random.choice([
        "Mais uma semana, mais uma oportunidade de fazer acontecer! 💚",
        "Cada dia é uma chance de surpreender. Bora, time! 🌿",
        "Novo dia, nova meta, mesma garra! Vamos juntas! 💪",
        "O sucesso é construído dia a dia. E esse time constrói bonito! 🌟",
    ])


def gerar_mensagem_semanal(r):
    nome_mes = r["nome_mes"]
    dia = r["dia"]
    msg = f"Bom dia!!! 💚\nBora pra atualização de vendas em {nome_mes}?\n\n"
    msg += f"Vendas do dia 01 ao dia {dia:02d} de {nome_mes.lower()}: {formatar_moeda(r['vendas'])}\n"

    if r["diferenca_mes"] is not None:
        if r["diferenca_mes"] > 0:
            msg += f"\nOff: Já vendemos {formatar_moeda(r['diferenca_mes'])} a mais que {nome_mes.lower()} do ano passado! 🎉\n"
        elif r["diferenca_mes"] < 0:
            msg += f"\nAtenção: Estamos {formatar_moeda(abs(r['diferenca_mes']))} abaixo de {nome_mes.lower()} do ano passado.\n"

    if r["faltam"] > 0:
        msg += f"\nA meta é {formatar_moeda(r['meta'])}, então faltam {formatar_moeda(r['faltam'])} pra batermos a meta!!! 🫶🏻\n"
        msg += f"\nTemos {r['dias_restantes']:.0f} dias pro mês acabar (descontando domingos e feriados)\n"
        msg += f"{formatar_moeda(r['valor_diario'])} por dia! 💚"
    else:
        msg += f"\n🎉🎉🎉 META BATIDA!!! 🎉🎉🎉\n"
        msg += f"Meta: {formatar_moeda(r['meta'])} | Realizado: {formatar_moeda(r['vendas'])}\n"
        msg += f"Superamos em {formatar_moeda(abs(r['faltam']))}! 💚"

    sp = r["semana_passada"]
    if sp:
        msg += f"\n\n📊 Semana passada ({sp['inicio'].day:02d}/{sp['inicio'].month:02d} a {sp['fim'].day:02d}/{sp['fim'].month:02d}):\n"
        msg += f"Vendemos: {formatar_moeda(sp['vendas'])}\n"
        msg += f"Mesma semana em {sp['inicio'].year - 1}: {formatar_moeda(sp['vendas_ant'])}\n"
        if sp["diferenca"] > 0:
            msg += f"Mandamos {formatar_moeda(sp['diferenca'])} a mais ({sp['percentual']:+.1f}%)! 🔥"
        elif sp["diferenca"] < 0:
            msg += f"Ficamos {formatar_moeda(abs(sp['diferenca']))} abaixo ({sp['percentual']:+.1f}%). Bora virar! 💪"

    sv = r["semana_que_vem"]
    if sv:
        label = "Esta semana"  # Agora sempre retorna a semana ATUAL
        msg += f"\n\n📊 {label} ({sv['inicio'].day:02d}/{sv['inicio'].month:02d} a {sv['fim'].day:02d}/{sv['fim'].month:02d}):\n"
        msg += f"No ano passado vendemos {formatar_moeda(sv['vendas_ano_passado'])} nessa semana. Bora superar! 🚀"

    # Frase de incentivo
    frase = escolher_frase_incentivo(r)
    msg += f"\n\n💬 {frase}"

    return msg


# =====================================================
# MENSAGEM TEXTO — FECHAMENTO MENSAL
# =====================================================

def gerar_mensagem_fechamento(r):
    nome_mes = r["nome_mes"]
    ano = r["hoje"].year
    ins = r.get("insights", {})

    bateu_meta = r["faltam"] <= 0

    msg = f"Fechamos {nome_mes}! 💚🌿\n\n"

    if bateu_meta:
        msg += f"🎉🎉🎉 META BATIDA!!! 🎉🎉🎉\n"
        msg += f"Meta: {formatar_moeda(r['meta'])} | Vendemos: {formatar_moeda(r['vendas'])}\n"
        msg += f"Superamos em {formatar_moeda(abs(r['faltam']))}! Parabéns, time!! 👏💚\n"
    else:
        msg += f"Vendas do mês: {formatar_moeda(r['vendas'])}\n"
        msg += f"Meta era {formatar_moeda(r['meta'])} — faltaram {formatar_moeda(r['faltam'])}.\n"
        msg += f"Mês difícil, mas aprendemos muito! 💪\n"

    # Comparativo ajustado por dias úteis (REAIS da planilha)
    if ins.get("dias_uteis_atual") and ins.get("dias_uteis_anterior"):
        du_atual = ins["dias_uteis_atual"]
        du_ant = ins["dias_uteis_anterior"]
        msg += f"\n📊 Comparativo justo com {nome_mes}/{ano-1}:\n"
        msg += f"Abrimos {du_atual} dias este ano vs {du_ant} dias no ano passado\n"
        msg += f"Venda por dia aberto: {formatar_moeda(ins['venda_por_dia_util_atual'])} vs {formatar_moeda(ins['venda_por_dia_util_ant'])}\n"
        if ins["diff_por_dia_util"] > 0:
            msg += f"Vendemos {formatar_moeda(ins['diff_por_dia_util'])} a mais POR DIA! ({ins['pct_por_dia_util']:+.1f}%) 🔥\n"
        elif ins["diff_por_dia_util"] < 0:
            msg += f"Ficamos {formatar_moeda(abs(ins['diff_por_dia_util']))} abaixo por dia ({ins['pct_por_dia_util']:+.1f}%).\n"
        if du_atual != du_ant:
            msg += f"⚡ Lembre: tivemos {'menos' if du_atual < du_ant else 'mais'} dias abertos este ano!\n"

    msg += f"\nBora marcar nossa reunião pra falar mais sobre? 📋✨"

    return msg


# =====================================================
# LOGO
# =====================================================

def carregar_logo_base64():
    for nome in ["logo.png", "Logo.png", "LOGO.png", "LOGO_BMQ_COR_07.png"]:
        caminho = os.path.join(PASTA_SCRIPT, nome)
        if os.path.exists(caminho):
            with open(caminho, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


def analisar_picos_fornecedores(plano_fornecedores):
    """Analisa picos de vencimento (múltiplos fornecedores no mesmo dia)."""
    if not plano_fornecedores or not plano_fornecedores.get("fornecedores"):
        return ""
    
    # Agrupar por data de vencimento
    vencimentos_por_data = {}
    for forn in plano_fornecedores.get("fornecedores", []):
        melhor = forn.get("melhor_prazo")
        alerta_pico = forn.get("alerta_pico")
        
        if alerta_pico:
            data = alerta_pico.get("data")
            if data:
                if data not in vencimentos_por_data:
                    vencimentos_por_data[data] = []
                vencimentos_por_data[data].append(forn["nome"])
    
    # Detectar picos (múltiplos no mesmo dia)
    picos_html = ""
    for data in sorted(vencimentos_por_data.keys()):
        fornecedores = vencimentos_por_data[data]
        if len(fornecedores) > 1:
            # Pico detectado!
            dia_nome = ['Seg','Ter','Qua','Qui','Sex','Sab','Dom'][data.weekday()]
            data_str = data.strftime("%d/%m")
            
            alerta_color = "#B84527"  # Crítico por padrão
            nivel_texto = "🚨 CRÍTICO"
            
            forn_lista = "<br>      • ".join(fornecedores)
            picos_html += f"""<div style="background:rgba(184,69,39,0.1);border-radius:12px;padding:14px;margin-bottom:12px;border-left:4px solid {alerta_color}">
                <div style="font-weight:700;color:{alerta_color};margin-bottom:8px">{nivel_texto} — {data_str} ({dia_nome})</div>
                <div style="font-size:0.85em;color:#333;margin-bottom:8px">
                    <strong>{len(fornecedores)} fornecedores vencendo JUNTOS:</strong><br>
                    • {forn_lista}
                </div>
                <div style="background:rgba(184,69,39,0.08);border-radius:8px;padding:10px;font-size:0.82em;border-left:2px solid {alerta_color}">
                    <strong>💡 Ação Rápida:</strong> Negocie prazos DIFERENTES com esses fornecedores para distribuir os vencimentos ao longo da semana. Não libere todos com o mesmo prazo!
                </div>
            </div>"""
    
    if picos_html:
        return f"""<div style="background:linear-gradient(135deg,rgba(184,69,39,0.05),rgba(230,168,52,0.05));border-radius:14px;padding:16px;margin-bottom:16px;border:2px solid rgba(184,69,39,0.2)">
            <h4 style="margin:0 0 12px;color:#B84527;font-size:1em">🎯 Análise Rigorosa — Picos de Vencimento Detectados</h4>
            {picos_html}
        </div>"""
    
    return ""


# =====================================================
# HTML
# =====================================================

def gerar_html(r, mensagem_texto):
    nome_mes = r.get("nome_mes", "Mês")
    dia = r.get("dia", 1)
    hoje = r.get("hoje") or date.today()  # Fallback se 'hoje' não existir
    ano = hoje.year
    vendas = r.get("vendas", 0)
    meta = r.get("meta", 1)
    pct_meta = (vendas / meta * 100) if meta > 0 else 0
    faltam = r.get("faltam", meta - vendas)
    fechamento = r.get("fechamento", False)
    insights = r.get("insights", {})
    historico = r.get("historico", {})
    dias_restantes = r.get("dias_restantes", 1)
    valor_diario = r.get("valor_diario", 0)

    logo_b64 = carregar_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Bem Me Quer" class="logo">' if logo_b64 else '<div class="logo-text">Bem Me Quer<br><span>Cosméticos</span></div>'

    modo_titulo = "📊 Fechamento Mensal" if fechamento else "📊 Relatório de Vendas"
    modo_badge = '<span class="badge-fechamento">FECHAMENTO</span>' if fechamento else ""

    # ── Card semana passada ──
    card_sp = ""
    sp = r["semana_passada"]
    if sp:
        cor = "#324D38" if sp["diferenca"] >= 0 else "#B84527"
        icone = "🔥" if sp["diferenca"] >= 0 else "💪"
        txt = f"+{formatar_moeda(sp['diferenca'])} ({sp['percentual']:+.1f}%)" if sp["diferenca"] >= 0 else f"{formatar_moeda(sp['diferenca'])} ({sp['percentual']:+.1f}%)"
        card_sp = f"""<div class="card"><div class="card-header">📊 Semana Passada ({sp['inicio'].day:02d}/{sp['inicio'].month:02d} a {sp['fim'].day:02d}/{sp['fim'].month:02d})</div>
        <div class="card-body">
            <div class="stat-row"><span>Esta semana:</span><span class="stat-value">{formatar_moeda(sp['vendas'])}</span></div>
            <div class="stat-row"><span>Mesma semana {sp['inicio'].year-1}:</span><span class="stat-value">{formatar_moeda(sp['vendas_ant'])}</span></div>
            <div class="stat-row highlight" style="color:{cor}"><span>{icone} Diferença:</span><span class="stat-value">{txt}</span></div>
        </div></div>"""

    # ── Card semana atual/próxima ──
    card_sv = ""
    sv = r["semana_que_vem"]
    if sv and not fechamento:
        lb = "📊 Esta Semana"  # Agora sempre retorna a semana ATUAL
        card_sv = f"""<div class="card preview-card"><div class="card-header">{lb} ({sv['inicio'].day:02d}/{sv['inicio'].month:02d} a {sv['fim'].day:02d}/{sv['fim'].month:02d})</div>
        <div class="card-body">
            <div class="stat-row"><span>No ano passado vendemos:</span><span class="stat-value highlight-value">{formatar_moeda(sv['vendas_ano_passado'])}</span></div>
            <p class="motivacao">Bora superar! 🚀</p>
        </div></div>"""

    # ── Aviso próximo mês ──
    aviso_html = ""
    if r["aviso_prox"]:
        av = r["aviso_prox"]
        sug = "".join(f"<code>{s}</code> " for s in av["sugestoes"])
        aviso_html = f'<div class="aviso">⚠️ <strong>Faltam {av["dias_faltando"]} dias!</strong> Crie a aba de {av["mes_nome"]}/{av["ano"]}.<br>Nomes aceitos: {sug}</div>'

    # ── Comparativo mensal ──
    comp_html = ""
    if r["diferenca_mes"] is not None:
        if r["diferenca_mes"] >= 0:
            comp_html = f'<div class="comparativo positivo">🎉 <strong>{formatar_moeda(r["diferenca_mes"])}</strong> a mais que {nome_mes.lower()} do ano passado!</div>'
        else:
            comp_html = f'<div class="comparativo negativo">⚠️ <strong>{formatar_moeda(abs(r["diferenca_mes"]))}</strong> abaixo de {nome_mes.lower()} do ano passado.</div>'

    # ── Comparativo justo por dia útil (fechamento) ──
    comp_justo_html = ""
    if fechamento and insights.get("dias_uteis_atual"):
        du_a = insights["dias_uteis_atual"]
        du_ant = insights["dias_uteis_anterior"]
        cor_ju = "#324D38" if insights["diff_por_dia_util"] >= 0 else "#B84527"
        seta_ju = "▲" if insights["diff_por_dia_util"] >= 0 else "▼"
        nota_dias = ""
        if du_a != du_ant:
            nota_dias = f"<br><small>⚡ {nome_mes}/{ano}: {du_a:.0f} dias abertos vs {nome_mes}/{ano-1}: {du_ant:.0f} dias abertos</small>"
        comp_justo_html = f"""
        <div class="comparativo-justo">
            <h3>⚖️ Comparativo Justo (por dia útil)</h3>
            <div class="justo-grid">
                <div class="justo-item"><div class="justo-label">{ano}</div><div class="justo-value">{formatar_moeda(insights['venda_por_dia_util_atual'])}<span>/dia</span></div></div>
                <div class="justo-item"><div class="justo-label">{ano-1}</div><div class="justo-value">{formatar_moeda(insights['venda_por_dia_util_ant'])}<span>/dia</span></div></div>
                <div class="justo-item result"><div class="justo-label">Diferença</div><div class="justo-value" style="color:{cor_ju}">{seta_ju} {formatar_moeda(abs(insights['diff_por_dia_util']))} ({insights['pct_por_dia_util']:+.1f}%)</div></div>
            </div>
            {nota_dias}
        </div>"""

    # ── Histórico de semanas ──
    historico_html = ""
    semanas = historico.get("semanas", [])
    if semanas:
        rows = ""
        for s in semanas:
            cor_r = "#324D38" if s["diferenca"] >= 0 else "#B84527"
            seta = "▲" if s["diferenca"] >= 0 else "▼"
            rows += f'<tr><td>{s["periodo"]}</td><td class="num">{formatar_moeda(s["vendas"])}</td><td class="num">{formatar_moeda(s["vendas_ant"])}</td><td class="num" style="color:{cor_r};font-weight:600">{seta} {formatar_moeda(abs(s["diferenca"]))} ({s["percentual"]:+.1f}%)</td></tr>'
        historico_html = f"""<div class="section"><h2>📅 Histórico de Semanas — {nome_mes}</h2>
            <div class="table-wrapper"><table><thead><tr><th>Período</th><th>Vendas</th><th>Ano Anterior</th><th>Diferença</th></tr></thead><tbody>{rows}</tbody></table></div></div>"""

    # ── INSIGHTS (FECHAMENTO) ──
    insights_html = ""
    if fechamento and insights:
        insight_cards = f"""<div class="insight-grid">
            <div class="insight-card"><div class="insight-icon">💰</div><div class="insight-label">Ticket Médio Diário</div><div class="insight-value">{formatar_moeda(insights['ticket_medio'])}</div><div class="insight-sub">{insights['dias_trabalhados']} dias com vendas</div></div>
            <div class="insight-card"><div class="insight-icon">🏆</div><div class="insight-label">Melhor Dia da Semana</div><div class="insight-value">{insights['melhor_dia_semana']}</div><div class="insight-sub">Média: {formatar_moeda(insights['melhor_dia_semana_media'])}</div></div>
            <div class="insight-card"><div class="insight-icon">📉</div><div class="insight-label">Dia Mais Fraco</div><div class="insight-value">{insights['pior_dia_semana']}</div><div class="insight-sub">Média: {formatar_moeda(insights['pior_dia_semana_media'])}</div></div>
            <div class="insight-card"><div class="insight-icon">{"📈" if insights["tendencia_pct"]>=0 else "📉"}</div><div class="insight-label">Tendência do Mês</div><div class="insight-value" style="color:{"#324D38" if insights["tendencia_pct"]>=0 else "#B84527"}">{insights["tendencia_pct"]:+.1f}%</div><div class="insight-sub">{"Melhorou" if insights["tendencia_pct"]>=0 else "Caiu"} na 2ª metade</div></div>
        </div>"""

        # Média por dia da semana
        media_dias_html = ""
        if insights.get("media_por_dia_semana"):
            max_val = max(insights["media_por_dia_semana"].values()) or 1
            bars = ""
            for dn, val in insights["media_por_dia_semana"].items():
                pct_b = (val / max_val * 100) if max_val > 0 else 0
                bars += f'<div class="bar-row"><span class="bar-label">{dn[:3]}</span><div class="bar-track"><div class="bar-fill" style="width:{pct_b:.0f}%"></div></div><span class="bar-value">{formatar_moeda(val)}</span></div>'
            media_dias_html = f'<div class="chart-section"><h3>Média por Dia da Semana</h3>{bars}</div>'

        # TOP 5
        top5_html = ""
        if insights.get("top5"):
            medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
            rows_t = "".join(f'<tr><td>{medals[i]}</td><td>Dia {d["dia"]:02d} ({d["dia_semana_nome"]})</td><td class="num" style="font-weight:700">{formatar_moeda(d["produtos"])}</td></tr>' for i, d in enumerate(insights["top5"]))
            top5_html = f'<div class="mini-table"><h3>🏆 TOP 5 Dias de Venda</h3><table><tbody>{rows_t}</tbody></table></div>'

        # Bottom 3
        bottom3_html = ""
        if insights.get("bottom3"):
            rows_b = "".join(f'<tr><td>Dia {d["dia"]:02d} ({d["dia_semana_nome"]})</td><td class="num">{formatar_moeda(d["produtos"])}</td></tr>' for d in insights["bottom3"])
            bottom3_html = f'<div class="mini-table fraco"><h3>⚠️ Dias Mais Fracos</h3><table><tbody>{rows_b}</tbody></table></div>'

        # Serviços
        servicos_html = ""
        if insights.get("total_servicos", 0) > 0:
            servicos_html = f'<div class="insight-card wide"><div class="insight-icon">💆‍♀️</div><div class="insight-label">Serviços no Mês</div><div class="insight-value">{formatar_moeda(insights["total_servicos"])}</div><div class="insight-sub">Semana {insights.get("semana_mais_servicos","?")} teve mais serviços</div></div>'

        # Comparativo semanal
        comp_sem_html = ""
        if insights.get("comparativo_semanal"):
            rows_cs = ""
            for cs in insights["comparativo_semanal"]:
                cor_cs = "#324D38" if cs["diferenca"] >= 0 else "#B84527"
                seta_cs = "▲" if cs["diferenca"] >= 0 else "▼"
                rows_cs += f'<tr><td>Semana {cs["semana"]} ({cs["dia_inicio"]:02d}-{cs["dia_fim"]:02d})</td><td class="num">{formatar_moeda(cs["vendas"])}</td><td class="num">{formatar_moeda(cs["vendas_ant"])}</td><td class="num" style="color:{cor_cs};font-weight:600">{seta_cs} {cs["percentual"]:+.1f}%</td></tr>'
            comp_sem_html = f'<div class="section"><h3>📊 Comparativo Semanal vs Ano Anterior</h3><div class="table-wrapper"><table><thead><tr><th>Semana</th><th>{ano}</th><th>{ano-1}</th><th>Variação</th></tr></thead><tbody>{rows_cs}</tbody></table></div></div>'

        # Dias fracos — vale a pena abrir?
        dias_fracos_html = ""
        if insights.get("dias_fracos"):
            rows_df = ""
            for df in insights["dias_fracos"]:
                rows_df += f'<tr><td>Dia {df["dia"]:02d} ({df["dia_semana_nome"]})</td><td class="num">{formatar_moeda(df["produtos"])}</td><td class="num" style="color:#B84527">{df["pct_do_ticket"]:.0f}% do ticket médio</td></tr>'
            dias_fracos_html = f"""<div class="section" style="border:1px solid rgba(184,69,39,0.2)">
                <h3>🤔 Vale a Pena Abrir? — Dias com vendas muito abaixo</h3>
                <p style="font-size:0.85em;color:#888;margin-bottom:12px">Dias com vendas abaixo de 30% do ticket médio ({formatar_moeda(insights["ticket_medio"])})</p>
                <div class="table-wrapper"><table><thead><tr><th>Dia</th><th>Vendas</th><th>Comparativo</th></tr></thead><tbody>{rows_df}</tbody></table></div>
            </div>"""

        # Dias fechados (loja não abriu, exceto domingos)
        dias_fechados_html = ""
        if insights.get("dias_fechados"):
            lista_f = ", ".join(f'dia {d["dia"]:02d} ({d["dia_semana_nome"]})' for d in insights["dias_fechados"])
            dias_fechados_html = f'<div class="aviso" style="margin-top:0">📅 <strong>Dias que a loja não abriu:</strong> {lista_f}</div>'

        # Ausências da equipe
        ausencias_html = ""
        aus = r.get("ausencias", [])
        if aus:
            rows_aus = ""
            for a in aus:
                rows_aus += f'<tr><td><strong>{a["nome"]}</strong></td><td>{a["motivo"]}</td><td>Dia {a["dia_inicio"]:02d} a {a["dia_fim"]:02d}</td></tr>'
            ausencias_html = f"""<div class="section" style="border:1px solid rgba(184,69,39,0.15)">
                <h3>👥 Ausências da Equipe</h3>
                <p style="font-size:0.85em;color:#888;margin-bottom:12px">Colaboradores ausentes impactam diretamente nas vendas</p>
                <div class="table-wrapper"><table><thead><tr><th>Colaborador</th><th>Motivo</th><th>Período</th></tr></thead><tbody>{rows_aus}</tbody></table></div>
            </div>"""

        insights_html = f"""<div class="section fechamento-section"><h2>📊 Fechamento de {nome_mes} — Insights</h2>
            {insight_cards}
            <div class="insights-grid-2col">{media_dias_html}<div>{top5_html}{bottom3_html}</div></div>
            {servicos_html}{comp_sem_html}</div>
            {dias_fracos_html}
            {dias_fechados_html}
            {ausencias_html}"""

    msg_js = mensagem_texto.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    # ── SEÇÃO DE SERVIÇOS ──
    servicos_section_html = ""
    serv = r.get("analise_servicos")
    if serv:

        # Cards resumo — SERVIÇO vs COMPRAS separados
        cor_lucro_serv = "#B84527" if serv["lucro_servico"] < 0 else "#324D38"
        icone_lucro_serv = "⚠️" if serv["lucro_servico"] < 0 else "✅"

        # "Traduzindo" o resultado do serviço
        if serv["lucro_servico"] >= 0:
            traduzindo_resultado = f'<div style="background:#eef4e8;border-radius:10px;padding:14px;margin-top:10px;font-size:0.85em;border:1px solid rgba(50,77,56,0.12)">📖 <strong>Traduzindo:</strong> A profissional custou {formatar_moeda(serv["custo_total"])} no mês e só com os pagamentos de sobrancelha ({formatar_moeda(serv["receita_servico_puro"])}) já se pagou, sobrando <strong style="color:#324D38">{formatar_moeda(serv["lucro_servico"])}</strong> de lucro. Fora isso, {serv["qtd_compras"]} clientes compraram {formatar_moeda(serv["receita_compras"])} em produtos!</div>'
        else:
            resultado_real = serv["lucro_servico"] + serv["receita_compras"]
            if resultado_real > 0:
                traduzindo_resultado = f'<div style="background:#fef9ee;border-radius:10px;padding:14px;margin-top:10px;font-size:0.85em;border:1px solid rgba(230,168,52,0.2)">📖 <strong>Traduzindo:</strong> Só com sobrancelha, a profissional deu prejuízo de {formatar_moeda(abs(serv["lucro_servico"]))} (custou {formatar_moeda(serv["custo_total"])} e faturou {formatar_moeda(serv["receita_servico_puro"])}). Porém, {serv["qtd_compras"]} clientes compraram produtos no valor de {formatar_moeda(serv["receita_compras"])}. <strong style="color:#324D38">No total, o serviço gerou {formatar_moeda(resultado_real)} de lucro!</strong> A profissional atrai clientes que compram.</div>'
            else:
                traduzindo_resultado = f'<div style="background:rgba(184,69,39,0.06);border-radius:10px;padding:14px;margin-top:10px;font-size:0.85em;border:1px solid rgba(184,69,39,0.15)">📖 <strong>Traduzindo:</strong> A profissional custou {formatar_moeda(serv["custo_total"])} e faturou {formatar_moeda(serv["receita_servico_puro"])} em sobrancelhas + {formatar_moeda(serv["receita_compras"])} em compras de produtos. <strong style="color:#B84527">Mesmo assim, ficou {formatar_moeda(abs(resultado_real))} negativo.</strong> Vale avaliar ações pra aumentar os atendimentos ou as compras.</div>'

        serv_resumo = f"""
            <div class="insight-grid" style="margin-bottom:6px">
                <div class="insight-card" style="background:#fff"><div class="insight-icon">👥</div><div class="insight-label">Atendimentos</div><div class="insight-value">{serv['total_atendimentos']}</div><div class="insight-sub">{serv['media_atend_por_dia']:.1f} por dia</div></div>
                <div class="insight-card" style="background:#fff"><div class="insight-icon">💸</div><div class="insight-label">Custo Profissional</div><div class="insight-value">{formatar_moeda(serv['custo_total'])}</div><div class="insight-sub">{serv['dias_profissional']} dias × {formatar_moeda(serv['custo_diaria'])}</div></div>
            </div>
            <div class="justo-grid" style="margin-bottom:6px">
                <div class="justo-item" style="background:#fff"><div class="justo-label">💇 Pagaram Sobrancelha</div><div class="justo-value">{serv['qtd_servico']}</div><div class="justo-label" style="margin-top:4px">Receita: {formatar_moeda(serv['receita_servico_puro'])}</div><div class="justo-label">Ticket médio: {formatar_moeda(serv['ticket_medio_servico'])}</div></div>
                <div class="justo-item" style="background:#fff"><div class="justo-label">🛍️ Compraram Produto<br><small>(ganharam a sobrancelha)</small></div><div class="justo-value">{serv['qtd_compras']}</div><div class="justo-label" style="margin-top:4px">Receita: {formatar_moeda(serv['receita_compras'])}</div><div class="justo-label">Ticket médio: {formatar_moeda(serv['ticket_medio_compra'])}</div></div>
                <div class="justo-item result" style="background:rgba(255,255,255,0.7)"><div class="justo-label">{icone_lucro_serv} Resultado Serviço</div><div class="justo-value" style="color:{cor_lucro_serv}">{formatar_moeda(serv['lucro_servico'])}</div><div class="justo-label" style="margin-top:4px">Serviço - Custo</div></div>
            </div>
            {traduzindo_resultado}
            <div style="text-align:center;margin:10px 0;font-size:0.82em;color:#8BA279">
                Taxa de conversão: <strong>{serv['taxa_conversao']:.0f}%</strong> dos atendimentos resultaram em compra de produto
            </div>"""

        # Formas de pagamento
        pg_rows = ""
        for pg_nome, pg_count in serv["pagamentos_ranking"]:
            pct_pg = (pg_count / serv["total_atendimentos"] * 100) if serv["total_atendimentos"] > 0 else 0
            pg_rows += f'<div class="bar-row"><span class="bar-label" style="width:100px">{pg_nome}</span><div class="bar-track"><div class="bar-fill" style="width:{pct_pg:.0f}%"></div></div><span class="bar-value">{pg_count} ({pct_pg:.0f}%)</span></div>'
        serv_pagamentos = f'<div class="chart-section" style="margin-bottom:18px;background:#fff"><h3>💳 Formas de Pagamento</h3>{pg_rows}</div>' if pg_rows else ""

        # Clientes novas vs retorno
        serv_clientes = f"""<div class="justo-grid" style="margin-bottom:18px">
            <div class="justo-item" style="background:#fff"><div class="justo-label">Clientes Únicas</div><div class="justo-value">{serv['clientes_mes_total']}</div></div>
            <div class="justo-item" style="background:rgba(50,77,56,0.06)"><div class="justo-label">Já Vieram Antes</div><div class="justo-value" style="color:#324D38">{serv['clientes_retorno']}</div></div>
            <div class="justo-item" style="background:#fff"><div class="justo-label">Clientes Novas</div><div class="justo-value" style="color:#B84527">{serv['clientes_novas']}</div></div>
        </div>
        <p style="text-align:center;font-size:0.85em;color:#8BA279;margin-bottom:14px">
            {serv['pct_retorno']:.0f}% das clientes deste mês já vieram antes — {"ótima fidelização!" if serv["pct_retorno"] >= 40 else "oportunidade de fidelizar mais!"}
        </p>"""

        # Top recorrentes
        serv_recorrentes = ""
        if serv.get("top_recorrentes"):
            rows_rec = ""
            for i, c in enumerate(serv["top_recorrentes"][:10]):
                medal = ["🥇","🥈","🥉"][i] if i < 3 else f"{i+1}º"
                rows_rec += f'<tr><td>{medal}</td><td>{c["nome"]}</td><td class="num">{c["vezes"]}x</td><td class="num">{c["meses_distintos"]} meses</td></tr>'
            serv_recorrentes = f"""<div class="mini-table" style="margin-bottom:18px;background:#fff">
                <h3>🏆 Top 10 Clientes Mais Fiéis (desde ago/24)</h3>
                <table><thead><tr><th></th><th>Cliente</th><th>Vezes</th><th>Meses</th></tr></thead><tbody>{rows_rec}</tbody></table>
            </div>"""

        # Comparativos
        serv_comp = ""
        comp_ant = serv.get("comparativo_mes_anterior", {})
        comp_aa = serv.get("comparativo_ano_anterior", {})
        if comp_ant.get("atendimentos", 0) > 0 or comp_aa.get("atendimentos", 0) > 0:
            rows_comp = ""
            if comp_ant.get("atendimentos", 0) > 0:
                dif_atend = serv["total_atendimentos"] - comp_ant["atendimentos"]
                cor_ca = "#324D38" if dif_atend >= 0 else "#B84527"
                seta_ca = "▲" if dif_atend >= 0 else "▼"
                rows_comp += f'<tr><td>Mês anterior</td><td class="num">{comp_ant["atendimentos"]}</td><td class="num">{formatar_moeda(comp_ant["receita"])}</td><td class="num" style="color:{cor_ca}">{seta_ca} {abs(dif_atend)} atend.</td></tr>'
            if comp_aa.get("atendimentos", 0) > 0:
                dif_aa = serv["total_atendimentos"] - comp_aa["atendimentos"]
                cor_caa = "#324D38" if dif_aa >= 0 else "#B84527"
                seta_caa = "▲" if dif_aa >= 0 else "▼"
                rows_comp += f'<tr><td>Mesmo mês {ano-1}</td><td class="num">{comp_aa["atendimentos"]}</td><td class="num">{formatar_moeda(comp_aa["receita"])}</td><td class="num" style="color:{cor_caa}">{seta_caa} {abs(dif_aa)} atend.</td></tr>'
            serv_comp = f'<div class="table-wrapper"><table><thead><tr><th>Comparativo</th><th>Atend.</th><th>Receita</th><th>Diferença</th></tr></thead><tbody>{rows_comp}</tbody></table></div>'

        # Impacto da profissional nas vendas de PRODUTOS + traduzindo
        impacto_html = ""
        imp = insights.get("impacto_profissional", {})
        if imp.get("dias_com", 0) > 0 and imp.get("dias_sem", 0) > 0:
            cor_imp = "#324D38" if imp["diferenca"] >= 0 else "#B84527"
            seta_imp = "▲" if imp["diferenca"] >= 0 else "▼"

            if imp["percentual"] >= 15:
                traduzindo_imp = f'📖 <strong>Traduzindo:</strong> Nos dias que a profissional está na loja, as vendas de PRODUTOS são {imp["percentual"]:.0f}% maiores (média de {formatar_moeda(imp["media_com"])} vs {formatar_moeda(imp["media_sem"])}). Ela atrai clientes que acabam comprando! Considere ampliar os dias dela.'
            elif imp["percentual"] >= 5:
                traduzindo_imp = f'📖 <strong>Traduzindo:</strong> Há uma leve alta de {imp["percentual"]:.0f}% nas vendas de produtos nos dias da profissional. O impacto é positivo mas moderado.'
            elif imp["percentual"] >= -5:
                traduzindo_imp = f'📖 <strong>Traduzindo:</strong> As vendas de produtos são praticamente iguais com ou sem a profissional (diferença de apenas {abs(imp["percentual"]):.0f}%). O serviço não atrapalha, mas também não puxa vendas de forma significativa.'
            else:
                traduzindo_imp = f'📖 <strong>Traduzindo:</strong> Nos dias sem profissional, as vendas de produtos são {abs(imp["percentual"]):.0f}% maiores. Isso pode acontecer se os sábados forem naturalmente mais fortes — não significa que a profissional afasta clientes.'

            impacto_html = f"""<div style="background:#fff;border-radius:12px;padding:18px;margin-bottom:18px;border:1px dashed #8BA279">
                <h3 style="margin-top:0">🔍 Impacto da Profissional nas Vendas de Produtos</h3>
                <div class="justo-grid">
                    <div class="justo-item"><div class="justo-label">Dias COM profissional<br><small>(ter/qui/sex — {imp['dias_com']} dias)</small></div><div class="justo-value">{formatar_moeda(imp['media_com'])}<br><small>média/dia</small></div></div>
                    <div class="justo-item"><div class="justo-label">Dias SEM profissional<br><small>(seg/qua/sáb — {imp['dias_sem']} dias)</small></div><div class="justo-value">{formatar_moeda(imp['media_sem'])}<br><small>média/dia</small></div></div>
                    <div class="justo-item result"><div class="justo-label">Diferença</div><div class="justo-value" style="color:{cor_imp}">{seta_imp} {formatar_moeda(abs(imp['diferenca']))}<br><small>({imp['percentual']:+.1f}%)</small></div></div>
                </div>
                <div style="background:#fafaf6;border-radius:10px;padding:12px;margin-top:12px;font-size:0.85em">{traduzindo_imp}</div>
            </div>"""

        # Alerta de queda no mês
        alerta_queda_html = ""
        aq = serv.get("alerta_queda")
        if aq:
            sugestoes = [
                "Divulgar promoção relâmpago nas redes sociais",
                "Oferecer combo especial (sobrancelha + produto) com desconto",
                "Enviar mensagem de reativação pra clientes que não vieram esse mês",
                "Criar promoção \"traga uma amiga\" com desconto pra ambas",
            ]
            import random
            random.seed(aq["semana_para"])
            sug = random.sample(sugestoes, 2)
            alerta_queda_html = f"""<div style="background:rgba(230,168,52,0.08);border-radius:12px;padding:18px;margin-bottom:18px;border:1px solid rgba(230,168,52,0.25)">
                <h3 style="margin-top:0;color:#8B6914">📉 Atenção: Queda de {aq['pct_queda']:.0f}% na {aq['semana_para']}ª semana</h3>
                <p style="font-size:0.88em;margin-bottom:10px">Os atendimentos caíram de <strong>{aq['atend_de']}</strong> (semana {aq['semana_de']}) para <strong>{aq['atend_para']}</strong> (semana {aq['semana_para']}). Isso é normal no meio/fim do mês, mas vale agir!</p>
                <p style="font-size:0.85em;margin-bottom:4px"><strong>💡 Sugestões pra reagir:</strong></p>
                <p style="font-size:0.85em;margin:0;padding-left:8px">• {sug[0]}</p>
                <p style="font-size:0.85em;margin:0;padding-left:8px">• {sug[1]}</p>
            </div>"""

        # Resumo da SEMANA — separado
        serv_semana_html = ""
        rs = serv.get("resumo_semana")
        if rs:
            serv_semana_html = f"""<div style="background:#fff;border-radius:14px;padding:18px;margin-bottom:18px;border:1px solid rgba(139,162,121,0.3)">
                <h3 style="margin-top:0">📅 Semana {rs['inicio'].strftime('%d/%m')} a {rs['fim'].strftime('%d/%m')}</h3>
                <div class="justo-grid">
                    <div class="justo-item"><div class="justo-label">💇 Pagaram Sobrancelha</div><div class="justo-value">{rs['qtd_servico']}</div><div class="justo-label" style="margin-top:4px">Receita: {formatar_moeda(rs['receita_servico'])}</div><div class="justo-label">Ticket: {formatar_moeda(rs['ticket_servico'])}</div></div>
                    <div class="justo-item"><div class="justo-label">🛍️ Compraram Produto</div><div class="justo-value">{rs['qtd_compras']}</div><div class="justo-label" style="margin-top:4px">Receita: {formatar_moeda(rs['receita_compras'])}</div><div class="justo-label">Ticket: {formatar_moeda(rs['ticket_compra'])}</div></div>
                    <div class="justo-item result"><div class="justo-label">Total Atendimentos</div><div class="justo-value">{rs['atendimentos']}</div></div>
                </div>
            </div>"""

        servicos_section_html = f"""<div class="section" style="border:2px solid #8BA279;background:rgba(139,162,121,0.06)">
            <h2>💆‍♀️ Serviços — Sobrancelha</h2>
            <div class="subtitle" style="color:#8BA279;font-size:0.82em;margin-top:-14px;margin-bottom:18px">Acumulado de {nome_mes} (01/{r['hoje'].month:02d} a {dia:02d}/{r['hoje'].month:02d}/{ano})</div>
            {serv_semana_html}
            <h3 style="border-top:1px solid rgba(50,77,56,0.1);padding-top:16px;margin-top:4px">📊 Acumulado do Mês</h3>
            {serv_resumo}
            {impacto_html}
            {alerta_queda_html}
            {serv_pagamentos}
            {serv_clientes}
            {serv_recorrentes}
            {serv_comp}
        </div>"""

    # ── SEÇÃO FINANCEIRA ──
    financeiro_section_html = ""
    fin = r.get("financeiro")
    if fin:
        sem = fin["semana"]
        proj = fin["projecao"]
        saldo = fin["saldo"]
        saldos_contas = fin.get("saldos_contas", {})
        fin_insights = fin.get("insights", [])
        nubank = fin.get("nubank", {})
        nubank_aval = fin.get("nubank_avaliacao", {})
        meta_ads = fin.get("meta_ads", {})
        adiamentos = fin.get("adiamentos", [])
        mensagem_wpp = fin.get("mensagem_wpp", "")
        alertas_saz = fin.get("alertas_sazonais", [])
        teto_diario_info = fin.get("teto_diario", {})

        # Saldo vs Total semana
        cobre = saldo["saldo"] >= sem["total_semana"]
        cor_saldo = "#324D38" if cobre else "#B84527"
        sobra_falta = saldo["saldo"] - sem["total_semana"]
        icone_caixa = "✅" if cobre else "🚨"

        # ── Nubank / Reserva no topo ──
        nub_saldo = saldos_contas.get("nubank", 0)
        nub_pct = saldos_contas.get("nubank_pct_meta", 0)
        nub_falta = saldos_contas.get("nubank_falta_meta", 0)
        cor_nub_barra = "#8B5CF6" if nub_pct >= 50 else "#E6A834" if nub_pct >= 25 else "#B84527"

        nubank_topo = f"""<div style="background:linear-gradient(135deg,#1a1a2e,#2d2d44);border-radius:14px;padding:16px;margin-bottom:16px;color:#fff">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <div><span style="font-size:1.1em">💜</span> <strong>Reserva Nubank (CDB)</strong></div>
                <div style="font-size:0.8em;opacity:0.7">Meta: R${50000:,.2f}</div>
            </div>
            <div style="font-size:1.6em;font-weight:700;margin-bottom:8px">{formatar_moeda(nub_saldo)}</div>
            <div style="background:rgba(255,255,255,0.15);border-radius:20px;height:10px;margin-bottom:8px;overflow:hidden">
                <div style="background:{cor_nub_barra};height:100%;width:{min(nub_pct, 100):.0f}%;border-radius:20px;transition:width 0.5s"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.82em;opacity:0.8">
                <span>{nub_pct:.0f}% da meta</span>
                <span>Faltam {formatar_moeda(nub_falta)}</span>
            </div>
            {'<div style=\"margin-top:10px;padding:10px;background:rgba(255,255,255,0.08);border-radius:8px;font-size:0.82em\">' + nubank_aval.get('mensagem', '') + '</div>' if nubank_aval.get('usar') else ''}
        </div>"""

        # ── Alertas sazonais ──
        sazonal_html = ""
        if alertas_saz:
            items_saz = ""
            for a in alertas_saz:
                bg_saz = "rgba(230,168,52,0.08)" if a.get("tipo") == "preview" else "rgba(75,85,110,0.06)"
                borda = "#E6A834" if a.get("tipo") == "preview" else "#666"
                items_saz += f'<div style="background:{bg_saz};border-radius:10px;padding:14px;margin-bottom:8px;border-left:3px solid {borda};font-size:0.85em"><strong>{a.get("icone","")} {a.get("titulo","")}</strong><br>{a.get("alerta","")}</div>'
            sazonal_html = f'<div style="margin-bottom:14px">{items_saz}</div>'

        # ── Teto Diário de Pagamento (antes do fin_resumo) ──
        teto_html = ""
        if teto_diario_info.get("teto_diario_recomendado"):
            teto_recomd = teto_diario_info["teto_diario_recomendado"]
            ocupacao_pct = teto_diario_info.get("ocupacao_semana_pct", 0)
            recomendacao = teto_diario_info.get("recomendacao", "")
            
            cor_teto = "#324D38" if ocupacao_pct <= 100 else "#E6A834" if ocupacao_pct < 110 else "#B84527"
            icone_teto = "✅" if ocupacao_pct <= 100 else "⚠️" if ocupacao_pct < 110 else "🚨"
            
            # Tabela dos dias
            dias_teto_html = ""
            for d in teto_diario_info.get("dias", []):
                # ✅ Se tem Nubank separado, mostrar detalhe
                valor_nubank = d.get("valor_nubank", 0)
                valor_exibicao = d['valor']
                nubank_label = ""
                if valor_nubank > 0:
                    nubank_label = f"<br><small style='color:#999'>(Sicoob: {formatar_moeda(valor_exibicao - valor_nubank)} + Nubank: {formatar_moeda(valor_nubank)})</small>"
                
                # ✅ Badge para dias já passados com pagamentos realizados
                passou_badge = ""
                if d.get("passou", False):
                    passou_badge = f"<br><small style='color:#324D38'>✅ Realizado em dia anterior</small>"
                
                dias_teto_html += f"""<tr>
                    <td>{d['dia']} ({d['data'].strftime('%d/%m')})</td>
                    <td class="num">{formatar_moeda(d['valor'])}{nubank_label}</td>
                    <td class="num">{d['percentual']:.0f}%</td>
                    <td style="color:{d['viabilidade'].replace('critico', '#B84527').replace('atencao', '#E6A834').replace('ok', '#324D38')};font-weight:600">{d['icone']} {d['texto']}{passou_badge}</td>
                </tr>"""
            
            teto_html = f"""<div style="background:#fff;border-radius:12px;padding:18px;margin-bottom:18px;border:2px solid {cor_teto}">
                <h3 style="margin-top:0;color:{cor_teto}">{icone_teto} Teto Diário de Pagamento</h3>
                <div style="background:rgba(120,120,120,0.06);border-radius:10px;padding:14px;margin-bottom:14px;font-size:0.85em">
                    <p style="margin:0"><strong>Receita média:</strong> R${teto_diario_info.get('media_diaria_receita', 0):,.2f}/dia</p>
                    <p style="margin:8px 0 0 0"><strong>Teto recomendado:</strong> R${teto_recomd:,.2f}/dia (55% da média — margem de 45%)</p>
                    <p style="margin:8px 0 0 0"><small style="color:#666">💡 <strong>Nota:</strong> O cálculo considera apenas Sicoob (caixa operacional). Pagamentos em Nubank (reserva) aparecem separados.</small></p>
                </div>
                <div class="table-wrapper"><table style="font-size:0.85em;width:100%"><thead><tr><th>Dia</th><th>Total a Pagar (Sicoob)</th><th>% do Teto</th><th>Status</th></tr></thead><tbody>
                    {dias_teto_html}
                </tbody></table></div>
                <div style="background:rgba(120,120,120,0.06);border-radius:10px;padding:12px;margin-top:14px;font-size:0.85em">
                    📊 Ocupação: <strong style="color:{cor_teto}">{ocupacao_pct:.0f}%</strong><br>
                    💡 {recomendacao}
                </div>
            </div>"""

        # ── Contas já pagas (antes do fin_resumo) ──
        pagas_html = ""
        if sem.get("total_pagas", 0) > 0:
            pagas_html = f"""<div style="background:rgba(50,77,56,0.08);border-radius:12px;padding:16px;margin-bottom:18px;border:1px solid rgba(50,77,56,0.2)">
                <h3 style="margin-top:0;color:#324D38">✅ Contas Já Pagas</h3>
                <p style="font-size:0.85em;margin:0"><strong>Total:</strong> R${sem.get('total_pagas', 0):,.2f}</p>
                <p style="font-size:0.82em;color:#666;margin:6px 0 0 0">Essas contas foram liquidadas e não entram mais no caixa necessário.</p>
            </div>"""

        fin_resumo = f"""
            {nubank_topo}
            {sazonal_html}
            <div class="insight-grid" style="margin-bottom:10px">
                <div class="insight-card" style="background:#fff"><div class="insight-icon">🏦</div><div class="insight-label">Caixa (Sicoob)</div><div class="insight-value" style="color:{cor_saldo}">{formatar_moeda(saldo['saldo'])}</div><div class="insight-sub">Atualizado: {saldo['data'].strftime('%d/%m') if saldo['data'] else '?'}</div></div>
                <div class="insight-card" style="background:#fff"><div class="insight-icon">📋</div><div class="insight-label">Contas da Semana</div><div class="insight-value">{formatar_moeda(sem['total_semana'])}</div><div class="insight-sub">{sem['qtd_contas']} contas</div></div>
                <div class="insight-card" style="background:#fff"><div class="insight-icon">{icone_caixa}</div><div class="insight-label">{'Sobra' if cobre else 'Falta'}</div><div class="insight-value" style="color:{cor_saldo}">{formatar_moeda(abs(sobra_falta))}</div><div class="insight-sub">{'Caixa cobre!' if cobre else 'Precisa negociar'}</div></div>
            </div>
            <div class="justo-grid" style="margin-bottom:14px">
                <div class="justo-item" style="background:#fff"><div class="justo-label">🔒 Fixas (não adia)</div><div class="justo-value">{formatar_moeda(sem['fixas'])}</div></div>
                <div class="justo-item" style="background:#fff"><div class="justo-label">🤝 Negociáveis</div><div class="justo-value">{formatar_moeda(sem['negociaveis'])}</div></div>
            </div>
            {teto_html}
            {pagas_html}
            """

        # ── Detalhamento por dia COM saldo progressivo ──
        dias_html = ""
        saldo_corrente = saldo["saldo"]
        for d in sem["dias"]:
            rows_dia = ""
            # Contas a pagar (não pagas)
            for c in sorted(d["contas"], key=lambda x: x["valor"], reverse=True):
                tag_fixa = ' <span style="color:#B84527;font-size:0.75em">🔒</span>' if c["fixa"] else ""
                tag_neg = ' <span style="color:#4B556E;font-size:0.75em">🤝</span>' if c["negociavel"] else ""
                tag_conta = f' <span style="color:#888;font-size:0.75em">[{c["conta_financeira"]}]</span>' if c["conta_financeira"] not in ("SICOOB", "", "None") else ""
                forn_html = f'<span style="color:#888;font-size:0.75em">{c.get("fornecedor") or ""}</span>' if c.get("fornecedor") else ""
                rows_dia += f'<tr><td>{c["descricao"][:55]}{tag_fixa}{tag_neg}{tag_conta}<br>{forn_html}</td><td class="num">{formatar_moeda(c["valor"])}</td></tr>'

            # Contas já pagas (Realizado) — com checkmark visual
            rows_pagas = ""
            total_pagas_dia = 0
            if d.get("pagas"):
                for c in sorted(d["pagas"], key=lambda x: x["valor"], reverse=True):
                    total_pagas_dia += c["valor"]
                    tag_conta = f' <span style="color:#888;font-size:0.75em">[{c["conta_financeira"]}]</span>' if c["conta_financeira"] not in ("SICOOB", "", "None") else ""
                    forn_html = f'<span style="color:#888;font-size:0.75em">{c.get("fornecedor") or ""}</span>' if c.get("fornecedor") else ""
                    rows_pagas += f'<tr style="opacity:0.7;background:rgba(50,77,56,0.05)"><td>✅ {c["descricao"][:50]}{tag_conta}<br>{forn_html}</td><td class="num" style="color:#324D38">{formatar_moeda(c["valor"])}</td></tr>'

            saldo_apos = saldo_corrente - total_pagas_dia
            cor_saldo_dia = "#324D38" if saldo_apos >= 2000 else "#B84527" if saldo_apos < 0 else "#E6A834"

            # Cor da borda baseada no TOTAL (a pagar + pagas)
            total_movimento = d["total"] + total_pagas_dia
            cor_dia_borda = ""
            if total_movimento > 5000:
                cor_dia_borda = "border-left:3px solid #B84527;"
            elif total_movimento > 3000:
                cor_dia_borda = "border-left:3px solid #E6A834;"

            # DIA NUNCA SERÁ ZERADO SE HÁ CONTAS (PAGAS OU NÃO)
            tem_contas_totais = bool(d["contas"] or d.get("pagas"))
            
            if tem_contas_totais:
                if total_pagas_dia > 0:
                    saldo_label = f'<div style="text-align:right;margin-top:8px;padding-top:8px;border-top:1px solid rgba(75,85,110,0.1);font-size:0.82em">Caixa antes: <strong>{formatar_moeda(saldo_corrente)}</strong> → Caixa após pagamentos: <strong style="color:{cor_saldo_dia}">{formatar_moeda(saldo_apos)}</strong></div>'
                    saldo_corrente = saldo_apos
                else:
                    saldo_label = f'<div style="text-align:right;margin-top:8px;padding-top:8px;border-top:1px solid rgba(75,85,110,0.1);font-size:0.82em">Caixa: <strong>{formatar_moeda(saldo_corrente)}</strong></div>'
            else:
                saldo_label = f'<div style="font-size:0.85em;color:#888">Zerado — Caixa: <strong>{formatar_moeda(saldo_corrente)}</strong></div>'

            # Renderizar tabela com AMBAS contas a pagar e pagas
            tabela_html = ""
            if rows_dia or rows_pagas:
                tabela_html = f'<table style="font-size:0.82em"><tbody>{rows_dia}{rows_pagas}</tbody></table>'
            
            # Mostrar total a pagar (não pagas) e badge de pagas
            cor_total = "#324D38" if d['total'] > 0 else "#888"
            pagas_badge = f'<div style="font-size:0.75em;color:#324D38;margin-top:2px">✅ +{formatar_moeda(total_pagas_dia)}</div>' if total_pagas_dia > 0 else ''
            
            dias_html += f"""<div style="background:#fff;border-radius:10px;padding:14px;margin-bottom:10px;{cor_dia_borda}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <strong>{d['nome_dia']} {d['data'].strftime('%d/%m')}</strong>
                    <div style="text-align:right">
                        <div style="font-weight:700;color:{cor_total};font-size:0.95em">{formatar_moeda(d['total'])}</div>
                        {pagas_badge}
                    </div>
                </div>
                {tabela_html if tem_contas_totais else ''}
                {saldo_label}
            </div>"""

        # ── Insights inteligentes ──
        insights_fin_html = ""
        if fin_insights:
            items_html = ""
            for ins in fin_insights:
                cor_ins = {"critico": "#B84527", "atencao": "#8B6914", "ok": "#324D38",
                           "info": "#4B556E", "estrategia": "#4B556E"}.get(ins["tipo"], "#324D38")
                bg_ins = {"critico": "rgba(184,69,39,0.06)", "atencao": "rgba(230,168,52,0.06)",
                          "ok": "rgba(50,77,56,0.04)", "info": "rgba(75,85,110,0.04)",
                          "estrategia": "rgba(75,85,110,0.04)"}.get(ins["tipo"], "rgba(75,85,110,0.04)")
                items_html += f'<div style="background:{bg_ins};border-radius:8px;padding:12px;margin-bottom:8px;font-size:0.85em;border-left:3px solid {cor_ins}">{ins["icone"]} {ins["texto"]}</div>'
            insights_fin_html = f'<div style="margin-bottom:14px"><h3 style="margin-bottom:10px">🧠 Análise & Insights</h3>{items_html}</div>'

        # ── Nubank + Meta Ads ──
        decisoes_html = ""
        if nubank or meta_ads:
            cor_nub = {"ok": "#324D38", "atencao": "#8B6914", "critico": "#B84527"}.get(nubank.get("tipo", ""), "#324D38")
            cor_meta = {"ok": "#324D38", "atencao": "#8B6914", "critico": "#B84527"}.get(meta_ads.get("tipo", ""), "#324D38")

            nub_html = f"""<div class="justo-item" style="background:#fff;border-left:3px solid {cor_nub}">
                <div class="justo-label">💜 Nubank (CDB)</div>
                <div class="justo-value" style="font-size:0.95em;color:{cor_nub}">{'R$500' if nubank.get('transferir') else 'Não transferir'}</div>
                <div class="justo-label" style="margin-top:6px;font-size:0.8em;line-height:1.4">{nubank.get('mensagem', '')}</div>
            </div>"""

            meta_html = f"""<div class="justo-item" style="background:#fff;border-left:3px solid {cor_meta}">
                <div class="justo-label">📣 Meta Ads (Tráfego)</div>
                <div class="justo-value" style="font-size:0.95em;color:{cor_meta}">{'R$100' if meta_ads.get('investir') else 'Pausar'}</div>
                <div class="justo-label" style="margin-top:6px;font-size:0.8em;line-height:1.4">{meta_ads.get('mensagem', '')}</div>
            </div>"""

            decisoes_html = f"""<div style="margin-bottom:14px">
                <h3 style="margin-bottom:10px">📌 Decisões da Semana</h3>
                <div class="justo-grid">{nub_html}{meta_html}</div>
            </div>"""

        # ── Adiamentos sugeridos ──
        adiamentos_html = ""
        if adiamentos:
            rows_adi = ""
            for a in adiamentos:
                nome = a["fornecedor"] if a["fornecedor"] != a["descricao"][:50] else a["descricao"][:40]
                rows_adi += f"""<tr>
                    <td>{nome}</td>
                    <td class="num">{formatar_moeda(a['valor'])}</td>
                    <td style="text-align:center">{a['data_original'].strftime('%d/%m')}</td>
                    <td style="text-align:center;font-weight:700;color:#324D38">{a['data_sugerida'].strftime('%d/%m')}</td>
                </tr>"""
            total_adiar = sum(a["valor"] for a in adiamentos)
            adiamentos_html = f"""<div style="background:rgba(230,168,52,0.08);border-radius:12px;padding:16px;margin-bottom:14px;border:1px solid rgba(230,168,52,0.25)">
                <h3 style="margin-top:0;color:#8B6914">🤝 Negociar Adiamento — {formatar_moeda(total_adiar)}</h3>
                <p style="font-size:0.85em;margin-bottom:10px">Sugestão de melhores datas (dias mais leves nas próximas 4 semanas):</p>
                <table style="font-size:0.85em;width:100%"><thead><tr><th style="text-align:left">Fornecedor</th><th>Valor</th><th>Vence</th><th>Adiar para</th></tr></thead><tbody>{rows_adi}</tbody></table>
                <div style="margin-top:10px;font-size:0.82em;color:#666">📖 <strong>Traduzindo:</strong> Se conseguir adiar esses boletos, o caixa fica {formatar_moeda(total_adiar)} mais leve essa semana. O fornecedor pode sugerir data diferente — o importante é que saia dessa semana!</div>
            </div>"""

        # ── Projeção até fim do mês COM referência ano anterior ──
        cor_proj = "#324D38" if proj["saldo_projetado"] >= 0 else "#B84527"
        cor_proj_real = "#324D38" if proj.get("saldo_com_receita", 0) >= 0 else "#B84527"
        rec_info = fin.get("receita_info", {})

        prev_entrada = proj.get("previsao_entrada_restante", 0)
        saldo_com_rec = proj.get("saldo_com_receita", 0)

        proj_html = f"""<div style="background:#fff;border-radius:10px;padding:14px;margin-bottom:14px">
            <h3 style="margin-top:0">📈 Projeção até fim do mês</h3>
            <div class="justo-grid">
                <div class="justo-item"><div class="justo-label">Saldo Atual</div><div class="justo-value">{formatar_moeda(proj['saldo_atual'])}</div></div>
                <div class="justo-item"><div class="justo-label">Contas a Pagar</div><div class="justo-value" style="color:#B84527">- {formatar_moeda(proj['total_a_pagar_mes'])}</div><div class="justo-label" style="margin-top:4px">{proj['qtd_contas_restantes']} contas</div></div>
                <div class="justo-item"><div class="justo-label">Ref. entrada ({rec_info.get('ref_mes', '?')})</div><div class="justo-value" style="color:#888">+ {formatar_moeda(prev_entrada)}</div><div class="justo-label" style="margin-top:4px">~R${rec_info.get('media_diaria_ap', 0):,.0f}/dia × {rec_info.get('dias_restantes', 0)} dias</div></div>
                <div class="justo-item result"><div class="justo-label">Saldo s/ contas</div><div class="justo-value" style="color:{cor_proj}">{formatar_moeda(proj['saldo_projetado'])}</div></div>
            </div>
            <div style="background:rgba(120,120,120,0.06);border-radius:8px;padding:12px;margin-top:10px;font-size:0.85em">
                📖 <strong>Traduzindo:</strong> Saldo atual menos todas as contas previstas = <strong style="color:{cor_proj}">{formatar_moeda(proj['saldo_projetado'])}</strong>.
                {'Precisa negociar adiamentos e/ou contar com receitas que vão entrar!' if proj['saldo_projetado'] < 0 else 'Caixa fecha positivo sem contar receitas — boa!'}
                <br><span style="color:#888;font-size:0.9em">📊 Referência {rec_info.get('ref_mes', '?')}: o mês faturou {formatar_moeda(rec_info.get('ref_ano_passado', 0))} (~{formatar_moeda(rec_info.get('media_diaria_ap', 0))}/dia). Se repetir, entra +{formatar_moeda(prev_entrada)} ainda. <strong>Use como comparativo, não garantia.</strong></span>
            </div>
        </div>"""

        # ── Simulador de prazos de compra ──
        sim_prazos = fin.get("simulacao_prazos", [])
        dias_compra_html = ""
        if sim_prazos:
            rows_sim = ""
            for s in sim_prazos:
                cor_v = {"ok": "#324D38", "atencao": "#E6A834", "critico": "#B84527"}.get(s["viabilidade"], "#666")
                icone_v = {"ok": "✅", "atencao": "⚠️", "critico": "⛔"}.get(s["viabilidade"], "?")
                rows_sim += f'<tr><td style="text-align:center"><strong>{s["prazo"]}d</strong></td><td>{s["dia_semana"]} {s["data_venc"].strftime("%d/%m")} ({s["mes"]})</td><td class="num">{formatar_moeda(s["carga_semana"])}</td><td style="color:{cor_v};font-weight:600">{icone_v} {s["texto"]}</td></tr>'
            dias_compra_html = f"""<div style="background:#fff;border-radius:10px;padding:14px;margin-bottom:14px">
                <h3 style="margin-top:0">📦 Se liberar pedido hoje, quando cai?</h3>
                <p style="font-size:0.82em;color:#666;margin-bottom:8px">Simulação: se fechar pedido hoje ({date.today().strftime('%d/%m')}), veja onde cai cada prazo e se a semana aguenta:</p>
                <table style="font-size:0.85em;width:100%"><thead><tr><th>Prazo</th><th>Vence em</th><th>Semana já tem</th><th>Viável?</th></tr></thead><tbody>{rows_sim}</tbody></table>
                <div style="margin-top:10px;font-size:0.82em;color:#666">📖 <strong>Traduzindo:</strong> Antes de liberar pedido, veja se o vencimento cai numa semana leve. Prefira prazos que caem em semanas com menos contas. Quanto mais verde, melhor!</div>
            </div>"""

        # ── BLOCO DE COMPRAS (dia 20+) ──
        compras_html = ""
        bc = fin.get("bloco_compras")
        if bc:
            # Teto e disponível
            cor_disp = "#324D38" if bc["disponivel"] > 0 else "#B84527"
            cmv_cor = "#324D38" if bc["cmv_real_pct"] <= 35 else "#B84527"

            # Ranking fornecedores
            forn_rows = ""
            for i, f in enumerate(bc["ranking_fornecedores"][:10]):
                medal = ["🥇","🥈","🥉"][i] if i < 3 else f"{i+1}º"
                forn_rows += f'<tr><td>{medal}</td><td>{f["fornecedor"][:30]}</td><td class="num">{formatar_moeda(f["mensal"])}/mês</td><td class="num">{f["forma"]}</td><td class="num">dia {f["dia_vencimento_freq"]}</td></tr>'

            # Semanas mais leves
            sem_rows = ""
            for s, v in sorted(bc.get("semanas_prox", {}).items()):
                tag = " 👈 mais leve" if v == min(bc.get("semanas_prox", {}).values()) else ""
                sem_rows += f'<tr><td>Semana {s}</td><td class="num">{formatar_moeda(v)}</td><td style="color:#324D38">{tag}</td></tr>'

            compras_html = f"""<div style="background:rgba(139,100,50,0.04);border-radius:14px;padding:18px;margin-bottom:18px;border:2px solid rgba(139,100,50,0.2)">
                <h3 style="margin-top:0;color:#8B6914">🛒 Planejamento de Compras — {bc['mes_referencia']}</h3>

                <div class="insight-grid" style="margin-bottom:12px">
                    <div class="insight-card" style="background:#fff"><div class="insight-icon">🎯</div><div class="insight-label">Teto de Compra</div><div class="insight-value">{formatar_moeda(bc['teto_compra'])}</div><div class="insight-sub">{CMV_TETO_PCT:.0f}% de {formatar_moeda(bc['fat_base'])}</div></div>
                    <div class="insight-card" style="background:#fff"><div class="insight-icon">📦</div><div class="insight-label">Já Comprometido</div><div class="insight-value">{formatar_moeda(bc['ja_previsto'])}</div><div class="insight-sub">boletos já lançados</div></div>
                    <div class="insight-card" style="background:#fff"><div class="insight-icon">💚</div><div class="insight-label">Disponível</div><div class="insight-value" style="color:{cor_disp}">{formatar_moeda(bc['disponivel'])}</div><div class="insight-sub">para novos pedidos</div></div>
                </div>

                <div style="background:#fff;border-radius:10px;padding:12px;margin-bottom:12px;font-size:0.85em">
                    📖 <strong>Traduzindo:</strong> Com base na previsão de faturamento de {formatar_moeda(bc['fat_base'])}, o teto de compras é {formatar_moeda(bc['teto_compra'])}. Já tem {formatar_moeda(bc['ja_previsto'])} comprometido, então <strong style="color:{cor_disp}">pode liberar até {formatar_moeda(bc['disponivel'])} em novos pedidos</strong>.
                </div>

                <div class="justo-grid" style="margin-bottom:12px">
                    <div class="justo-item" style="background:#fff"><div class="justo-label">CMV Real (mês atual)</div><div class="justo-value" style="color:{cmv_cor}">{bc['cmv_real_pct']:.0f}%</div><div class="justo-label" style="margin-top:4px">Teto: {CMV_TETO_PCT:.0f}%</div></div>
                    <div class="justo-item" style="background:#fff"><div class="justo-label">Lucro Projetado</div><div class="justo-value" style="color:{'#324D38' if bc['lucro_projetado'] > 0 else '#B84527'}">{formatar_moeda(bc['lucro_projetado'])}</div><div class="justo-label" style="margin-top:4px">Fat - CMV - Fixos</div></div>
                </div>
                <div style="background:rgba(120,120,120,0.06);border-radius:8px;padding:12px;margin-bottom:12px;font-size:0.84em">
                    📖 <strong>O que é CMV?</strong> É o Custo da Mercadoria Vendida — quanto você gastou em compras de produtos pra revender. Se o CMV está em {bc['cmv_real_pct']:.0f}%, significa que de cada R$100 que entra, R${bc['cmv_real_pct']:.0f} vão pra pagar fornecedores.<br>
                    <strong>Por que o teto é {CMV_TETO_PCT:.0f}%?</strong> Porque acima disso a margem fica apertada demais pra cobrir salários, aluguel, impostos e ainda sobrar lucro. {'<span style=\"color:#324D38\">✅ Hoje está dentro do saudável!</span>' if bc['cmv_real_pct'] <= CMV_TETO_PCT else '<span style=\"color:#B84527\">⚠️ Está acima — cada compra nova piora. Gire estoque antes de comprar!</span>'}
                </div>

                {'<div class="mini-table" style="margin-bottom:12px;background:#fff"><h4>📅 Carga por semana em ' + bc["mes_referencia"] + '</h4><table><thead><tr><th>Semana</th><th>Contas a Pagar</th><th></th></tr></thead><tbody>' + sem_rows + '</tbody></table><p style="font-size:0.82em;color:#666;margin-top:8px">💡 Programe vencimentos dos novos pedidos pra semana mais leve!</p></div>' if sem_rows else ''}

                <div class="mini-table" style="background:#fff"><h4>🏪 Top Fornecedores (últimos 6 meses)</h4>
                    <table><thead><tr><th></th><th>Fornecedor</th><th>Média/mês</th><th>Pagamento</th><th>Dia freq.</th></tr></thead><tbody>{forn_rows}</tbody></table>
                </div>
            </div>"""

        # ── RESUMÃO FECHAMENTO ──
        resumao_html = ""
        res = fin.get("resumao")
        if res:
            cmv_cor = "#324D38" if res["cmv_pct"] <= CMV_TETO_PCT else "#B84527"

            # Saídas por categoria
            cat_rows = ""
            for cat, val in res["saidas_por_categoria"].items():
                cat_rows += f'<tr><td>{cat}</td><td class="num">{formatar_moeda(val)}</td></tr>'

            # Fornecedores do mês
            forn_rows_f = ""
            for r_f in res["ranking_fornecedores"][:10]:
                forn_rows_f += f'<tr><td>{r_f["fornecedor"][:30]}</td><td class="num">{formatar_moeda(r_f["total"])}</td><td class="num">{r_f["count"]}x</td><td>{r_f["forma"]}</td></tr>'

            # Acertos e melhorias
            acertos_html = ""
            for a in res.get("acertos", []):
                acertos_html += f'<div style="background:rgba(50,77,56,0.04);border-radius:8px;padding:10px;margin-bottom:6px;font-size:0.85em;border-left:3px solid #324D38">✅ {a}</div>'
            melhorias_html = ""
            for m in res.get("melhorias", []):
                melhorias_html += f'<div style="background:rgba(184,69,39,0.06);border-radius:8px;padding:10px;margin-bottom:6px;font-size:0.85em;border-left:3px solid #B84527">⚠️ {m}</div>'

            resumao_html = f"""<div style="background:rgba(75,85,110,0.06);border-radius:14px;padding:18px;margin-bottom:18px;border:2px dashed rgba(75,85,110,0.3)">
                <h3 style="margin-top:0">📊 Resumão Financeiro do Mês</h3>

                <div class="justo-grid" style="margin-bottom:12px">
                    <div class="justo-item" style="background:#fff"><div class="justo-label">Faturamento</div><div class="justo-value">{formatar_moeda(res['faturamento'])}</div></div>
                    <div class="justo-item" style="background:#fff"><div class="justo-label">Compras (CMV)</div><div class="justo-value">{formatar_moeda(res['total_compras'])}</div><div class="justo-label" style="margin-top:4px;color:{cmv_cor}"><strong>{res['cmv_pct']:.0f}%</strong> (teto: {CMV_TETO_PCT:.0f}%)</div></div>
                </div>

                {acertos_html}{melhorias_html}

                <div class="mini-table" style="margin-bottom:12px;background:#fff"><h4>🏪 Fornecedores do Mês</h4>
                    <table><thead><tr><th>Fornecedor</th><th>Total</th><th>Vezes</th><th>Forma</th></tr></thead><tbody>{forn_rows_f}</tbody></table>
                </div>

                <div class="mini-table" style="background:#fff"><h4>📂 Saídas por Categoria</h4>
                    <table><thead><tr><th>Categoria</th><th>Valor</th></tr></thead><tbody>{cat_rows}</tbody></table>
                </div>
            </div>"""

        # ── Propostas estratégicas ──
        propostas_html = ""
        props = fin.get("propostas", [])
        if props:
            items_prop = ""
            for p in props:
                impacto_tag = f' <span style="color:#324D38;font-weight:600">+{formatar_moeda(p["impacto"])}/mês</span>' if p.get("impacto", 0) > 0 else ""
                items_prop += f"""<div style="background:#fff;border-radius:10px;padding:14px;margin-bottom:8px;border-left:3px solid #666">
                    <div style="font-weight:600;margin-bottom:4px">{p['icone']} {p['titulo']}{impacto_tag}</div>
                    <div style="font-size:0.85em;color:#555">{p['proposta']}</div>
                </div>"""
            propostas_html = f"""<div style="background:rgba(100,100,100,0.04);border-radius:14px;padding:18px;margin-bottom:18px;border:2px solid rgba(100,100,100,0.2)">
                <h3 style="margin-top:0;color:#444">💡 Diante do cenário atual, proponho:</h3>
                <p style="font-size:0.82em;color:#666;margin-bottom:12px">Ações concretas pra aumentar lucro e organizar o financeiro</p>
                {items_prop}
            </div>"""

        # ── Plano de Fornecedores (se fornecedores_mes.py existe) ──
        plano_html = ""
        plano = fin.get("plano_fornecedores")
        if plano and plano.get("fornecedores"):
            # Janela de ouro
            jo = plano.get("janela_ouro", {})
            jo_html = ""
            if jo:
                jo_html = f"""<div style="background:linear-gradient(135deg,#2d5a3e,#3d7a52);border-radius:12px;padding:14px;margin-bottom:14px;color:#fff;text-align:center">
                    <div style="font-size:.85em;opacity:.8">🏆 Janela de Ouro pra vencimentos</div>
                    <div style="font-size:1.4em;font-weight:700;margin:6px 0">Semana {jo['inicio'].strftime('%d')} a {jo['fim'].strftime('%d/%m')}</div>
                    <div style="font-size:.82em;opacity:.7">Apenas {formatar_moeda(jo['carga'])} em contas previstas</div>
                </div>"""

            # Carga mensal COM ALERTAS DE OVERSPENDING
            cm = plano.get("carga_mensal", {})
            alertas_over = plano.get("alertas_overspending", {})
            nomes_m = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
            timeline_items = ""
            alertas_timeline = ""
            
            for m, v in cm.items():
                cor_bg = "#ffebee" if v > 50000 else "#fff3e0" if v > 20000 else "#e8f5e9"
                cor_txt = "#c62828" if v > 50000 else "#e65100" if v > 20000 else "#2e7d32"
                ico = "🔴" if v > 50000 else "⚠️" if v > 20000 else "✅"
                pct = min(v / 100000 * 100, 100)
                
                # Adicionar a timeline com alert visual se houver overspending
                alerta_badge = ""
                if m in alertas_over:
                    alerta = alertas_over[m]
                    if alerta["nivel"] == "critico":
                        alerta_badge = '🚨'
                    elif alerta["nivel"] == "atencao":
                        alerta_badge = '⚠️'
                
                timeline_items += f'<div style="flex:1;background:{cor_bg};border-radius:10px;padding:10px;text-align:center;position:relative"><div style="font-size:.75em;opacity:.7">{nomes_m.get(m,"?")}</div><div style="font-size:1.1em;font-weight:700;color:{cor_txt}">{formatar_moeda(v)}</div><div style="font-size:.72em">{ico} {alerta_badge}</div></div>'
                
                # Criar cards com alertas
                if m in alertas_over:
                    alerta = alertas_over[m]
                    bg_alerta = {
                        "critico": "rgba(184,69,39,0.08)",
                        "atencao": "rgba(230,168,52,0.08)",
                        "ok": "rgba(50,77,56,0.04)"
                    }.get(alerta["nivel"], "#fff")
                    
                    borda_alerta = {
                        "critico": "#B84527",
                        "atencao": "#E6A834",
                        "ok": "#324D38"
                    }.get(alerta["nivel"], "#666")
                    
                    alertas_timeline += f"""<div style="background:{bg_alerta};border-radius:12px;padding:14px;margin-bottom:10px;border:2px solid {borda_alerta};border-left:4px solid {borda_alerta}">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                            <div style="font-weight:700;font-size:0.95em;color:{borda_alerta}">{alerta['emoji']} {alerta['titulo']}</div>
                            <span style="background:{borda_alerta};color:#fff;padding:4px 8px;border-radius:8px;font-size:0.72em;font-weight:600;text-transform:uppercase">{alerta['nivel']}</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.5);border-radius:8px;padding:10px;margin-bottom:10px;font-size:0.85em;white-space:pre-wrap">
                            {alerta['alerta']}
                        </div>
                        <div style="background:rgba(255,255,255,0.3);border-radius:8px;padding:10px;font-size:0.82em;border-left:3px solid {borda_alerta}">
                            <strong>💡 Recomendação:</strong> {alerta['recomendacao']}
                        </div>
                    </div>"""

            # Cards de fornecedores
            forn_cards = ""
            for f in plano["fornecedores"]:
                # Badge de risco
                badge_cls = {"baixo": "background:#e8f5e9;color:#2e7d32",
                             "medio": "background:#fff3e0;color:#e65100",
                             "alto": "background:#ffebee;color:#c62828"}.get(f["risco"], "")
                badge_txt = {"baixo": "Baixo", "medio": "Médio", "alto": "Alto"}.get(f["risco"], "?")

                # Meta info
                hist_txt = f'R${f["historico_media"]:,.2f}/pedido ({f["historico_count"]}x)' if f["historico_count"] > 0 else "Sem histórico"
                val_txt = f'<strong style="color:#e65100">{formatar_moeda(f["valor_orcado"])}</strong>' if f.get("valor_orcado") else (f["valor_sugerido"] or "A definir")

                # Prazo rows
                prazo_rows = ""
                for s in f["simulacoes"]:
                    status_cls = {"ok": "color:#2e7d32;font-weight:600", "atencao": "color:#e65100;font-weight:600", "critico": "color:#c62828;font-weight:600"}.get(s["status"], "")
                    ico = {"ok": "✅", "atencao": "⚠️", "critico": "⛔"}.get(s["status"], "?")
                    bg = "background:#e8f5e9" if s["recomendado"] else ""
                    prazo_rows += f'<tr style="{bg}"><td><strong>{s["prazo"]}d</strong></td><td>{s["dia_semana"]} {s["data"].strftime("%d/%m")}</td><td style="text-align:right;font-variant-numeric:tabular-nums">{formatar_moeda(s["carga_semana"])}</td><td style="{status_cls}">{ico} {s["texto"]}</td></tr>'

                # Observação
                obs_html = f'<div style="background:#fff3e0;border-radius:6px;padding:8px 10px;font-size:.82em;margin-top:6px;border-left:3px solid #e65100">{f["observacao"]}</div>' if f.get("observacao") else ""

                # Recomendação
                melhores = [s for s in f["simulacoes"] if s["recomendado"]]
                if melhores:
                    reco_prazos = "/".join(str(s["prazo"]) for s in melhores)
                    reco_data = melhores[0]["data"].strftime("%d/%m")
                    reco_txt = f'Negociar <strong>{reco_prazos} dias</strong>. 1ª parcela: {reco_data}.'
                else:
                    reco_txt = "⚠️ Todos os prazos caem em semana pesada. Considere esperar 1 semana pra liberar."

                icone_cor = {"baixo": "🟣", "medio": "🟡", "alto": "🔴"}.get(f["risco"], "⚪")

                forn_cards += f"""<div style="background:#fff;border-radius:12px;padding:14px;margin-bottom:10px;border:1px solid #eee">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                        <div style="font-weight:700;font-size:1em">{icone_cor} {f['nome']}</div>
                        <span style="padding:3px 8px;border-radius:12px;font-size:.72em;font-weight:600;{badge_cls}">{badge_txt}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;font-size:.82em">
                        <div style="background:#f8f8f8;padding:6px 8px;border-radius:6px"><span style="color:#888">Histórico</span><br><strong>{hist_txt}</strong></div>
                        <div style="background:#f8f8f8;padding:6px 8px;border-radius:6px"><span style="color:#888">Valor</span><br>{val_txt}</div>
                        <div style="background:#f8f8f8;padding:6px 8px;border-radius:6px"><span style="color:#888">Previsto</span><br><strong>{formatar_moeda(f['ja_previsto']) if f['ja_previsto'] > 0 else 'Nenhum'}</strong></div>
                        <div style="background:#f8f8f8;padding:6px 8px;border-radius:6px"><span style="color:#888">Prazos</span><br><strong>{f['prazos_disponiveis']}{'d ✨' if f['prazo_livre'] else 'd'}</strong></div>
                    </div>
                    <table style="width:100%;border-collapse:collapse;font-size:.84em;margin-bottom:8px"><thead><tr style="border-bottom:2px solid #eee"><th style="text-align:left;padding:6px;color:#666">Prazo</th><th style="text-align:left;padding:6px;color:#666">Vence em</th><th style="text-align:right;padding:6px;color:#666">Semana já tem</th><th style="text-align:left;padding:6px;color:#666">Viável?</th></tr></thead><tbody>{prazo_rows}</tbody></table>
                    <div style="background:#f5f5f5;border-radius:6px;padding:10px;font-size:.85em;border-left:3px solid #666">👉 {reco_txt}</div>
                    {obs_html}
                </div>"""

            # Resumo rápido
            resumo_items = ""
            for f in plano["fornecedores"]:
                melhores = [s for s in f["simulacoes"] if s["recomendado"]]
                prazo_txt = "/".join(str(s["prazo"]) for s in melhores) if melhores else "Esperar"
                data_txt = melhores[0]["data"].strftime("%d/%m") if melhores else "?"
                r_bg = {"baixo":"#e8f5e9","medio":"#fff3e0","alto":"#ffebee"}.get(f["risco"],"#f5f5f5")
                r_cor = {"baixo":"#2e7d32","medio":"#e65100","alto":"#c62828"}.get(f["risco"],"#666")
                nome_curto = f["nome"].split("(")[0].strip()[:15]
                resumo_items += f'<div style="background:#fff;border-radius:8px;padding:10px;text-align:center;border:1px solid #eee"><div style="font-weight:600;font-size:.82em">{nome_curto}</div><div style="font-size:1.1em;font-weight:700;color:#2e7d32">{prazo_txt}</div><div style="font-size:.72em;color:#888">1ª: {data_txt}</div></div>'

            # Análise rigorosa de picos de vencimento
            picos_html = analisar_picos_fornecedores(plano)

            plano_html = f"""<div style="background:rgba(100,100,100,0.04);border-radius:14px;padding:18px;margin-bottom:18px;border:2px dashed rgba(100,100,100,0.3)">
                <h3 style="margin-top:0;color:#444">📦 Plano de Compras — Fornecedores do Mês</h3>
                {picos_html}
                <div style="display:flex;gap:8px;margin-bottom:14px">{timeline_items}</div>
                {alertas_timeline}
                {jo_html}
                {forn_cards}
                <h4 style="text-align:center;margin:14px 0 8px;color:#666">📋 Resumo Rápido</h4>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:6px;margin-bottom:12px">{resumo_items}</div>
                <div style="background:linear-gradient(135deg,#1a1a2e,#2d2d44);border-radius:10px;padding:14px;color:#fff;font-size:.85em">
                    <strong>📏 Regras de Ouro:</strong><br>
                    → Nenhum vencimento novo em março. Tudo a partir de abril.<br>
                    → Prazo livre? Use 45/60/75 sempre.<br>
                    → Fornecedor novo? Pedido conservador.<br>
                    → Não conseguiu prazo bom? Reduza o pedido ao mínimo.
                </div>
            </div>"""

        # ── RECOMENDAÇÕES INTELIGENTES DE COMPRAS ──
        # ── MELHOR DIA PARA LIBERAR PEDIDOS (ANÁLISE HISTÓRICA) ──
        melhor_dia_html = ""
        analise_dia = fin.get("analise_melhor_dia", {})
        if analise_dia.get("melhor_dia_nome"):
            melhor_dia_nome = analise_dia["melhor_dia_nome"]
            carga_melhor = analise_dia.get("carga_melhor_dia", 0)
            ranking = analise_dia.get("ranking_dias", [])
            
            # Gerar ranking visual
            ranking_items = ""
            for dia_nome, carga_val in ranking[:5]:
                pct = min((carga_val / max([c for _, c in ranking], default=1)) * 100, 100) if ranking else 0
                icone = "🟢" if carga_val == carga_melhor else "🟡" if carga_val < 12000 else "🔴"
                ranking_items += f'<div style="margin-bottom:6px;font-size:0.85em"><div style="display:flex;justify-content:space-between;margin-bottom:2px"><span><strong>{icone} {dia_nome}</strong></span><span>{formatar_moeda(carga_val)}</span></div><div style="background:#eee;border-radius:4px;height:6px;overflow:hidden"><div style="background:{"#324D38" if carga_val == carga_melhor else "#E6A834" if carga_val < 12000 else "#B84527"};height:100%;width:{pct}%"></div></div></div>'
            
            melhor_dia_html = f"""<div style="background:rgba(50,77,56,0.04);border-radius:14px;padding:18px;margin-bottom:18px;border:2px solid rgba(50,77,56,0.2)">
                <h3 style="margin-top:0;color:#324D38">📅 Ponto 4A — Melhor Dia para Liberar Pedidos</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px">
                    <div style="background:#fff;border-radius:10px;padding:14px;text-align:center">
                        <div style="font-size:0.75em;color:#666;text-transform:uppercase;font-weight:600">Melhor Dia</div>
                        <div style="font-size:2em;font-weight:700;color:#324D38;margin:8px 0">{melhor_dia_nome}</div>
                        <div style="font-size:0.85em;color:#666">Carga: {formatar_moeda(carga_melhor)}</div>
                    </div>
                    <div style="background:#fff;border-radius:10px;padding:14px">
                        <div style="font-size:0.75em;color:#666;text-transform:uppercase;font-weight:600;margin-bottom:8px">Ranking Dias</div>
                        {ranking_items}
                    </div>
                </div>
                <div style="background:#f9f9f9;border-radius:10px;padding:12px;font-size:0.85em;border-left:3px solid #324D38">
                    <strong>💡 Recomendação:</strong> Libere pedidos preferencialmente na <strong>{melhor_dia_nome}</strong>. Se não conseguir vencer em {melhor_dia_nome}, tente <strong>Terça ou Quarta</strong> — os dias mais leves.
                </div>
            </div>"""

        # ── AVISOS DE OVERSPENDING HISTÓRICO ──
        overspending_html = ""
        avisos_over = fin.get("avisos_overspending", [])
        if avisos_over:
            items_over = ""
            for av in avisos_over:
                bg_over = "rgba(184,69,39,0.08)" if "overspending" in av.get("alerta", "").lower() else "rgba(75,85,110,0.06)"
                borda = "#B84527" if "overspending" in av.get("alerta", "").lower() else "#666"
                items_over += f'<div style="background:{bg_over};border-radius:10px;padding:12px;border-left:3px solid {borda};font-size:0.85em;margin-bottom:10px"><strong>{av.get("icone","")} {av.get("titulo","")}</strong><br>{av.get("alerta","")}</div>'
            overspending_html = f'<div style="margin-bottom:14px">{items_over}</div>'

        recom_compras_html = ""
        rec_compras = fin.get("recomendacoes_compras", [])
        if rec_compras:
            cards_rec = ""
            for r in rec_compras:
                # Flag de urgência
                icone = r.get("icone", "")
                urgencia = r.get("urgencia", "")
                melhor_prazo = r.get("melhor_prazo", "?")
                data_venc = r.get("data_vencimento")
                data_str = data_venc.strftime("%d/%m") if data_venc else "?"
                carga = r.get("carga_semana", 0)
                contexto = r.get("contexto", "")
                
                # PIX vs Boleto
                pix_boleto = r.get("pix_vs_boleto", {})
                rec_pag = pix_boleto.get("recomendacao", "?")
                mot_pag = pix_boleto.get("motivo", "")
                
                # Cores
                cor_urgencia = {"CRÍTICO": "#B84527", "ATENÇÃO": "#E6A834", "OK": "#324D38"}.get(urgencia, "#666")
                
                cards_rec += f"""
                <div style="background:#fff;border-radius:12px;padding:14px;margin-bottom:10px;border:2px solid {cor_urgencia};border-left:4px solid {cor_urgencia}">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                        <div style="font-weight:700;font-size:0.95em">{icone} {r['fornecedor']}</div>
                        <span style="background:{cor_urgencia};color:#fff;padding:4px 10px;border-radius:8px;font-size:0.75em;font-weight:600">{urgencia}</span>
                    </div>
                    
                    <div style="background:rgba(120,120,120,0.06);border-radius:8px;padding:10px;margin-bottom:10px;font-size:0.85em">
                        <strong>📅 Quando liberar?</strong><br>
                        {contexto}<br>
                        <strong style="color:{cor_urgencia}">Prazo recomendado: {melhor_prazo} dias → Vence em {data_str}</strong>
                    </div>
                    
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;font-size:0.85em">
                        <div style="background:#fff3e0;border-radius:8px;padding:8px;border-left:3px solid #E6A834">
                            <div style="color:#666;font-size:0.75em;font-weight:600">CARGA DA SEMANA</div>
                            <div style="font-weight:700;color:#8B6914">{formatar_moeda(carga)}</div>
                        </div>
                        <div style="background:#f0f8ff;border-radius:8px;padding:8px;border-left:3px solid #4B7DC1">
                            <div style="color:#666;font-size:0.75em;font-weight:600">PAGAMENTO</div>
                            <div style="font-weight:700;color:#2E5AA0">{rec_pag}</div>
                        </div>
                    </div>
                    
                    <div style="background:#f9f9f9;border-radius:8px;padding:10px;font-size:0.82em;border-left:3px solid #666">
                        💡 <strong>{rec_pag}:</strong> {mot_pag}
                    </div>
                </div>"""
            
            recom_compras_html = f"""<div style="background:rgba(139,100,50,0.04);border-radius:14px;padding:18px;margin-bottom:18px;border:2px solid rgba(139,100,50,0.2)">
                <h3 style="margin-top:0;color:#8B6914">🎯 Ponto 4B — Recomendações Inteligentes & Limites de Compra</h3>
                <p style="font-size:0.85em;color:#666;margin-bottom:14px">Análise automática: melhor data pra liberar, validação de limites (semanal R$15k/ideal, diário R$8k, parcela R$2k), e melhor forma de pagamento.</p>
                
                <div style="background:#fff;border-radius:12px;padding:14px;margin-bottom:14px;border:1px solid #ddd">
                    <h4 style="margin-top:0;color:#8B6914">📊 Limites de Compra Configurados</h4>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;font-size:0.85em">
                        <div style="background:#e8f5e9;border-radius:8px;padding:10px;text-align:center">
                            <div style="color:#666;font-size:0.75em;font-weight:600">Semanal Ideal</div>
                            <div style="font-size:1.4em;font-weight:700;color:#2e7d32">R$15.000</div>
                        </div>
                        <div style="background:#fff3e0;border-radius:8px;padding:10px;text-align:center">
                            <div style="color:#666;font-size:0.75em;font-weight:600">Emergência</div>
                            <div style="font-size:1.4em;font-weight:700;color:#e65100">R$20.000</div>
                        </div>
                        <div style="background:#ffebee;border-radius:8px;padding:10px;text-align:center">
                            <div style="color:#666;font-size:0.75em;font-weight:600">Diário</div>
                            <div style="font-size:1.4em;font-weight:700;color:#c62828">R$8.000</div>
                        </div>
                        <div style="background:#f0f8ff;border-radius:8px;padding:10px;text-align:center">
                            <div style="color:#666;font-size:0.75em;font-weight:600">Parcela Máx</div>
                            <div style="font-size:1.4em;font-weight:700;color:#2E5AA0">R$2.000</div>
                        </div>
                    </div>
                </div>
                
                {cards_rec}
                <div style="background:linear-gradient(135deg,#1a1a2e,#2d2d44);border-radius:10px;padding:14px;color:#fff;font-size:.85em;margin-top:14px">
                    <strong>📏 Regras de Ouro:</strong><br>
                    • <strong>Semanal:</strong> Máximo R$15.000 ideal, até R$20.000 em emergência, NUNCA ultrapassar<br>
                    • <strong>Diário:</strong> Máximo R$8.000 por dia de pagamento<br>
                    • <strong>Parcela:</strong> Máximo R$2.000 por parcela (se > disso, dividir em mais parcelas)<br>
                    • <strong>Dias:</strong> Libere em {melhor_dia_nome}, Terça ou Quarta (dias mais leves)<br>
                </div>
            </div>"""

        # ── Texto copiável ──
        financeiro_section_html = f"""<div class="section" style="border:2px solid rgba(120,120,120,0.4);background:rgba(120,120,120,0.04)">
            <h2>💰 Área Cinzenta — Financeiro</h2>
            <div class="subtitle" style="color:rgba(120,120,120,0.7);font-size:0.82em;margin-top:-14px;margin-bottom:18px">Semana {sem['inicio'].strftime('%d/%m')} a {sem['fim'].strftime('%d/%m/%Y')}</div>
            {fin_resumo}
            {dias_html}
            {decisoes_html}
            {adiamentos_html}
            {insights_fin_html}
            {proj_html}
            {dias_compra_html}
            {recom_compras_html}
            {compras_html}
            {resumao_html}
            {propostas_html}
            {plano_html}
            <div style="margin-top:14px">
                <div class="mensagem-texto" id="msgFinTexto" style="max-height:400px;font-size:0.82em;white-space:pre-line">{mensagem_wpp}</div>
                <button class="btn-copiar" id="btnCopiarFin" onclick="copiarFinanceiro()" style="background:linear-gradient(135deg,#666,#888);margin-top:10px">📋 Copiar p/ WhatsApp</button>
            </div>
        </div>"""

    # ── Painel de Saldos ──
    fin = r.get("financeiro")
    saldos = fin.get("saldos_contas", {}) if fin else {}
    sicoob = saldos.get("sicoob", 0)
    nubank = saldos.get("nubank", 0)
    caixa_loja = saldos.get("caixa_loja", 0)
    total_geral = sicoob + nubank + caixa_loja
    nub_pct = saldos.get("nubank_pct_meta", 0)
    nub_falta = saldos.get("nubank_falta_meta", 0)
    cor_nub_barra = "#8B5CF6" if nub_pct >= 50 else "#E6A834" if nub_pct >= 25 else "#B84527"
    painel_saldos_html = f"""<div style="background:#fff;border-radius:18px;padding:28px;margin-bottom:18px;box-shadow:0 2px 20px rgba(50,77,56,0.06);border:1px solid rgba(50,77,56,0.08);">
    <div style="font-size:0.8em;text-transform:uppercase;letter-spacing:1.5px;color:#8BA279;font-weight:600;margin-bottom:14px;">💰 Saldos das Contas</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:0;">
        <div style="background:#fff;border-radius:14px;padding:18px;text-align:center;border:1px solid rgba(50,77,56,0.1);">
            <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1.5px;color:#8BA279;font-weight:600;margin-bottom:8px;">Sicoob</div>
            <div style="font-size:1.5em;font-weight:700;color:#324D38;">{formatar_moeda(sicoob)}</div>
        </div>
        <div style="background:linear-gradient(135deg,#1a1a2e,#2d2d44);border-radius:14px;padding:18px;text-align:center;">
            <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1.5px;color:rgba(255,255,255,0.6);font-weight:600;margin-bottom:8px;">Nubank (CDB)</div>
            <div style="font-size:1.5em;font-weight:700;color:#fff;margin-bottom:8px;">{formatar_moeda(nubank)}</div>
            <div style="background:rgba(255,255,255,0.15);border-radius:20px;height:8px;overflow:hidden;margin-bottom:4px;">
                <div style="background:{cor_nub_barra};height:100%;width:{min(nub_pct,100):.0f}%;border-radius:20px;"></div>
            </div>
            <div style="font-size:0.72em;color:rgba(255,255,255,0.6);">{nub_pct:.0f}% da meta - faltam {formatar_moeda(nub_falta)}</div>
        </div>
        <div style="background:#fff;border-radius:14px;padding:18px;text-align:center;border:1px solid rgba(50,77,56,0.1);">
            <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1.5px;color:#8BA279;font-weight:600;margin-bottom:8px;">Caixa Loja</div>
            <div style="font-size:1.5em;font-weight:700;color:#324D38;">{formatar_moeda(caixa_loja)}</div>
        </div>
        <div style="background:rgba(50,77,56,0.06);border-radius:14px;padding:18px;text-align:center;border:2px solid rgba(50,77,56,0.15);">
            <div style="font-size:0.7em;text-transform:uppercase;letter-spacing:1.5px;color:#8BA279;font-weight:600;margin-bottom:8px;">Total Geral</div>
            <div style="font-size:1.5em;font-weight:700;color:#324D38;">{formatar_moeda(total_geral)}</div>
        </div>
    </div>

</div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bem Me Quer — {modo_titulo}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Inter',sans-serif; background:#F5F3EC; color:#324D38; padding:20px; min-height:100vh; }}
        .container {{ max-width:860px; margin:0 auto; }}
        .header {{ text-align:center; padding:35px 20px 30px; background:linear-gradient(135deg,#324D38,#4a6b52); border-radius:20px; margin-bottom:20px; position:relative; overflow:hidden; }}
        .header::before {{ content:''; position:absolute; top:-50%; right:-30%; width:400px; height:400px; background:radial-gradient(circle,rgba(199,207,158,0.15) 0%,transparent 70%); }}
        .logo {{ width:160px; height:auto; margin-bottom:15px; filter:brightness(0) invert(1); opacity:0.95; }}
        .logo-text {{ font-family:'Cormorant Garamond',serif; font-size:2.2em; color:#F5F3EC; font-weight:400; font-style:italic; margin-bottom:10px; }}
        .logo-text span {{ font-size:0.4em; font-style:normal; letter-spacing:4px; text-transform:uppercase; display:block; opacity:0.7; }}
        .header h1 {{ font-size:1.1em; font-weight:500; color:#C7CF9E; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }}
        .header .subtitle {{ color:rgba(245,243,236,0.6); font-size:0.85em; font-weight:300; }}
        .badge-fechamento {{ display:inline-block; background:#B84527; color:#fff; padding:4px 14px; border-radius:20px; font-size:0.75em; font-weight:700; letter-spacing:1px; margin-top:8px; }}
        .meta-section {{ background:#fff; border-radius:18px; padding:28px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }}
        .meta-numeros {{ display:flex; justify-content:space-between; flex-wrap:wrap; gap:15px; margin-bottom:22px; }}
        .meta-item {{ text-align:center; flex:1; min-width:120px; padding:12px 8px; background:#fafaf6; border-radius:12px; border:1px solid rgba(50,77,56,0.06); }}
        .meta-item .label {{ color:#8BA279; font-size:0.7em; text-transform:uppercase; letter-spacing:1.5px; font-weight:600; }}
        .meta-item .value {{ font-size:1.4em; font-weight:700; color:#324D38; margin-top:6px; }}
        .meta-item .value.destaque {{ color:#B84527; }}
        .progress-container {{ background:#edeadf; border-radius:14px; height:36px; overflow:hidden; }}
        .progress-bar {{ height:100%; border-radius:14px; background:linear-gradient(90deg,#8BA279,#324D38); transition:width 1.5s ease; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85em; color:#F5F3EC; text-shadow:0 1px 2px rgba(0,0,0,0.3); min-width:60px; }}
        .comparativo {{ padding:14px 20px; border-radius:12px; margin-bottom:18px; font-size:0.92em; font-weight:500; }}
        .comparativo.positivo {{ background:rgba(50,77,56,0.08); border:1px solid rgba(50,77,56,0.15); color:#324D38; }}
        .comparativo.negativo {{ background:rgba(184,69,39,0.08); border:1px solid rgba(184,69,39,0.15); color:#B84527; }}
        .comparativo-justo {{ background:#fff; border-radius:16px; padding:22px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:2px solid #C7CF9E; }}
        .comparativo-justo h3 {{ font-size:0.95em; margin-bottom:14px; color:#324D38; }}
        .comparativo-justo small {{ display:block; margin-top:10px; color:#8BA279; font-size:0.82em; }}
        .justo-grid {{ display:flex; gap:14px; flex-wrap:wrap; }}
        .justo-item {{ flex:1; min-width:140px; text-align:center; padding:12px; background:#fafaf6; border-radius:10px; }}
        .justo-item.result {{ background:rgba(50,77,56,0.06); }}
        .justo-label {{ font-size:0.72em; text-transform:uppercase; letter-spacing:1px; color:#8BA279; font-weight:600; }}
        .justo-value {{ font-size:1.2em; font-weight:700; color:#324D38; margin-top:4px; }}
        .justo-value span {{ font-size:0.6em; font-weight:400; color:#888; }}
        .cards {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:18px; }}
        .card {{ flex:1; min-width:280px; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }}
        .card-header {{ padding:14px 20px; background:rgba(50,77,56,0.04); font-weight:600; font-size:0.88em; color:#324D38; border-bottom:1px solid rgba(50,77,56,0.06); }}
        .card-body {{ padding:18px 20px; }}
        .stat-row {{ display:flex; justify-content:space-between; padding:7px 0; font-size:0.88em; color:#555; }}
        .stat-value {{ font-weight:600; color:#324D38; }}
        .stat-row.highlight {{ font-weight:700; font-size:0.95em; padding-top:12px; margin-top:4px; border-top:1px solid rgba(50,77,56,0.08); }}
        .highlight-value {{ color:#B84527; font-size:1.15em; font-weight:700; }}
        .motivacao {{ text-align:center; padding-top:12px; font-size:0.95em; color:#8BA279; font-weight:600; }}
        .preview-card {{ border-color:rgba(184,69,39,0.15); }}
        .preview-card .card-header {{ background:rgba(184,69,39,0.04); color:#B84527; }}
        .section {{ background:#fff; border-radius:18px; padding:28px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }}
        .section h2 {{ font-size:1.05em; margin-bottom:18px; color:#324D38; font-weight:700; }}
        .section h3 {{ font-size:0.92em; margin-bottom:12px; color:#324D38; font-weight:600; }}
        .table-wrapper {{ overflow-x:auto; }}
        table {{ width:100%; border-collapse:collapse; font-size:0.85em; }}
        thead th {{ text-align:left; padding:10px 12px; background:rgba(50,77,56,0.04); color:#8BA279; font-weight:600; font-size:0.8em; text-transform:uppercase; letter-spacing:1px; border-bottom:2px solid rgba(50,77,56,0.1); }}
        tbody td {{ padding:10px 12px; border-bottom:1px solid rgba(50,77,56,0.06); }}
        .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
        .fechamento-section {{ border:2px solid #324D38; }}
        .insight-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:22px; }}
        .insight-card {{ background:#fafaf6; border-radius:14px; padding:18px; text-align:center; border:1px solid rgba(50,77,56,0.06); }}
        .insight-card.wide {{ grid-column:1/-1; display:flex; align-items:center; gap:18px; text-align:left; justify-content:center; }}
        .insight-icon {{ font-size:1.5em; margin-bottom:6px; }}
        .insight-label {{ font-size:0.72em; text-transform:uppercase; letter-spacing:1px; color:#8BA279; font-weight:600; }}
        .insight-value {{ font-size:1.4em; font-weight:700; color:#324D38; margin:4px 0; }}
        .insight-sub {{ font-size:0.78em; color:#999; }}
        .insights-grid-2col {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:18px; }}
        @media (max-width:700px) {{ .insights-grid-2col {{ grid-template-columns:1fr; }} }}
        .chart-section {{ background:#fafaf6; border-radius:14px; padding:18px; border:1px solid rgba(50,77,56,0.06); }}
        .bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
        .bar-label {{ width:35px; font-size:0.8em; font-weight:600; color:#555; }}
        .bar-track {{ flex:1; background:#edeadf; border-radius:8px; height:22px; overflow:hidden; }}
        .bar-fill {{ height:100%; background:linear-gradient(90deg,#8BA279,#324D38); border-radius:8px; transition:width 1s ease; }}
        .bar-value {{ width:90px; text-align:right; font-size:0.8em; font-weight:600; color:#324D38; }}
        .mini-table {{ background:#fafaf6; border-radius:14px; padding:18px; border:1px solid rgba(50,77,56,0.06); margin-bottom:14px; }}
        .mini-table.fraco {{ border-color:rgba(184,69,39,0.12); }}
        .mini-table table {{ font-size:0.85em; }}
        .mini-table td {{ padding:8px 10px; }}
        .mensagem-section {{ background:#fff; border-radius:18px; padding:28px; margin-bottom:18px; box-shadow:0 2px 20px rgba(50,77,56,0.06); border:1px solid rgba(50,77,56,0.08); }}
        .mensagem-section h2 {{ font-size:1em; margin-bottom:16px; color:#324D38; font-weight:600; }}
        .mensagem-texto {{ background:#fafaf6; border:1px solid rgba(50,77,56,0.08); border-radius:12px; padding:20px; white-space:pre-wrap; font-size:0.88em; line-height:1.7; color:#444; max-height:500px; overflow-y:auto; }}
        .btn-copiar {{ display:block; width:100%; margin-top:16px; padding:15px; border:none; border-radius:12px; background:linear-gradient(135deg,#324D38,#4a6b52); color:#F5F3EC; font-size:0.95em; font-weight:600; cursor:pointer; transition:all 0.3s; letter-spacing:0.5px; }}
        .btn-copiar:hover {{ transform:translateY(-2px); box-shadow:0 6px 20px rgba(50,77,56,0.3); }}
        .btn-copiar.copiado {{ background:linear-gradient(135deg,#8BA279,#a3b88e); }}
        .aviso {{ background:rgba(230,168,52,0.1); border:1px solid rgba(230,168,52,0.25); border-radius:12px; padding:16px 20px; margin-bottom:18px; font-size:0.88em; color:#8B6914; }}
        .aviso code {{ background:rgba(230,168,52,0.15); padding:2px 8px; border-radius:5px; font-size:0.9em; }}
        .footer {{ text-align:center; padding:25px 20px; color:#BBB494; font-size:0.75em; letter-spacing:1px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">{logo_html}<h1>{modo_titulo}</h1><div class="subtitle">{nome_mes} {ano} — Dia {dia:02d}/{hoje.month:02d}/{ano}</div>{modo_badge}</div>
    {painel_saldos_html}
    {aviso_html}
    <div class="meta-section">
        <div class="meta-numeros">
            <div class="meta-item"><div class="label">Vendas</div><div class="value">{formatar_moeda(vendas)}</div></div>
            <div class="meta-item"><div class="label">Meta</div><div class="value">{formatar_moeda(meta)}</div></div>
            <div class="meta-item"><div class="label">{"Superou em" if faltam <= 0 else "Faltam"}</div><div class="value destaque">{formatar_moeda(abs(faltam))}</div></div>
            <div class="meta-item"><div class="label">Por dia ({dias_restantes:.0f} dias)</div><div class="value">{formatar_moeda(valor_diario)}</div></div>
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
    <div class="footer"><span style="font-size:1.2em">🌿</span><br>Bem Me Quer Cosméticos — Gerado em {dia:02d}/{hoje.month:02d}/{ano}</div>
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
document.addEventListener('DOMContentLoaded', () => {{
    const bar = document.querySelector('.progress-bar');
    const w = bar.style.width; bar.style.width = '0%';
    setTimeout(() => {{ bar.style.width = w; }}, 300);
}});
</script>
</body></html>"""
    return html


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    forcar = "--fechamento" in sys.argv
    auto = "--auto" in sys.argv

    print("=" * 55)
    print(f"  🌿 BEM ME QUER — {'FECHAMENTO MENSAL' if forcar else 'RELATÓRIO DE VENDAS'}")
    print("=" * 55)
    print()

    try:
        # 1. Criamos o dicionário 'r' com os dados do relatório
        r = gerar_dados_relatorio(forcar_fechamento=forcar, auto=auto)
        
        if not r:
            print("❌ Não foi possível gerar o relatório.")
            exit()

        # 2. ADICIONAMOS A DATA AQUI! Logo após garantir que 'r' existe.
        # Assim, todas as funções abaixo poderão usar r['hoje'] se precisarem.
        import datetime # (Lembrete: o ideal é mover isso para a linha 1 do arquivo depois)
        r['hoje'] = datetime.date.today()

        # 3. Geramos as mensagens
        if r["fechamento"]:
            mensagem = gerar_mensagem_fechamento(r)
        else:
            mensagem = gerar_mensagem_semanal(r)

        # 4. Geramos o HTML (sem dar erro de chave, pois 'hoje' já está lá em cima!)
        html = gerar_html(r, mensagem)

        # 5. Salvamos o arquivo
        caminho = os.path.join(PASTA_SCRIPT, "relatorio.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)

        print()
        print(f"✅ Relatório salvo: {caminho}")
        if r["fechamento"]:
            print(f"📊 Histórico: {caminho_historico(r['hoje'].month, r['hoje'].year)}")
        print("🌐 Abrindo no navegador...")
        webbrowser.open(f"file:///{caminho}")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback # (Lembrete: também ideal mover para o topo do arquivo)
        traceback.print_exc()
