import streamlit as st
import pandas as pd
import io
import numpy as np
from functools import lru_cache
import gc

# --- Performance Configuration ---
# Configure pandas for better memory usage
pd.options.mode.chained_assignment = None
pd.options.display.max_columns = None

# --- Cached Functions for Performance ---

@st.cache_data(ttl=3600, max_entries=3)  # Cache for 1 hour, max 3 entries
def read_file_cached(file_content, file_name, file_type):
    """Cached version of file reading with optimized memory usage."""
    try:
        if file_type == 'csv':
            # Use more efficient CSV reading with chunking for large files
            df = pd.read_csv(
                io.StringIO(file_content.decode('utf-8')), 
                sep=None, 
                engine='c',  # Faster C engine
                dtype=str,
                low_memory=False
            )
        elif file_type in ['xlsx', 'xls']:
            df = pd.read_excel(
                io.BytesIO(file_content), 
                engine='openpyxl', 
                dtype=str
            )
        else:
            raise ValueError(f"Unsupported file format: {file_name}")

        # Memory optimization: convert object columns to category where appropriate
        for col in df.columns:
            if df[col].dtype == 'object':
                unique_values = df[col].nunique()
                total_values = len(df[col])
                # Convert to category if less than 50% unique values
                if unique_values / total_values < 0.5:
                    df[col] = df[col].astype('category')

        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {file_name}: {e}")
        return None

@lru_cache(maxsize=32)
def standardize_column_name(col_name):
    """Cached function for column name standardization."""
    col = str(col_name).strip().title()
    
    replacements = {
        'Description': 'Descrição',
        'Descricao': 'Descrição',
        'Endereco': 'Endereço',
        'Endereco Origem': 'Endereço Origem',
        'Endereco Destino': 'Endereço Destino',
        'Quantidade Nao Alocada': 'Quantidade Não Alocada'
    }
    
    return replacements.get(col, col)

