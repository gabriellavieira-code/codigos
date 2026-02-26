import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]
creds = Credentials.from_service_account_file("credentials/service_account.json", scopes=scopes)
gc = gspread.authorize(creds)
planilha = gc.open_by_key("1-UNfQN6y6OgntbwYzEwG7Z6UdJPw71I5sIo1EWchqz8")

aba = planilha.worksheet("FEVEREIRO/26")
dados = aba.get_all_values()

print(f"Total linhas: {len(dados)}")
print()
for i, linha in enumerate(dados[:10]):
    print(f"L{i+1:02d}: {linha}")
