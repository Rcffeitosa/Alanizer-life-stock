# Aplicativo de Rastreabilidade de Estoque

Este é um aplicativo desenvolvido em Python e Streamlit para analisar e consolidar dados de rastreabilidade de itens em estoque a partir de três planilhas Excel.

## Como Executar

1. **Instale as dependências:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Execute a aplicação:**

   ```bash
   streamlit run app.py
   ```

3. **Use a interface:**
   - Faça o upload das três planilhas solicitadas (`Status_da_Ordem.xlsx`, `Consulta_Rastreabilidade.xlsx`, `Consulta_de_Estoque.xlsx`).
   - Clique no botão "Gerar Relatório" para processar os dados.
   - O relatório será exibido na tela e você poderá exportá-lo como um arquivo `.xlsx` ou `.csv`.
