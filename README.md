# 📊 Processador de Rastreabilidade

Uma aplicação Python para processar e gerar relatórios de rastreabilidade de estoque, integrando dados de múltiplas fontes.

## 🚀 Funcionalidades

- **Interface Web**: Interface intuitiva usando Streamlit
- **Interface CLI**: Linha de comando para automação
- **Processamento de Dados**: Integração de três tipos de arquivo
- **Validação**: Verificação automática de formato e integridade
- **Relatórios**: Geração de relatórios em Excel
- **Estatísticas**: Análise visual dos dados processados

## 📋 Requisitos

- Python 3.8+
- pandas
- openpyxl
- streamlit
- plotly
- pathlib2

## 🔧 Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## 🖥️ Uso da Interface Web

Para iniciar a aplicação web:

```bash
streamlit run app.py
```

A aplicação será aberta automaticamente no navegador (geralmente em `http://localhost:8501`).

### Arquivos Necessários

A aplicação requer três arquivos:

1. **Arquivo de Rastreabilidade** (CSV ou Excel)
   - Colunas necessárias:
     - `Item`
     - `Descrição do Item`
     - `Endereço Origem`
     - `Endereço Destino`

2. **Arquivo de Status da Ordem** (Excel)
   - Colunas necessárias:
     - `Item`
     - `Description`
     - `Quantidade Não Alocada`

3. **Arquivo de Consulta de Estoque** (Excel)
   - Colunas necessárias:
     - `Item`
     - `Descrição`
     - `Endereço`
     - `Qtd Atual`

## 💻 Uso da Interface CLI

Para usar a interface de linha de comando:

```bash
python cli.py -r arquivo_rastreabilidade.csv -s arquivo_status.xlsx -e arquivo_estoque.xlsx
```

### Opções da CLI

- `-r, --rastreabilidade`: Arquivo de rastreabilidade (obrigatório)
- `-s, --status`: Arquivo de status da ordem (obrigatório)
- `-e, --estoque`: Arquivo de consulta de estoque (obrigatório)
- `-o, --output`: Nome do arquivo de saída (opcional)
- `--log-level`: Nível de log (DEBUG, INFO, WARNING, ERROR)
- `--verbose`: Modo verboso
- `--validate-only`: Apenas validar arquivos

### Exemplo de Uso

```bash
# Processamento básico
python cli.py -r rastreabilidade.csv -s status.xlsx -e estoque.xlsx

# Com arquivo de saída personalizado
python cli.py -r rastreabilidade.csv -s status.xlsx -e estoque.xlsx -o relatorio_customizado.xlsx

# Modo verboso com log detalhado
python cli.py -r rastreabilidade.csv -s status.xlsx -e estoque.xlsx --verbose --log-level DEBUG

# Apenas validar arquivos
python cli.py -r rastreabilidade.csv -s status.xlsx -e estoque.xlsx --validate-only
```

## 🔄 Processo de Transformação

A aplicação realiza as seguintes operações:

1. **Carregamento**: Lê os três arquivos de entrada
2. **Validação**: Verifica formato, tamanho e colunas obrigatórias
3. **Processamento**:
   - Combina endereços de origem e destino
   - Cria chaves únicas para relacionamento
   - Remove duplicatas
   - Faz merge entre as tabelas
4. **Regras de Negócio**:
   - Filtra apenas endereços que começam com 'A0'
   - Define status 'VIDA' para itens sem quantidade alocada
   - Calcula quantidades por endereço
5. **Geração do Relatório**: Cria arquivo Excel com dados processados

## 📊 Saída

O relatório final contém as seguintes colunas:

- `Item`: Código do item
- `Descrição do Item`: Descrição do item
- `Endereço`: Endereço consolidado
- `Chave1`: Chave única (Item + Endereço)
- `Não Alocado`: Quantidade não alocada
- `Qnt endereço`: Quantidade no endereço
- `Status`: Status do item (VIDA ou vazio)

## 📈 Estatísticas

A aplicação gera estatísticas do processamento:

- Total de items processados
- Items com status 'VIDA'
- Items com quantidade
- Número de endereços únicos
- Gráfico de distribuição por status

## 🐛 Resolução de Problemas

### Erro: "Colunas faltando"

Verifique se os arquivos contêm todas as colunas obrigatórias com os nomes exatos.

### Erro: "Arquivo muito grande"

O limite é de 200MB por arquivo. Considere dividir arquivos grandes.

### Erro: "Formato não suportado"

Use apenas arquivos CSV ou Excel (.xlsx, .xls).

### Erro de Memória

Para arquivos muito grandes, use a interface CLI que é mais eficiente em memória.

## 🔧 Configuração

As configurações podem ser ajustadas no arquivo `config.py`:

- Formatos suportados
- Tamanho máximo de arquivo
- Colunas obrigatórias
- Mensagens de erro e sucesso
- Configurações de logging

## 📝 Logs

Os logs são salvos em arquivos diários no formato:
`rastreabilidade_YYYYMMDD.log`

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Envie um pull request

## 📄 Licença

Este projeto é de código aberto.

## 🆘 Suporte

Para dúvidas ou problemas:

1. Verifique os logs de erro
2. Consulte a seção de resolução de problemas
3. Use o modo `--verbose` para mais detalhes
4. Verifique se os arquivos estão no formato correto

## 🔄 Versão

Versão atual: 1.0.0

### Histórico de Versões

- v1.0.0: Versão inicial com interface web e CLI completas
