"""
Módulo de Análise de Serviços — Bem Me Quer Cosméticos
Lê a planilha de Serviços de Sobrancelha e gera insights.

Usado pelo relatorio_semanal.py
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime
import calendar
import re
import json
import os

PLANILHA_SERVICOS_ID = "1-UNfQN6y6OgntbwYzEwG7Z6UdJPw71I5sIo1EWchqz8"

CUSTO_DIARIA_ANTIGO = 180.0   # Até março/2026
CUSTO_DIARIA_NOVO = 190.0     # A partir de abril/2026
DATA_MUDANCA_DIARIA = (2026, 4)  # Ano, mês

DIAS_SEMANA_PROFISSIONAL = [1, 3, 4]  # Terça(1), Quinta(3), Sexta(4)


def custo_diaria(ano, mes):
    """Retorna o custo da diária conforme o período."""
    if (ano, mes) >= DATA_MUDANCA_DIARIA:
        return CUSTO_DIARIA_NOVO
    return CUSTO_DIARIA_ANTIGO

NOMES_MESES_SERVICOS = {
    1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL",
    5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
    9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
}

# Mapeamento de nomes de abas (a planilha varia o formato)
def encontrar_aba_servicos(abas, mes, ano):
    """Tenta encontrar a aba de serviços para o mês/ano."""
    ano2 = str(ano)[-2:]
    ano4 = str(ano)
    nome_mes = NOMES_MESES_SERVICOS.get(mes, "")

    tentativas = [
        f"{nome_mes}/{ano2}",        # FEVEREIRO/26
        f"{nome_mes}/{ano4}",        # FEVEREIRO/2026
        f"{nome_mes}{ano2}",          # FEVEREIRO26
        f"{nome_mes}{ano4}",          # FEVEREIRO2026
    ]

    # Tentativa exata
    for t in tentativas:
        for aba in abas:
            if aba.strip().upper() == t.upper():
                return aba

    # Fallback: busca parcial (nome do mês + ano em qualquer formato)
    # Também tenta sem acento (MARCO vs MARÇO)
    nome_sem_acento = nome_mes.replace("Ç", "C").replace("ç", "c").replace("Ã", "A").replace("ã", "a")
    for aba in abas:
        aba_upper = aba.strip().upper().replace(" ", "")
        if (nome_mes in aba_upper or nome_sem_acento in aba_upper) and (ano2 in aba_upper or ano4 in aba_upper):
            return aba
    return None


def detectar_colunas(header):
    """Detecta a posição das colunas baseado no cabeçalho."""
    cols = {
        "data": None, "cliente": None, "contato": None,
        "tipo": None, "valor": None, "combo": None,
        "pagamento": None, "feedback": None,
    }
    for i, h in enumerate(header):
        h_upper = h.upper().strip()
        if "DATA" in h_upper and cols["data"] is None:
            cols["data"] = i
        elif "CLIENTE" in h_upper:
            cols["cliente"] = i
        elif "CONTATO" in h_upper:
            cols["contato"] = i
        elif "PAGO" in h_upper or h_upper == "COMPRA":
            cols["tipo"] = i
        elif "VALOR" in h_upper:
            cols["valor"] = i
        elif "COMBO" in h_upper or "SERVIÇO" in h_upper:
            cols["combo"] = i
        elif "PAGAMENTO" in h_upper:
            cols["pagamento"] = i
        elif "FEEDBACK" in h_upper:
            cols["feedback"] = i

    # Se CLIENTE não foi achado, inferir: é a coluna DEPOIS de DATA
    if cols["cliente"] is None and cols["data"] is not None:
        cols["cliente"] = cols["data"] + 1

    return cols


def limpar_valor_servico(texto):
    """Extrai valor numérico de strings como 'R$ 30,00' ou 'R$150'."""
    if not texto or not texto.strip():
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


def classificar_tipo(tipo_texto, valor=0):
    """Classifica o tipo de atendimento."""
    t = tipo_texto.upper().strip()

    if "COMBO" in t:
        return "combo"
    elif "COMPROU" in t and ("150" in t or "100" in t):
        return "compra_produto"
    elif "COMPROU" in t and "HASKELL" in t:
        return "compra_produto"
    elif "COMPROU" in t and ("BOTHÂNICO" in t or "BOTANICO" in t):
        return "compra_produto"
    elif "COMPROU" in t:
        return "compra_produto"
    elif "PAGOU" in t and "30" in t:
        return "com_henna"  # R$30
    elif "PAGOU" in t and "25" in t:
        return "sem_henna"  # R$25
    elif "PAGOU" in t and "20" in t:
        return "sobrancelha_antiga"  # preço antigo
    elif "PAGOU" in t:
        return "servico_outro"
    else:
        return "outro"


def parse_data(texto):
    """Tenta parsear a data em vários formatos."""
    texto = texto.strip()
    if not texto:
        return None
    formatos = ["%d/%m/%Y", "%d/%m/%y"]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None


def normalizar_nome(nome):
    """Normaliza nome para comparação de recorrência."""
    if not nome:
        return ""
    nome = nome.strip().lower()
    # Remove observações entre parênteses ou após "JÁ PAGOU"
    nome = re.sub(r'\s*(já pagou|j[aá] pagou).*', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*mix\s*\d+.*', '', nome, flags=re.IGNORECASE)
    # Remove espaços extras
    nome = re.sub(r'\s+', ' ', nome).strip()
    # Remove acentos simples para matching
    substituicoes = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o',
        'ô': 'o', 'õ': 'o', 'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }
    for de, para in substituicoes.items():
        nome = nome.replace(de, para)
    return nome


def ler_atendimentos_aba(planilha, nome_aba):
    """Lê todos os atendimentos de uma aba."""
    try:
        aba = planilha.worksheet(nome_aba)
    except Exception:
        return []

    dados = aba.get_all_values()
    if len(dados) < 3:
        return []

    # Encontrar header (geralmente linha 3, índice 2)
    header_idx = None
    for i, linha in enumerate(dados[:5]):
        texto = " ".join(str(c).upper() for c in linha)
        # Aceitar: CLIENTE + DATA, ou QUANT + DATA + CONTATO (quando CLIENTE está em branco)
        if ("CLIENTE" in texto and ("DATA" in texto or "QUANT" in texto)) or \
           ("QUANT" in texto and "DATA" in texto and "CONTATO" in texto):
            header_idx = i
            break

    if header_idx is None:
        return []

    cols = detectar_colunas(dados[header_idx])

    # Fallback para abas antigas sem coluna CLIENTE detectada
    if cols["cliente"] is None:
        # Tentar posição fixa (formato antigo)
        cols["cliente"] = 4
        cols["data"] = 3
        cols["tipo"] = 6
        cols["pagamento"] = 7

    atendimentos = []
    for i in range(header_idx + 1, len(dados)):
        linha = dados[i]
        if len(linha) < 4:
            continue

        # Extrair cliente
        cliente = ""
        if cols["cliente"] is not None and cols["cliente"] < len(linha):
            cliente = linha[cols["cliente"]].strip()
        if not cliente:
            continue

        # Extrair data
        dt = None
        if cols["data"] is not None and cols["data"] < len(linha):
            dt = parse_data(linha[cols["data"]])
        if dt is None:
            continue

        # Extrair tipo
        tipo_texto = ""
        if cols["tipo"] is not None and cols["tipo"] < len(linha):
            tipo_texto = linha[cols["tipo"]].strip()
        if not tipo_texto:
            continue

        # Extrair valor
        valor = 0.0
        if cols["valor"] is not None and cols["valor"] < len(linha):
            valor = limpar_valor_servico(linha[cols["valor"]])
        if valor == 0:
            # Tentar extrair do tipo ("PAGOU R$30" → 30)
            match = re.search(r'R?\$?\s*(\d+[\.,]?\d*)', tipo_texto)
            if match:
                valor = limpar_valor_servico(match.group(1))

        # Extrair combo/serviço
        combo = ""
        if cols["combo"] is not None and cols["combo"] < len(linha):
            combo = linha[cols["combo"]].strip()

        # Extrair pagamento
        pagamento = ""
        if cols["pagamento"] is not None and cols["pagamento"] < len(linha):
            pagamento = linha[cols["pagamento"]].strip()

        # Extrair contato
        contato = ""
        if cols["contato"] is not None and cols["contato"] < len(linha):
            contato = linha[cols["contato"]].strip()

        tipo = classificar_tipo(tipo_texto, valor)

        atendimentos.append({
            "data": dt,
            "cliente": cliente,
            "cliente_normalizado": normalizar_nome(cliente),
            "contato": contato,
            "tipo_texto": tipo_texto,
            "tipo": tipo,
            "valor": valor,
            "combo": combo,
            "pagamento": pagamento,
            "mes": dt.month,
            "ano": dt.year,
        })

    return atendimentos


def contar_dias_profissional(ano, mes):
    """Conta quantos dias a profissional trabalhou (ter/qui/sex) no mês."""
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dias = 0
    for dia in range(1, ultimo_dia + 1):
        try:
            dt = date(ano, mes, dia)
        except ValueError:
            continue
        if dt > date.today() and ano == date.today().year:
            break
        if dt.weekday() in DIAS_SEMANA_PROFISSIONAL:
            dias += 1
    return dias


def gerar_analise_servicos(planilha_servicos, mes, ano, abas_servicos, semana_inicio=None, semana_fim=None):
    """Gera análise completa de serviços para o mês, com resumo semanal opcional."""

    # Ler aba do mês atual
    nome_aba = encontrar_aba_servicos(abas_servicos, mes, ano)
    if not nome_aba:
        return None

    atendimentos = ler_atendimentos_aba(planilha_servicos, nome_aba)
    
    if not atendimentos:
        return None

    # Filtrar SEMPRE só o mês/ano correto - nunca carregar próximos meses
    # Se semana cruza de mês, a data final é truncada ao último dia do mês
    atendimentos = [a for a in atendimentos if a["mes"] == mes and a["ano"] == ano]

    total_atend = len(atendimentos)
    receita_total = sum(a["valor"] for a in atendimentos)

    # Custo da profissional
    dias_prof = contar_dias_profissional(ano, mes)
    diaria = custo_diaria(ano, mes)
    custo_total = dias_prof * diaria
    lucro = receita_total - custo_total

    # Tipos de atendimento
    tipos = {}
    for a in atendimentos:
        t = a["tipo"]
        if t not in tipos:
            tipos[t] = {"count": 0, "receita": 0}
        tipos[t]["count"] += 1
        tipos[t]["receita"] += a["valor"]

    # Formas de pagamento
    pagamentos = {}
    for a in atendimentos:
        pg = a["pagamento"].strip()
        if not pg:
            pg = "Não informado"
        # Normalizar
        pg_upper = pg.upper()
        if "PIX" in pg_upper:
            pg = "Pix"
        elif "DINHEIRO" in pg_upper:
            pg = "Dinheiro"
        elif "CRÉDITO" in pg_upper or "CREDITO" in pg_upper:
            pg = "Cartão Crédito"
        elif "DÉBITO" in pg_upper or "DEBITO" in pg_upper:
            pg = "Cartão Débito"
        elif "PICPAY" in pg_upper:
            pg = "PicPay"

        pagamentos[pg] = pagamentos.get(pg, 0) + 1

    pagamentos_ranking = sorted(pagamentos.items(), key=lambda x: x[1], reverse=True)

    # Atendimentos por dia da semana
    atend_por_dia = {}
    for a in atendimentos:
        ds = a["data"].weekday()
        dia_nome = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado"}
        dn = dia_nome.get(ds, "?")
        if dn not in atend_por_dia:
            atend_por_dia[dn] = {"count": 0, "receita": 0}
        atend_por_dia[dn]["count"] += 1
        atend_por_dia[dn]["receita"] += a["valor"]

    # Receita de serviço puro (só sobrancelha: R$25, R$30, combos)
    TIPOS_SERVICO = ("com_henna", "sem_henna", "sobrancelha_antiga", "combo", "servico_outro")
    atend_servico = [a for a in atendimentos if a["tipo"] in TIPOS_SERVICO]
    atend_compra = [a for a in atendimentos if a["tipo"] == "compra_produto"]

    receita_servico_puro = sum(a["valor"] for a in atend_servico)
    receita_compras = sum(a["valor"] for a in atend_compra)
    qtd_servico = len(atend_servico)
    qtd_compras = len(atend_compra)
    taxa_conversao = (qtd_compras / total_atend * 100) if total_atend > 0 else 0

    # Ticket médio SEPARADO
    # Serviço: média de quem pagou sobrancelha (R$25/R$30/combo)
    ticket_medio_servico = receita_servico_puro / qtd_servico if qtd_servico > 0 else 0
    # Compra: média de quem comprou produto (R$150+)
    ticket_medio_compra = receita_compras / qtd_compras if qtd_compras > 0 else 0
    # Geral (todos)
    ticket_medio = receita_total / total_atend if total_atend > 0 else 0
    media_atend_por_dia = total_atend / dias_prof if dias_prof > 0 else 0

    # Lucro: comparar custo da profissional vs receita de serviço
    # Compras de produto são receita da LOJA, não do serviço diretamente
    lucro_servico = receita_servico_puro - custo_total

    # ── CLIENTES RECORRENTES (histórico completo) ──
    todos_atendimentos = []
    for aba_nome in abas_servicos:
        # Pular abas não-mensais
        if aba_nome.upper() in ("ATIVIDADES DIÁRIAS", "PRODUTOS"):
            continue
        atend_aba = ler_atendimentos_aba(planilha_servicos, aba_nome)
        todos_atendimentos.extend(atend_aba)

    # Contar frequência por cliente normalizado
    freq_total = {}
    meses_por_cliente = {}
    for a in todos_atendimentos:
        cn = a["cliente_normalizado"]
        if not cn:
            continue
        freq_total[cn] = freq_total.get(cn, 0) + 1
        chave_mes = f"{a['ano']}-{a['mes']:02d}"
        if cn not in meses_por_cliente:
            meses_por_cliente[cn] = set()
        meses_por_cliente[cn].add(chave_mes)

    # Top 15 clientes mais recorrentes
    top_recorrentes = sorted(freq_total.items(), key=lambda x: x[1], reverse=True)[:15]

    # Nome original do cliente (pegar o mais recente)
    nome_original = {}
    for a in sorted(todos_atendimentos, key=lambda x: x["data"]):
        cn = a["cliente_normalizado"]
        nome_original[cn] = a["cliente"]

    top_recorrentes_lista = []
    for cn, count in top_recorrentes:
        top_recorrentes_lista.append({
            "nome": nome_original.get(cn, cn).title(),
            "vezes": count,
            "meses_distintos": len(meses_por_cliente.get(cn, set())),
        })

    # Clientes deste mês: novas vs recorrentes
    clientes_mes = set()
    clientes_antes = set()
    for a in todos_atendimentos:
        cn = a["cliente_normalizado"]
        if not cn:
            continue
        if a["mes"] == mes and a["ano"] == ano:
            clientes_mes.add(cn)
        elif a["data"] < date(ano, mes, 1):
            clientes_antes.add(cn)

    clientes_retorno = clientes_mes & clientes_antes
    clientes_novas = clientes_mes - clientes_antes
    pct_retorno = (len(clientes_retorno) / len(clientes_mes) * 100) if clientes_mes else 0

    # Comparar com mês anterior
    mes_ant = mes - 1 if mes > 1 else 12
    ano_ant_ref = ano if mes > 1 else ano - 1
    nome_aba_ant = encontrar_aba_servicos(abas_servicos, mes_ant, ano_ant_ref)
    atend_ant = 0
    receita_ant = 0
    if nome_aba_ant:
        atend_mes_ant = ler_atendimentos_aba(planilha_servicos, nome_aba_ant)
        atend_mes_ant = [a for a in atend_mes_ant if a["mes"] == mes_ant and a["ano"] == ano_ant_ref]
        atend_ant = len(atend_mes_ant)
        receita_ant = sum(a["valor"] for a in atend_mes_ant)

    # Comparar com mesmo mês do ano anterior
    nome_aba_aa = encontrar_aba_servicos(abas_servicos, mes, ano - 1)
    atend_aa = 0
    receita_aa = 0
    if nome_aba_aa:
        atend_ano_ant = ler_atendimentos_aba(planilha_servicos, nome_aba_aa)
        atend_ano_ant = [a for a in atend_ano_ant if a["mes"] == mes and a["ano"] == ano - 1]
        atend_aa = len(atend_ano_ant)
        receita_aa = sum(a["valor"] for a in atend_ano_ant)

    # Resumo da semana
    resumo_semana = None
    if semana_inicio and semana_fim:
        # Se a semana cruza para outro mês, truncar ao último dia do mês atual
        semana_fim_truncada = semana_fim
        if semana_fim.month != mes:
            last_day = calendar.monthrange(ano, mes)[1]
            semana_fim_truncada = date(ano, mes, last_day)
        
        atend_semana = [a for a in atendimentos if semana_inicio <= a["data"] <= semana_fim_truncada]
        if atend_semana:
            atend_sem_servico = [a for a in atend_semana if a["tipo"] in TIPOS_SERVICO]
            atend_sem_compra = [a for a in atend_semana if a["tipo"] == "compra_produto"]
            receita_sem_serv = sum(a["valor"] for a in atend_sem_servico)
            receita_sem_compra = sum(a["valor"] for a in atend_sem_compra)
            resumo_semana = {
                "inicio": semana_inicio,
                "fim": semana_fim_truncada,  # Usar data truncada
                "atendimentos": len(atend_semana),
                "qtd_servico": len(atend_sem_servico),
                "qtd_compras": len(atend_sem_compra),
                "receita_servico": round(receita_sem_serv, 2),
                "receita_compras": round(receita_sem_compra, 2),
                "ticket_servico": round(receita_sem_serv / len(atend_sem_servico), 2) if atend_sem_servico else 0,
                "ticket_compra": round(receita_sem_compra / len(atend_sem_compra), 2) if atend_sem_compra else 0,
            }

    # Análise de queda por período do mês (semanas)
    semanas_mes = {}
    for a in atendimentos:
        sem_num = (a["data"].day - 1) // 7 + 1
        if sem_num not in semanas_mes:
            semanas_mes[sem_num] = {"atend": 0, "receita_serv": 0, "receita_compra": 0}
        semanas_mes[sem_num]["atend"] += 1
        if a["tipo"] in TIPOS_SERVICO:
            semanas_mes[sem_num]["receita_serv"] += a["valor"]
        elif a["tipo"] == "compra_produto":
            semanas_mes[sem_num]["receita_compra"] += a["valor"]

    alerta_queda = None
    if len(semanas_mes) >= 2:
        sems_ord = sorted(semanas_mes.items())
        for i in range(1, len(sems_ord)):
            sem_atual = sems_ord[i]
            sem_anterior = sems_ord[i - 1]
            dif_atend = sem_atual[1]["atend"] - sem_anterior[1]["atend"]
            if sem_anterior[1]["atend"] > 0 and dif_atend < 0:
                pct_queda = abs(dif_atend) / sem_anterior[1]["atend"] * 100
                if pct_queda >= 25:
                    alerta_queda = {
                        "semana_de": sem_anterior[0],
                        "semana_para": sem_atual[0],
                        "atend_de": sem_anterior[1]["atend"],
                        "atend_para": sem_atual[1]["atend"],
                        "pct_queda": round(pct_queda, 0),
                    }

    return {
        "total_atendimentos": total_atend,
        "qtd_servico": qtd_servico,
        "qtd_compras": qtd_compras,
        "receita_total": round(receita_total, 2),
        "receita_servico_puro": round(receita_servico_puro, 2),
        "receita_compras": round(receita_compras, 2),
        "taxa_conversao": round(taxa_conversao, 1),
        "dias_profissional": dias_prof,
        "custo_diaria": diaria,
        "custo_total": round(custo_total, 2),
        "lucro": round(lucro, 2),
        "lucro_servico": round(lucro_servico, 2),
        "ticket_medio": round(ticket_medio, 2),
        "ticket_medio_servico": round(ticket_medio_servico, 2),
        "ticket_medio_compra": round(ticket_medio_compra, 2),
        "media_atend_por_dia": round(media_atend_por_dia, 1),
        "tipos": tipos,
        "pagamentos_ranking": pagamentos_ranking,
        "atend_por_dia": atend_por_dia,
        "top_recorrentes": top_recorrentes_lista,
        "clientes_mes_total": len(clientes_mes),
        "clientes_retorno": len(clientes_retorno),
        "clientes_novas": len(clientes_novas),
        "pct_retorno": round(pct_retorno, 1),
        "comparativo_mes_anterior": {
            "atendimentos": atend_ant,
            "receita": round(receita_ant, 2),
        },
        "comparativo_ano_anterior": {
            "atendimentos": atend_aa,
            "receita": round(receita_aa, 2),
        },
        "resumo_semana": resumo_semana,
        "alerta_queda": alerta_queda,
    }


def conectar_servicos(credenciais_path):
    """Conecta na planilha de serviços."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_file(credenciais_path, scopes=scopes)
    gc = gspread.authorize(creds)
    planilha = gc.open_by_key(PLANILHA_SERVICOS_ID)
    abas = [ws.title for ws in planilha.worksheets()]
    return planilha, abas
