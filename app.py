import streamlit as st
import pandas as pd
import io
import numpy as np

# --- Funções de Processamento ---

def read_file(uploaded_file):
    """Lê, limpa e padroniza os nomes das colunas de um arquivo carregado."""
    if uploaded_file is None:
        return None
    
    try:
        file_name = uploaded_file.name
        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', dtype=str)
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str)
        else:
            st.error(f"Formato de arquivo não suportado: {file_name}. Por favor, use CSV ou XLSX.")
            return None

        # --- Padronização Robusta de Nomes de Colunas ---
        # 1. Remove espaços extras. 2. Converte para Title Case. 3. Substitui variações comuns.
        cols = df.columns.str.strip().str.title()
        
        replacements = {
            'Description': 'Descrição',
            'Descricao': 'Descrição',
            'Endereco': 'Endereço',
            'Endereco Origem': 'Endereço Origem',
            'Endereco Destino': 'Endereço Destino',
            'Quantidade Nao Alocada': 'Quantidade Não Alocada'
        }
        
        df.columns = [replacements.get(col, col) for col in cols]
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {file_name}: {e}")
        return None

@st.cache_data
def process_data(status_file, rastreabilidade_file, estoque_file):
    """Função principal para processar os três arquivos Excel e gerar o relatório final."""
    try:
        # 1. Processar o arquivo de Status da Ordem
        df_status = read_file(status_file)
        if df_status is None: return None

        required_cols = ['Item', 'Descrição', 'Quantidade Não Alocada']
        if not all(col in df_status.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df_status.columns]
            st.error(f"Erro no arquivo de status: Coluna(s) não encontrada(s): {missing}.")
            return None

        df_status_processed = df_status[required_cols].copy()
        df_status_processed['Quantidade Não Alocada'] = pd.to_numeric(df_status_processed['Quantidade Não Alocada'], errors='coerce').fillna(0)
        df_status_processed = df_status_processed[df_status_processed['Quantidade Não Alocada'] > 0].copy()
        
        # Otimização: Obter lista de itens de interesse para filtrar as outras planilhas
        itens_de_interesse = df_status_processed['Item'].unique()

        # 2. Processar Rastreabilidade para obter endereços 'A0'
        df_rastreabilidade = read_file(rastreabilidade_file)
        if df_rastreabilidade is None: return None
        
        if 'Endereço' in df_rastreabilidade.columns:
            df_rast_enderecos = df_rastreabilidade[['Item', 'Endereço']]
        elif 'Endereço Origem' in df_rastreabilidade.columns and 'Endereço Destino' in df_rastreabilidade.columns:
            df_rast_enderecos = df_rastreabilidade.melt(id_vars=['Item'], value_vars=['Endereço Origem', 'Endereço Destino'], value_name='Endereço')[['Item', 'Endereço']]
        else:
            df_rast_enderecos = pd.DataFrame(columns=['Item', 'Endereço']) # Continua com dataframe vazio se não achar

        df_rast_enderecos = df_rast_enderecos.dropna(subset=['Endereço'])
        df_rast_enderecos = df_rast_enderecos[
            df_rast_enderecos['Item'].isin(itens_de_interesse) &
            df_rast_enderecos['Endereço'].astype(str).str.startswith('A0')
        ][['Item', 'Endereço']]

        # 3. Processar Estoque para obter endereços 'A0' e quantidades
        df_estoque = read_file(estoque_file)
        if df_estoque is None: return None

        if 'Endereço' not in df_estoque.columns or 'Qtd Atual' not in df_estoque.columns:
            st.error("Erro no arquivo de Estoque: As colunas 'Endereço' e/ou 'Qtd Atual' não foram encontradas.")
            return None
        
        df_estoque.rename(columns={'Qtd Atual': 'Qtd em Estoque'}, inplace=True)
        df_estoque['Qtd em Estoque'] = pd.to_numeric(df_estoque['Qtd em Estoque'], errors='coerce').fillna(0)
        
        df_estoque_enderecos = df_estoque[
            df_estoque['Item'].isin(itens_de_interesse) &
            df_estoque['Endereço'].astype(str).str.startswith('A0')
        ].copy()
        
        df_estoque_enderecos = df_estoque_enderecos.groupby(['Item', 'Endereço'], as_index=False)['Qtd em Estoque'].sum()

        # 4. Consolidar todos os endereços 'A0' únicos de ambas as fontes
        todos_enderecos_a0 = pd.concat([
            df_rast_enderecos[['Item', 'Endereço']],
            df_estoque_enderecos[['Item', 'Endereço']]
        ]).drop_duplicates()

        # 5. Construir o relatório final de forma otimizada
        df_final = pd.merge(df_status_processed, todos_enderecos_a0, on='Item', how='left')
        df_final = pd.merge(df_final, df_estoque_enderecos, on=['Item', 'Endereço'], how='left')
        
        df_final['Endereço'].fillna('Sem Endereço A0 Conhecido', inplace=True)
        df_final['Qtd em Estoque'].fillna(0, inplace=True)
        
        df_final['Status da Quantidade'] = np.where(
            df_final['Qtd em Estoque'] > 0,
            df_final['Qtd em Estoque'].astype(int).astype(str),
            'VIDA'
        )
        
        df_final.rename(columns={
            'Endereço': 'Endereço',
            'Status da Quantidade': 'Rastreabilidade / Qnt. Atual'
        }, inplace=True)
        
        return df_final[['Item', 'Descrição', 'Quantidade Não Alocada', 'Endereço', 'Rastreabilidade / Qnt. Atual']]

    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento: {e}")
        return None

    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento: {e}")
        return None

