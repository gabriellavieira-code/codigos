#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

# Import das funções do projeto
import sys
sys.path.insert(0, r'c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao')
from servicos_analise import ler_atendimentos_aba

# Credenciais
cred_path = r"c:\Users\gaabi\OneDrive\Desktop\Codigos\loja-automacao\credentials\service_account.json"
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(cred_path, scopes=scopes)
gc = gspread.authorize(creds)

# Abrir planilha de serviços
sh = gc.open_by_key("1-UNfQN6y6OgntbwYzEwG7Z6UdJPw71I5sIo1EWchqz8")

# Listar abas
abas = [ws.title for ws in sh.worksheets()]
print(f"Abas disponíveis: {abas}\n")

# Ler dados de fevereiro e março
atend_fev = ler_atendimentos_aba(sh, "FEVEREIRO/26")
print(f"Fevereiro/26: {len(atend_fev)} atendimentos")
if atend_fev:
    print("Primeiros 5:")
    for a in atend_fev[:5]:
        print(f"  {a['data'].strftime('%d/%m')} - {a['cliente'][:20]} - {a['tipo']} - R${a['valor']:.2f}")

atend_mar = None
for aba in abas:
    if "MARÇO" in aba.upper() and "26" in aba:
        atend_mar = ler_atendimentos_aba(sh, aba)
        print(f"\n{aba}: {len(atend_mar)} atendimentos")
        if atend_mar:
            print("Primeiros 5:")
            for a in atend_mar[:5]:
                print(f"  {a['data'].strftime('%d/%m')} - {a['cliente'][:20]} - {a['tipo']} - R${a['valor']:.2f}")
        break

# Filtrar para semana 23/02 a 01/03
semana_inicio = date(2026, 2, 23)
semana_fim = date(2026, 3, 1)

todos_atend = atend_fev if atend_fev else []
if atend_mar:
    todos_atend.extend(atend_mar)

atend_semana = [a for a in todos_atend 
                if semana_inicio <= a["data"] <= semana_fim]

print(f"\n{'='*60}")
print(f"Atendimentos na semana {semana_inicio.strftime('%d/%m/%Y')} a {semana_fim.strftime('%d/%m/%Y')}: {len(atend_semana)}")
print(f"{'='*60}")
for a in sorted(atend_semana, key=lambda x: x["data"]):
    print(f"  {a['data'].strftime('%d/%m')} ({['seg','ter','qua','qui','sex','sab','dom'][a['data'].weekday()]}) - {a['cliente'][:30]:30} - {a['tipo']:20} - R${a['valor']:6.2f}")
