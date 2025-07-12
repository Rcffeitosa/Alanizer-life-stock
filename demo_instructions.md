# 🎯 Demonstração da Aplicação de Rastreabilidade

## 🚀 Como Executar

### 1. Aplicação Web (Streamlit)
```bash
python3 run.py web
```
- Abra o navegador em: `http://localhost:8501`
- Interface gráfica intuitiva
- Upload de arquivos via drag & drop
- Visualização de estatísticas e gráficos

### 2. Interface de Linha de Comando (CLI)
```bash
python3 run.py cli -r rastreabilidade.csv -s status.xlsx -e estoque.xlsx
```
- Processamento em lote
- Ideal para automação
- Logs detalhados
- Modo verboso disponível

### 3. Executar Testes
```bash
python3 run.py test
```
- Validação automática da aplicação
- Testes unitários e de integração
- Verificação de funcionamento

## 📄 Arquivos de Exemplo

### Arquivo de Rastreabilidade (CSV)
```csv
Item,Descrição do Item,Endereço Origem,Endereço Destino
ITEM001,Produto A,A0001,A0002
ITEM002,Produto B,A0003,A0004
ITEM003,Produto C,B0001,A0005
```

### Arquivo de Status da Ordem (Excel)
```excel
Item          | Description | Quantidade Não Alocada
ITEM001      | Desc A      | 10
ITEM002      | Desc B      | 
ITEM003      | Desc C      | 5
```

### Arquivo de Consulta de Estoque (Excel)
```excel
Item    | Descrição | Endereço    | Qtd Atual
ITEM001 | Produto A | A0001A0002  | 15
ITEM002 | Produto B | A0003A0004  | 0
ITEM003 | Produto C | A0005       | 8
```

## 🎯 Resultado Esperado

O sistema gerará um relatório Excel com:
- Items filtrados por endereços A0*
- Status "VIDA" para items sem quantidade alocada
- Quantidades consolidadas por endereço
- Estatísticas e visualizações

## 🔧 Funcionalidades Demonstradas

1. **Validação de Arquivos**: Formato, tamanho e estrutura
2. **Processamento de Dados**: Merge, limpeza e transformação
3. **Regras de Negócio**: Filtros específicos e cálculos
4. **Geração de Relatórios**: Excel com dados processados
5. **Visualizações**: Gráficos e estatísticas em tempo real
6. **Tratamento de Erros**: Mensagens claras e logs detalhados

## 🎨 Interface Web - Recursos

- **Upload Múltiplo**: Drag & drop para os três arquivos
- **Validação Visual**: Feedback imediato sobre erros
- **Progress Bar**: Acompanhamento do processamento
- **Estatísticas**: Métricas em tempo real
- **Gráficos**: Visualização da distribuição de dados
- **Download**: Botão para baixar o relatório gerado

## 💻 CLI - Opções Avançadas

```bash
# Processamento básico
python3 run.py cli -r data.csv -s status.xlsx -e estoque.xlsx

# Com arquivo de saída personalizado
python3 run.py cli -r data.csv -s status.xlsx -e estoque.xlsx -o meu_relatorio.xlsx

# Modo verboso com logs detalhados
python3 run.py cli -r data.csv -s status.xlsx -e estoque.xlsx --verbose --log-level DEBUG

# Apenas validar arquivos sem processar
python3 run.py cli -r data.csv -s status.xlsx -e estoque.xlsx --validate-only
```

## 📊 Exemplo de Saída

```
=== ESTATÍSTICAS DO RELATÓRIO ===
Total de items: 2
Items com status VIDA: 1
Items com quantidade: 1
Endereços únicos: 2

✅ Relatório gerado com sucesso: Relatorio_Rastreabilidade_20240101_120000.xlsx
```

## 🔍 Troubleshooting

### Problema: Colunas faltando
**Solução**: Verificar se os arquivos contêm todas as colunas obrigatórias

### Problema: Arquivo muito grande
**Solução**: Usar CLI para arquivos maiores que 200MB

### Problema: Formato não suportado
**Solução**: Usar apenas CSV ou Excel (.xlsx, .xls)

### Problema: Erro de memória
**Solução**: Processar arquivos em lotes menores

## 📝 Logs

Os logs são salvos automaticamente em:
- `rastreabilidade_YYYYMMDD.log`
- Contém informações detalhadas sobre o processamento
- Útil para debugging e auditoria

## 🎉 Sucesso!

Se tudo funcionou corretamente, você deve ter:
1. ✅ Aplicação rodando sem erros
2. ✅ Arquivos processados com sucesso
3. ✅ Relatório Excel gerado
4. ✅ Estatísticas exibidas
5. ✅ Logs salvos para auditoria