# loja-automacao — Relatório Semanal Bem Me Quer

Sistema automático de geração de relatório semanal de vendas para a loja Bem Me Quer.

## Como usar

1. Configure as credenciais do Google Sheets (veja `.env.example`)
2. Instale as dependências: `pip install gspread google-auth openpyxl pandas`
3. Execute o relatório: `python relatorio_semanal.py`

## Estrutura

```
loja-automacao/
├── relatorio_semanal.py     # Script principal
├── financeiro_analise.py    # Análise financeira (Excel)
├── servicos_analise.py      # Análise de serviços (Google Sheets)
├── fornecedores_mes.py      # Lista de fornecedores do mês
├── executar_relatorio.py    # Executa o relatório sem inputs
├── gerar_html_simples.py    # Gera apenas o HTML
├── ver_servicos.py          # Utilitário para inspecionar planilha
├── debug/                   # Scripts de diagnóstico (desenvolvimento)
├── testes/                  # Scripts de teste
├── credentials/             # Credenciais Google (NÃO commitar!)
└── .env.example             # Modelo de variáveis de ambiente
```

## ⚠️ Segurança

- Nunca commite a pasta `credentials/` ou o arquivo `.env`
- O arquivo `.gitignore` já está configurado para ignorá-los
