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

def process_data(status_file, rastreabilidade_file, estoque_file):
    """Função principal para processar os três arquivos Excel e gerar o relatório final."""
    try:
        # 1. Processar o arquivo de Status da Ordem
        df_status = read_file(status_file)
        if df_status is None:
            return None # A mensagem de erro já foi exibida na função read_file



        # --- Validação das Colunas Essenciais ---
        # Agora, verifica se as colunas padronizadas existem
        required_cols = ['Item', 'Descrição', 'Quantidade Não Alocada']
        missing_cols = [col for col in required_cols if col not in df_status.columns]

        if missing_cols:
            st.error(f"Erro ao processar o arquivo de status. Coluna(s) essencial(is) não encontrada(s): {missing_cols}.")
            st.info(f"Colunas disponíveis no arquivo (após tentativa de adaptação): {list(df_status.columns)}")
            return None

        df_status_processed = df_status[required_cols].copy()

        # Filtrar para remover itens com 'Quantidade Não Alocada' igual a 0
        df_status_processed = df_status_processed[df_status_processed['Quantidade Não Alocada'] != 0].copy()

        # 2. Processar Consulta_Rastreabilidade.xlsx
        df_rastreabilidade = read_file(rastreabilidade_file)
        if df_rastreabilidade is None:
            return None

        # Como read_file já padronizou, podemos decidir a estratégia com segurança
        if 'Endereço' in df_rastreabilidade.columns:
            # Estratégia 1: Usar a coluna 'Endereço' diretamente
            df_melted = df_rastreabilidade[['Item', 'Endereço']].copy()
        elif 'Endereço Origem' in df_rastreabilidade.columns and 'Endereço Destino' in df_rastreabilidade.columns:
            # Estratégia 2: Combinar 'Origem' e 'Destino'
            df_melted = df_rastreabilidade.melt(
                id_vars=['Item'],
                value_vars=['Endereço Origem', 'Endereço Destino'],
                value_name='Endereço'
            )
        else:
            st.error("Erro Crítico no arquivo de Rastreabilidade: Nenhuma coluna de endereço válida encontrada.")
            st.info("O arquivo deve conter ou uma coluna 'Endereço', ou as colunas 'Endereço Origem' e 'Endereço Destino'.")
            st.info(f"Colunas encontradas (já padronizadas): {list(df_rastreabilidade.columns)}")
            return None

        # Limpeza e filtragem otimizada
        df_filtered = df_melted.dropna(subset=['Endereço'])
        df_filtered = df_filtered[df_filtered['Endereço'].astype(str).str.startswith('A0')].copy()
        df_filtered.drop_duplicates(subset=['Item', 'Endereço'], inplace=True)

        # Agrupa por Item e cria a lista de endereços da rastreabilidade
        enderecos_rastreabilidade = (
            df_filtered.sort_values('Endereço')
            .groupby('Item', as_index=False)
            .agg(Enderecos_Rastreabilidade=('Endereço', list))
        )
        enderecos_rastreabilidade.rename(
            columns={'Enderecos_Rastreabilidade': 'Endereços A0 (Rastreabilidade)'},
            inplace=True
        )

        # 3. Processar Consulta_de_Estoque.xlsx, mantendo a granularidade
        df_estoque = read_file(estoque_file)
        if df_estoque is None:
            return None

        # --- Validação da coluna de Endereço no Estoque ---
        if 'Endereço' not in df_estoque.columns:
            st.error("Erro Crítico no arquivo de Estoque: A coluna 'Endereço' não foi encontrada.")
            st.info("O aplicativo tentou padronizar os nomes das colunas, mas não obteve sucesso.")
            st.info(f"Colunas encontradas no arquivo (após tentativa de limpeza): {list(df_estoque.columns)}")
            return None



        # Renomeia 'Qtd Atual' para 'Qtd em Estoque' para clareza
        if 'Qtd Atual' in df_estoque.columns:
            df_estoque.rename(columns={'Qtd Atual': 'Qtd em Estoque'}, inplace=True)

        itens_status = df_status_processed['Item'].unique()
        df_estoque_detalhado = df_estoque[
            df_estoque['Item'].isin(itens_status) &
            df_estoque['Endereço'].astype(str).str.startswith('A0', na=False)
        ].copy()
        
        # Garantir que a coluna de quantidade é numérica
        df_estoque_detalhado['Qtd em Estoque'] = pd.to_numeric(df_estoque_detalhado['Qtd em Estoque'], errors='coerce').fillna(0)

        # Agrupar para somar quantidades para o mesmo Item-Endereço
        df_estoque_detalhado = df_estoque_detalhado.groupby(['Item', 'Endereço'], as_index=False)['Qtd em Estoque'].sum()

        # 4. Unificar dados e construir o relatório
        df_merged = pd.merge(df_status_processed, enderecos_rastreabilidade, on='Item', how='left')

        # Obter a lista de endereços únicos do estoque para cada item
        enderecos_estoque = df_estoque_detalhado.groupby('Item')['Endereço'].apply(list).reset_index()
        enderecos_estoque.rename(columns={'Endereço': 'Endereços A0 (Estoque)'}, inplace=True)
        df_merged = pd.merge(df_merged, enderecos_estoque, on='Item', how='left')

        # Garantir que as colunas de lista existam e não sejam nulas
        for col in ['Endereços A0 (Rastreabilidade)', 'Endereços A0 (Estoque)']:
            df_merged[col] = df_merged[col].apply(lambda d: d if isinstance(d, list) else [])

        # Juntar as duas listas de endereços em uma única, sem duplicatas
        df_merged['Endereço A0'] = df_merged.apply(
            lambda row: sorted(list(set(row['Endereços A0 (Rastreabilidade)'] + row['Endereços A0 (Estoque)']))),
            axis=1
        )

        # 5. Estruturar o relatório final
        # Expandir para ter uma linha por endereço
        df_final = df_merged[['Item', 'Descrição', 'Quantidade Não Alocada', 'Endereço A0']].explode('Endereço A0').reset_index(drop=True)

        # Remover linhas onde 'Endereço A0' ficou nulo (para itens que não tinham nenhum endereço)
        df_final.dropna(subset=['Endereço A0'], inplace=True)

        # Juntar com as quantidades detalhadas do estoque
        df_final = pd.merge(
            df_final,
            df_estoque_detalhado,
            left_on=['Item', 'Endereço A0'],
            right_on=['Item', 'Endereço'],
            how='left'
        )

        # Aplicar a lógica do 'Status da Quantidade'
        df_final['Qtd em Estoque'] = df_final['Qtd em Estoque'].fillna(0)
        df_final['Status da Quantidade'] = np.where(
            df_final['Qtd em Estoque'] > 0,
            df_final['Qtd em Estoque'].astype(int).astype(str),
            'VIDA'
        )

        # Selecionar e reordenar as colunas finais
        df_final = df_final[[
            'Item',
            'Descrição',
            'Quantidade Não Alocada',
            'Endereço A0',
            'Status da Quantidade'
        ]]

        # Renomear colunas para a exibição final, conforme solicitado
        df_final.rename(columns={
            'Endereço A0': 'Endereço',
            'Status da Quantidade': 'Rastreabilidade / Qnt. Atual'
        }, inplace=True)

        return df_final

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