def read_file(uploaded_file):
    """Optimized file reading with caching and memory management."""
    if uploaded_file is None:
        return None
    
    try:
        file_name = uploaded_file.name
        file_content = uploaded_file.getvalue()
        
        # Determine file type
        if file_name.endswith('.csv'):
            file_type = 'csv'
        elif file_name.endswith(('.xlsx', '.xls')):
            file_type = 'xlsx'
        else:
            st.error(f"Formato de arquivo não suportado: {file_name}. Por favor, use CSV ou XLSX.")
            return None

        # Use cached reading
        df = read_file_cached(file_content, file_name, file_type)
        
        if df is None:
            return None

        # Optimize column standardization
        df.columns = [standardize_column_name(col) for col in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {uploaded_file.name}: {e}")
        return None

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def process_status_data(df_status):
    """Optimized status data processing with caching."""
    required_cols = ['Item', 'Descrição', 'Quantidade Não Alocada']
    missing_cols = [col for col in required_cols if col not in df_status.columns]

    if missing_cols:
        st.error(f"Erro ao processar o arquivo de status. Coluna(s) essencial(is) não encontrada(s): {missing_cols}.")
        st.info(f"Colunas disponíveis no arquivo: {list(df_status.columns)}")
        return None

    # Optimize data filtering
    df_processed = df_status[required_cols].copy()
    
    # Convert to numeric for efficient filtering
    df_processed['Quantidade Não Alocada'] = pd.to_numeric(df_processed['Quantidade Não Alocada'], errors='coerce')
    df_processed = df_processed[df_processed['Quantidade Não Alocada'] > 0].copy()
    
    return df_processed

@st.cache_data(ttl=1800)
def process_rastreabilidade_data(df_rastreabilidade):
    """Optimized rastreabilidade data processing with caching."""
    if 'Endereço' in df_rastreabilidade.columns:
        df_melted = df_rastreabilidade[['Item', 'Endereço']].copy()
    elif 'Endereço Origem' in df_rastreabilidade.columns and 'Endereço Destino' in df_rastreabilidade.columns:
        # Optimize melting operation
        df_melted = pd.melt(
            df_rastreabilidade[['Item', 'Endereço Origem', 'Endereço Destino']],
            id_vars=['Item'],
            value_vars=['Endereço Origem', 'Endereço Destino'],
            value_name='Endereço'
        )
    else:
        st.error("Erro Crítico no arquivo de Rastreabilidade: Nenhuma coluna de endereço válida encontrada.")
        return None

    # Optimize filtering with vectorized operations
    df_filtered = df_melted.dropna(subset=['Endereço'])
    df_filtered = df_filtered[df_filtered['Endereço'].str.startswith('A0', na=False)].copy()
    df_filtered.drop_duplicates(subset=['Item', 'Endereço'], inplace=True)

    # Optimize groupby operation
    enderecos_rastreabilidade = (
        df_filtered.sort_values('Endereço')
        .groupby('Item', as_index=False)
        .agg({'Endereço': lambda x: list(x)})
        .rename(columns={'Endereço': 'Endereços A0 (Rastreabilidade)'})
    )
    
    return enderecos_rastreabilidade

@st.cache_data(ttl=1800)
def process_estoque_data(df_estoque, itens_status):
    """Optimized estoque data processing with caching."""
    if 'Endereço' not in df_estoque.columns:
        st.error("Erro Crítico no arquivo de Estoque: A coluna 'Endereço' não foi encontrada.")
        return None

    # Rename for clarity
    if 'Qtd Atual' in df_estoque.columns:
        df_estoque = df_estoque.rename(columns={'Qtd Atual': 'Qtd em Estoque'})

    # Optimize filtering with vectorized operations
    mask = (
        df_estoque['Item'].isin(itens_status) & 
        df_estoque['Endereço'].str.startswith('A0', na=False)
    )
    df_estoque_filtered = df_estoque[mask].copy()
    
    # Convert to numeric efficiently
    df_estoque_filtered['Qtd em Estoque'] = pd.to_numeric(
        df_estoque_filtered['Qtd em Estoque'], 
        errors='coerce'
    ).fillna(0)

    # Optimize groupby operation
    df_estoque_grouped = (
        df_estoque_filtered
        .groupby(['Item', 'Endereço'], as_index=False)['Qtd em Estoque']
        .sum()
    )

    # Create address list per item
    enderecos_estoque = (
        df_estoque_grouped
        .groupby('Item')['Endereço']
        .apply(list)
        .reset_index()
        .rename(columns={'Endereço': 'Endereços A0 (Estoque)'})
    )
    
    return df_estoque_grouped, enderecos_estoque

def process_data(status_file, rastreabilidade_file, estoque_file):
    """Optimized main data processing function with progress tracking."""
    try:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. Process Status file
        status_text.text('Processando arquivo de Status...')
        progress_bar.progress(20)
        
        df_status = read_file(status_file)
        if df_status is None:
            return None
            
        df_status_processed = process_status_data(df_status)
        if df_status_processed is None:
            return None
        
        # 2. Process Rastreabilidade file
        status_text.text('Processando arquivo de Rastreabilidade...')
        progress_bar.progress(40)
        
        df_rastreabilidade = read_file(rastreabilidade_file)
        if df_rastreabilidade is None:
            return None
            
        enderecos_rastreabilidade = process_rastreabilidade_data(df_rastreabilidade)
        if enderecos_rastreabilidade is None:
            return None

        # 3. Process Estoque file
        status_text.text('Processando arquivo de Estoque...')
        progress_bar.progress(60)
        
        df_estoque = read_file(estoque_file)
        if df_estoque is None:
            return None
            
        itens_status = df_status_processed['Item'].unique()
        df_estoque_detalhado, enderecos_estoque = process_estoque_data(df_estoque, itens_status)
        if df_estoque_detalhado is None:
            return None

        # 4. Merge and build final report
        status_text.text('Construindo relatório final...')
        progress_bar.progress(80)
        
        # Optimize merge operations
        df_merged = df_status_processed.merge(enderecos_rastreabilidade, on='Item', how='left')
        df_merged = df_merged.merge(enderecos_estoque, on='Item', how='left')

        # Handle missing lists efficiently
        for col in ['Endereços A0 (Rastreabilidade)', 'Endereços A0 (Estoque)']:
            df_merged[col] = df_merged[col].apply(lambda d: d if isinstance(d, list) else [])

        # Combine address lists efficiently
        df_merged['Endereço A0'] = df_merged.apply(
            lambda row: sorted(set(row['Endereços A0 (Rastreabilidade)'] + row['Endereços A0 (Estoque)'])),
            axis=1
        )

        # 5. Build final report
        status_text.text('Finalizando relatório...')
        progress_bar.progress(90)
        
        # Optimize explode operation
        df_final = (
            df_merged[['Item', 'Descrição', 'Quantidade Não Alocada', 'Endereço A0']]
            .explode('Endereço A0')
            .dropna(subset=['Endereço A0'])
            .reset_index(drop=True)
        )

        # Optimize final merge
        df_final = df_final.merge(
            df_estoque_detalhado,
            left_on=['Item', 'Endereço A0'],
            right_on=['Item', 'Endereço'],
            how='left'
        )

        # Apply quantity logic efficiently
        df_final['Qtd em Estoque'] = df_final['Qtd em Estoque'].fillna(0)
        df_final['Status da Quantidade'] = np.where(
            df_final['Qtd em Estoque'] > 0,
            df_final['Qtd em Estoque'].astype(int).astype(str),
            'VIDA'
        )

        # Final column selection and renaming
        df_final = df_final[[
            'Item',
            'Descrição',
            'Quantidade Não Alocada',
            'Endereço A0',
            'Status da Quantidade'
        ]].rename(columns={
            'Endereço A0': 'Endereço',
            'Status da Quantidade': 'Rastreabilidade / Qnt. Atual'
        })

        # Clean up progress indicators
        progress_bar.progress(100)
        status_text.text('Processamento concluído!')
        
        # Clean up memory
        gc.collect()
        
        return df_final

    except Exception as e:
        st.error(f"Ocorreu um erro durante o processamento: {e}")
        return None

# --- Optimized Utility Functions ---

@st.cache_data
def to_excel(df):
    """Optimized Excel conversion with caching."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl', options={'remove_timezone': True}) as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    return output.getvalue()

def clear_uploads():
    """Optimized callback to clear uploads and cache."""
    st.session_state.clear_count += 1
    if 'final_report' in st.session_state:
        del st.session_state['final_report']
    # Clear caches to free memory
    st.cache_data.clear()

# --- Optimized Interface ---

st.set_page_config(
    page_title="Rastreabilidade de Estoque", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better performance and UX
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stProgress .st-bo {
        background-color: #FF6B6B;
    }
    div[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title('✅ Alanizer Life Stock Versão 1.1.0 - Otimizado - By Ricardo Feitosa')
st.markdown("""
Esta ferramenta integrada e otimizada processa dados de três planilhas para gerar relatórios de rastreabilidade com melhor performance.
""")

# Initialize session state
if 'clear_count' not in st.session_state:
    st.session_state.clear_count = 0

# Optimized sidebar with better UX
with st.sidebar:
    st.header('📤 Upload das Planilhas')
    
    # File uploaders with dynamic keys
    status_file = st.file_uploader(
        "1. Status_da_Ordem", 
        type=['xlsx', 'csv'], 
        key=f"status_uploader_{st.session_state.clear_count}",
        help="Arquivo contendo o status das ordens"
    )
    rastreabilidade_file = st.file_uploader(
        "2. Consulta_Rastreabilidade", 
        type=['xlsx', 'csv'], 
        key=f"rastreabilidade_uploader_{st.session_state.clear_count}",
        help="Arquivo com dados de rastreabilidade"
    )
    estoque_file = st.file_uploader(
        "3. Consulta_de_Estoque", 
        type=['xlsx', 'csv'], 
        key=f"estoque_uploader_{st.session_state.clear_count}",
        help="Arquivo com informações de estoque"
    )

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        gerar_relatorio = st.button('Gerar Relatório', type="primary", use_container_width=True)
    with col2:
        st.button('Limpar', on_click=clear_uploads, use_container_width=True)
    
    # Performance info
    st.markdown("---")
    st.caption("🚀 Versão otimizada com cache e processamento melhorado")

# Main processing logic
if gerar_relatorio:
    if all([status_file, rastreabilidade_file, estoque_file]):
        with st.spinner('Processando dados... Por favor, aguarde.'):
            final_report = process_data(status_file, rastreabilidade_file, estoque_file)
        
        if final_report is not None:
            st.success('✅ Relatório gerado com sucesso!')
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Registros", len(final_report))
            with col2:
                st.metric("Itens Únicos", final_report['Item'].nunique())
            with col3:
                st.metric("Endereços Únicos", final_report['Endereço'].nunique())
            
            # Display data with pagination for large datasets
            if len(final_report) > 1000:
                st.warning("Dataset grande detectado. Mostrando primeiros 1000 registros.")
                st.dataframe(final_report.head(1000), use_container_width=True)
                st.info(f"Total de {len(final_report)} registros. Use o download para ver todos os dados.")
            else:
                st.dataframe(final_report, use_container_width=True)
            
            st.session_state['final_report'] = final_report
        else:
            st.error("❌ Não foi possível gerar o relatório. Verifique os arquivos e tente novamente.")
    else:
        st.warning('⚠️ Por favor, faça o upload das três planilhas para continuar.')

# Optimized download section
if 'final_report' in st.session_state and not st.session_state['final_report'].empty:
    st.header('📥 Download do Relatório')
    report_df = st.session_state['final_report']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Baixar como CSV",
            data=csv,
            file_name='relatorio_rastreabilidade.csv',
            mime='text/csv',
        )
        
    with col2:
        excel_data = to_excel(report_df)
        st.download_button(
            label="📊 Baixar como XLSX",
            data=excel_data,
            file_name='relatorio_rastreabilidade.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    with col3:
        # Memory usage info
        memory_usage = report_df.memory_usage(deep=True).sum() / 1024 / 1024
        st.metric("Uso de Memória", f"{memory_usage:.2f} MB")