# --- Funções da Interface ---

def to_excel(df):
    """Converte um DataFrame para um arquivo Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    processed_data = output.getvalue()
    return processed_data

def clear_uploads():
    """Callback para limpar o estado dos uploaders, incrementando o contador de limpeza."""
    st.session_state.clear_count += 1
    if 'final_report' in st.session_state:
        del st.session_state['final_report']

# --- Interface do Streamlit ---

st.set_page_config(page_title="Rastreabilidade de Estoque", layout="wide")

st.title('✅ Alanizer Life Stock Versão 1.0.0 - By Ricardo Feitosa')
st.markdown("""
Esta ferramenta integra dados de três planilhas para gerar um relatório de rastreabilidade
 """)

# Inicializar o contador de limpeza no estado da sessão, se não existir
if 'clear_count' not in st.session_state:
    st.session_state.clear_count = 0

# Seção de Upload
with st.sidebar:
    st.header('📤 Upload das Planilhas')
    # Usar chaves dinâmicas baseadas no contador de limpeza para forçar a recriação do widget
    status_file = st.file_uploader("1. Status_da_Ordem", type=['xlsx', 'csv'], key=f"status_uploader_{st.session_state.clear_count}")
    rastreabilidade_file = st.file_uploader("2. Consulta_Rastreabilidade", type=['xlsx', 'csv'], key=f"rastreabilidade_uploader_{st.session_state.clear_count}")
    estoque_file = st.file_uploader("3. Consulta_de_Estoque", type=['xlsx', 'csv'], key=f"estoque_uploader_{st.session_state.clear_count}")

    # Criar colunas para os botões
    col1, col2 = st.columns(2)

    with col1:
        gerar_relatorio = st.button('Gerar Relatório', type="primary", use_container_width=True)

    with col2:
        st.button('Limpar', on_click=clear_uploads, use_container_width=True)

# Lógica principal do relatório
if gerar_relatorio:
    if status_file and rastreabilidade_file and estoque_file:
        with st.spinner('Processando dados... Por favor, aguarde.'):
            final_report = process_data(status_file, rastreabilidade_file, estoque_file)
        
        if final_report is not None:
            st.success('Relatório gerado com sucesso!')
            st.dataframe(final_report)
            
            # Armazenar o relatório no estado da sessão para download
            st.session_state['final_report'] = final_report
        else:
            st.error("Não foi possível gerar o relatório. Verifique os arquivos e tente novamente.")
    else:
        st.warning('Por favor, faça o upload das três planilhas para continuar.')

# Seção de Download (aparece após gerar o relatório)
if 'final_report' in st.session_state and not st.session_state['final_report'].empty:
    st.header('📥 Download do Relatório')
    report_df = st.session_state['final_report']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download em CSV
        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar como CSV",
            data=csv,
            file_name='relatorio_rastreabilidade.csv',
            mime='text/csv',
        )
        
    with col2:
        # Download em XLSX
        excel_data = to_excel(report_df)
        st.download_button(
            label="Baixar como XLSX",
            data=excel_data,
            file_name='relatorio_rastreabilidade.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
