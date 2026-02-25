"""
Roda na pasta loja-automacao pra me mostrar a estrutura da planilha de serviços.
Cole a saída aqui no chat!

Uso: python ver_servicos.py
"""
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]
creds = Credentials.from_service_account_file("credentials/service_account.json", scopes=scopes)
gc = gspread.authorize(creds)

planilha = gc.open_by_key("1-UNfQN6y6OgntbwYzEwG7Z6UdJPw71I5sIo1EWchqz8")

print("=== ABAS DISPONÍVEIS ===")
for ws in planilha.worksheets():
    print(f"  → {ws.title} ({ws.row_count}x{ws.col_count})")

for ws in planilha.worksheets():
    print(f"\n{'='*70}")
    print(f"ABA: {ws.title}")
    print(f"{'='*70}")
    dados = ws.get_all_values()
    for i, linha in enumerate(dados[:25]):
        conteudo = [c for c in linha if c.strip()]
        if conteudo:
            print(f"  L{i+1:02d}: {linha[:15]}")
    print(f"  ... Total: {len(dados)} linhas")
