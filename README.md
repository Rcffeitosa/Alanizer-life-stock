# Alanizer Life Stock - Documentação Técnica

**Versão:** 1.0.0
**Autor:** Ricardo Feitosa

## 1. Visão Geral

O **Alanizer Life Stock** é uma aplicação web desenvolvida em Python com o framework Streamlit. Sua principal função é automatizar a análise de rastreabilidade de itens em estoque, consolidando informações de três fontes de dados distintas (planilhas) em um relatório unificado. A ferramenta visa identificar itens com quantidades não alocadas, verificar seus possíveis endereços de armazenamento e comparar com o estoque atual, otimizando a gestão e a tomada de decisão.

## 2. Requisitos Técnicos

Para executar o projeto, é necessário ter o Python instalado e as seguintes bibliotecas, que podem ser instaladas a partir do arquivo `requirements.txt`.

- **`pandas`**: Utilizada para manipulação e análise dos dados das planilhas.
- **`openpyxl`**: Motor para leitura e escrita de arquivos no formato `.xlsx`.
- **`streamlit`**: Framework utilizado para criar a interface web interativa da aplicação.

## 3. Como Executar

Siga os passos abaixo para colocar a aplicação em funcionamento no seu ambiente local.

1. **Clone ou baixe o repositório**

   Certifique-se de ter todos os arquivos do projeto (`app.py`, `requirements.txt`, etc.) em um mesmo diretório.

2. **Instale as dependências**

   Abra um terminal ou prompt de comando no diretório do projeto e execute o comando:

   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação**

   No mesmo terminal, execute o seguinte comando para iniciar o servidor do Streamlit:

   ```bash
   streamlit run app.py
   ```

   Após a execução, uma aba será aberta no seu navegador padrão com a interface da aplicação, geralmente no endereço `http://localhost:8501`.

4. **Utilize a interface**

   1. Na barra lateral, faça o upload das três planilhas solicitadas.
   2. Clique no botão **"Gerar Relatório"**.
   3. Aguarde o processamento. O relatório final será exibido na tela principal.
   4. Utilize os botões **"Baixar como CSV"** ou **"Baixar como XLSX"** para exportar o resultado.

## 4. Lógica de Processamento (Arquitetura)

A lógica central da aplicação reside na função `process_data` dentro do `app.py`. O fluxo de processamento é o seguinte:

1. **Leitura e Padronização (`read_file`)**
   - Cada arquivo carregado (CSV ou Excel) é lido por esta função.
   - Os nomes das colunas são padronizados: espaços extras são removidos, o texto é convertido para o formato *Title Case* e nomes comuns (como `Description` ou `Descricao`) são mapeados para um padrão único (`Descrição`). Isso garante a robustez do script contra pequenas variações nos arquivos de entrada.

2. **Processamento do `Status_da_Ordem`**
   - A aplicação seleciona as colunas essenciais: `Item`, `Descrição` e `Quantidade Não Alocada`.
   - Filtra os dados para manter apenas os itens cuja `Quantidade Não Alocada` é maior que zero, focando apenas nos casos que necessitam de ação.

3. **Processamento da `Consulta_Rastreabilidade`**
   - A função busca por uma coluna de endereço. Ela é inteligente e pode seguir duas estratégias:
     - **Estratégia 1**: Se uma coluna chamada `Endereço` existe, ela é usada diretamente.
     - **Estratégia 2**: Se as colunas `Endereço Origem` e `Endereço Destino` existem, elas são combinadas em uma única lista de endereços por item.
   - Os endereços que começam com **'A0'** são **excluídos** da análise, pois são considerados endereços de expedição ou áreas não relevantes para o armazenamento.

4. **Processamento da `Consulta_de_Estoque`**
   - As colunas `Item` e `Quantidade Atual` são extraídas.
   - A `Quantidade Atual` é convertida para um formato numérico para permitir cálculos.

5. **Consolidação e Geração do Relatório (`merge`)**
   - O `DataFrame` do **Status da Ordem** é a base do relatório.
   - É feito um `merge` (LEFT JOIN) com os dados de **Rastreabilidade** usando a coluna `Item` como chave. Isso adiciona o endereço de armazenamento a cada item não alocado.
   - Em seguida, um segundo `merge` (LEFT JOIN) é realizado com os dados de **Estoque**, também pela coluna `Item`. Isso adiciona a quantidade atual em estoque.

6. **Finalização e Análise**
   - Para itens que não tiveram correspondência na Rastreabilidade, o campo `Endereço` é preenchido com **"Sem Rastreabilidade"**.
   - Uma nova coluna, `Status da Quantidade`, é criada para comparar a `Quantidade Não Alocada` com a `Quantidade Atual`, fornecendo um status claro sobre a disponibilidade do item.
   - As colunas são renomeadas e reordenadas para apresentar um relatório final limpo e intuitivo.

## 5. Estrutura dos Arquivos de Entrada

Para que a aplicação funcione corretamente, as planilhas de entrada devem conter as seguintes colunas (o nome pode ter pequenas variações, pois o script tenta padronizá-los):

- **`Status_da_Ordem.xlsx`**
  - `Item`: Código do produto.
  - `Description` ou `Descrição`: Descrição do produto.
  - `Quantidade Nao Alocada`: Quantidade pendente de alocação.

- **`Consulta_Rastreabilidade.xlsx`**
  - `Item`: Código do produto.
  - Deve conter ou a coluna `Endereço` ou as colunas `Endereço Origem` e `Endereço Destino`.

- **`Consulta_de_Estoque.xlsx`**
  - `Item`: Código do produto.
  - `Quantidade Atual`: Quantidade total do item em estoque.

## 6. Relatório Final (Saída)

O relatório gerado contém as seguintes colunas:

- **`Item`**: Código do produto.
- **`Descrição`**: Descrição do produto.
- **`Quantidade Não Alocada`**: Quantidade que precisa ser rastreada.
- **`Endereço`**: O último endereço de armazenamento conhecido do item (excluindo 'A0').
- **`Rastreabilidade / Qnt. Atual`**: Status comparativo entre a quantidade não alocada e a quantidade em estoque.
