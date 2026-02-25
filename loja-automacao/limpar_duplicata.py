"""
Remover linha duplicada do histórico
"""
import json

caminho = "historico_FEVEREIRO26.json"

with open(caminho, "r", encoding="utf-8") as f:
    dados = json.load(f)

print(f"Semanas antes: {len(dados['semanas'])}")
print("Períodos:")
for s in dados['semanas']:
    print(f"  - {s['periodo']}")

# Manter apenas as 4 primeiras semanas (remover "16/02 a 22/02")
dados['semanas'] = [s for s in dados['semanas'] if s['periodo'] != "16/02 a 22/02"]

print(f"\nSemanas depois: {len(dados['semanas'])}")
print("Períodos:")
for s in dados['semanas']:
    print(f"  - {s['periodo']}")

with open(caminho, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print("\n✅ Arquivo atualizado!")
