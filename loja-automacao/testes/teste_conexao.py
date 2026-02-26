import gspread
from google.oauth2.service_account import Credentials

# Configuração
CREDENCIAIS = "credentials/service_account.json"
PLANILHA_ID = "1Gdr6WSrf3SaL9WkvASIRcBi5nYKZDUK7FysPDzwI_HU"

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

print("1. Testando credenciais...")
try:
    creds = Credentials.from_service_account_file(CREDENCIAIS, scopes=scopes)
    print("   ✅ Credenciais OK!")
except Exception as e:
    print(f"   ❌ Erro nas credenciais: {e}")
    exit()

print("2. Conectando ao Google Sheets...")
try:
    gc = gspread.authorize(creds)
    print("   ✅ Conexão OK!")
except Exception as e:
    print(f"   ❌ Erro na conexão: {e}")
    exit()

print("3. Abrindo a planilha de vendas...")
try:
    planilha = gc.open_by_key(PLANILHA_ID)
    print(f"   ✅ Planilha encontrada: {planilha.title}")
except Exception as e:
    print(f"   ❌ Erro ao abrir planilha: {e}")
    print("   Verifique se compartilhou a planilha com o e-mail da conta de serviço.")
    exit()

print("4. Listando abas disponíveis...")
try:
    abas = [ws.title for ws in planilha.worksheets()]
    print(f"   ✅ {len(abas)} abas encontradas:")
    for aba in abas:
        print(f"      - {aba}")
except Exception as e:
    print(f"   ❌ Erro ao listar abas: {e}")
    exit()

print()
print("=" * 40)
print("🎉 TUDO FUNCIONANDO! Pode avançar!")
print("=" * 40)
