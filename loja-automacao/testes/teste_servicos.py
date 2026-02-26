"""
Teste de conexão com a planilha de serviços.
Roda: python teste_servicos.py
"""
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

print("1. Carregando credenciais...")
creds = Credentials.from_service_account_file("credentials/service_account.json", scopes=scopes)
gc = gspread.authorize(creds)

print("2. Abrindo planilha de serviços...")
try:
    planilha = gc.open_by_key("1-UNfQN6y6OgntbwYzEwG7Z6UdJPw71I5sIo1EWchqz8")
    print("   ✅ Planilha aberta com sucesso!")
except Exception as e:
    print(f"   ❌ ERRO ao abrir: {e}")
    print("\n   → A planilha NÃO está compartilhada com a conta de serviço.")
    print("   → Vá na planilha de serviços → Compartilhar → adicione o email da conta.")
    exit()

print("\n3. Abas encontradas:")
for ws in planilha.worksheets():
    print(f"   → '{ws.title}'")

print("\n4. Buscando FEVEREIRO/26...")
abas = [ws.title for ws in planilha.worksheets()]
for aba in abas:
    if "FEVER" in aba.upper() and "26" in aba:
        print(f"   ✅ Encontrada: '{aba}'")
        break
else:
    print("   ❌ Não encontrou. Verifique os nomes acima.")
