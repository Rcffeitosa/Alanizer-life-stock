import pandas as pd
import streamlit as st
import logging
from pathlib import Path
import plotly.express as px
from datetime import datetime
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RastreabilidadeProcessor:
    """Classe para processar dados de rastreabilidade"""
    
    def __init__(self):
        self.df_rastreabilidade = None
        self.df_status = None
        self.df_estoque = None
        self.df_resultado = None
        
    def load_data(self, rastreabilidade_file, status_ordem_file, consulta_estoque_file):
        """Carrega os dados dos arquivos fornecidos"""
        try:
            # Carregar dados com tratamento de erro
            if rastreabilidade_file.suffix == '.csv':
                self.df_rastreabilidade = pd.read_csv(rastreabilidade_file)
            else:
                self.df_rastreabilidade = pd.read_excel(rastreabilidade_file)
                
            self.df_status = pd.read_excel(status_ordem_file)
            self.df_estoque = pd.read_excel(consulta_estoque_file)
            
            logger.info("Dados carregados com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            return False
    
    def process_rastreabilidade(self):
        """Processa os dados de rastreabilidade"""
        # Seleção e renomeação de colunas
        required_columns = ['Item', 'Descrição do Item', 'Endereço Origem', 'Endereço Destino']
        
        # Verificar se as colunas existem
        missing_columns = [col for col in required_columns if col not in self.df_rastreabilidade.columns]
        if missing_columns:
            logger.error(f"Colunas faltando em rastreabilidade: {missing_columns}")
            return False
            
        self.df_rastreabilidade = self.df_rastreabilidade[required_columns].copy()
        
        # Unir endereços
        self.df_rastreabilidade['Endereço'] = (
            self.df_rastreabilidade['Endereço Origem'].fillna('') + 
            self.df_rastreabilidade['Endereço Destino'].fillna('')
        )
        
        # Criar chave1 e remover duplicados
        self.df_rastreabilidade['Chave1'] = (
            self.df_rastreabilidade['Item'].astype(str) + 
            self.df_rastreabilidade['Endereço']
        )
        self.df_rastreabilidade = self.df_rastreabilidade.drop_duplicates(
            subset=['Chave1']
        ).reset_index(drop=True)
        
        return True
    
    def merge_with_status(self):
        """Faz o merge com dados de status"""
        required_status_columns = ['Item', 'Description', 'Quantidade Não Alocada']
        
        # Verificar se as colunas existem
        missing_columns = [col for col in required_status_columns if col not in self.df_status.columns]
        if missing_columns:
            logger.error(f"Colunas faltando em status: {missing_columns}")
            return False
            
        df_status_filtered = self.df_status[required_status_columns].copy()
        
        self.df_rastreabilidade = self.df_rastreabilidade.merge(
            df_status_filtered,
            how='left',
            on='Item'
        )
        
        self.df_rastreabilidade = self.df_rastreabilidade.rename(columns={
            'Description': 'Descrição_Status',
            'Quantidade Não Alocada': 'Não Alocado'
        })
        
        return True
    
    def process_estoque(self):
        """Processa dados de estoque"""
        required_estoque_columns = ['Item', 'Descrição', 'Endereço', 'Qtd Atual']
        
        # Verificar se as colunas existem
        missing_columns = [col for col in required_estoque_columns if col not in self.df_estoque.columns]
        if missing_columns:
            logger.error(f"Colunas faltando em estoque: {missing_columns}")
            return False
            
        self.df_estoque['Endereço'] = self.df_estoque['Endereço'].fillna('')
        self.df_estoque['Chave2'] = (
            self.df_estoque['Item'].astype(str) + 
            self.df_estoque['Endereço']
        )
        self.df_estoque = self.df_estoque.drop_duplicates(subset=['Chave2'])
        
        # Fazer o PROCV para quantidade endereço
        estoque_lookup = self.df_estoque.set_index('Chave2')[['Item', 'Descrição', 'Qtd Atual']]
        
        def buscar_qnt_endereco(chave):
            try:
                return estoque_lookup.loc[chave, 'Qtd Atual']
            except KeyError:
                return None
        
        self.df_rastreabilidade['Qnt endereço'] = self.df_rastreabilidade['Chave1'].apply(buscar_qnt_endereco)
        
        return True
    
    def apply_business_rules(self):
        """Aplica regras de negócio"""
        # STATUS: se "Não Alocado" estiver nulo, colocar VIDA
        self.df_rastreabilidade['Status'] = self.df_rastreabilidade['Não Alocado'].apply(
            lambda x: 'VIDA' if pd.isna(x) else ''
        )
        
        # Qnt endereço: se nulo, deixar vazio
        self.df_rastreabilidade['Qnt endereço'] = self.df_rastreabilidade['Qnt endereço'].fillna('')
        
        # Filtrar somente endereço com 'A0'
        self.df_resultado = self.df_rastreabilidade[
            self.df_rastreabilidade['Endereço'].str.startswith('A0', na=False)
        ].copy()
        
        return True
    
    def generate_final_report(self, output_path='Relatorio_Rastreabilidade_Final.xlsx'):
        """Gera o relatório final"""
        final_columns = [
            'Item',
            'Descrição do Item',
            'Endereço',
            'Chave1',
            'Não Alocado',
            'Qnt endereço',
            'Status'
        ]
        
        df_resultado_final = self.df_resultado[final_columns]
        
        # Salvar resultado
        df_resultado_final.to_excel(output_path, index=False)
        logger.info(f"Relatório gerado com sucesso: {output_path}")
        
        return df_resultado_final
    
    def get_summary_stats(self):
        """Retorna estatísticas resumidas"""
        if self.df_resultado is None:
            return None
            
        stats = {
            'total_items': len(self.df_resultado),
            'items_with_vida_status': len(self.df_resultado[self.df_resultado['Status'] == 'VIDA']),
            'items_with_quantity': len(self.df_resultado[self.df_resultado['Qnt endereço'] != '']),
            'unique_addresses': self.df_resultado['Endereço'].nunique()
        }
        
        return stats

def main():
    """Função principal da aplicação Streamlit"""
    st.set_page_config(
        page_title="Processador de Rastreabilidade",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Processador de Rastreabilidade")
    st.markdown("---")
    
    # Sidebar para upload de arquivos
    st.sidebar.header("Upload de Arquivos")
    
    rastreabilidade_file = st.sidebar.file_uploader(
        "Arquivo de Rastreabilidade",
        type=['csv', 'xlsx'],
        help="Arquivo CSV ou Excel com dados de rastreabilidade"
    )
    
    status_ordem_file = st.sidebar.file_uploader(
        "Arquivo de Status da Ordem",
        type=['xlsx'],
        help="Arquivo Excel com dados de status da ordem"
    )
    
    consulta_estoque_file = st.sidebar.file_uploader(
        "Arquivo de Consulta de Estoque",
        type=['xlsx'],
        help="Arquivo Excel com dados de consulta de estoque"
    )
    
    if all([rastreabilidade_file, status_ordem_file, consulta_estoque_file]):
        # Inicializar processador
        processor = RastreabilidadeProcessor()
        
        # Salvar arquivos temporariamente
        temp_files = []
        for file, name in [(rastreabilidade_file, "rastreabilidade"), 
                          (status_ordem_file, "status"), 
                          (consulta_estoque_file, "estoque")]:
            temp_path = Path(f"temp_{name}.{file.name.split('.')[-1]}")
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            temp_files.append(temp_path)
        
        try:
            # Processar dados
            with st.spinner("Processando dados..."):
                if processor.load_data(temp_files[0], temp_files[1], temp_files[2]):
                    if (processor.process_rastreabilidade() and
                        processor.merge_with_status() and
                        processor.process_estoque() and
                        processor.apply_business_rules()):
                        
                        # Gerar relatório
                        output_path = f"Relatorio_Rastreabilidade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        df_final = processor.generate_final_report(output_path)
                        
                        # Mostrar estatísticas
                        st.success("✅ Processamento concluído com sucesso!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📈 Estatísticas")
                            stats = processor.get_summary_stats()
                            if stats:
                                st.metric("Total de Items", stats['total_items'])
                                st.metric("Items com Status VIDA", stats['items_with_vida_status'])
                                st.metric("Items com Quantidade", stats['items_with_quantity'])
                                st.metric("Endereços Únicos", stats['unique_addresses'])
                        
                        with col2:
                            st.subheader("📊 Distribuição por Status")
                            status_counts = df_final['Status'].value_counts()
                            fig = px.pie(
                                values=status_counts.values,
                                names=status_counts.index,
                                title="Distribuição de Status"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Mostrar preview dos dados
                        st.subheader("👀 Preview dos Dados")
                        st.dataframe(df_final.head(10))
                        
                        # Download do arquivo
                        with open(output_path, "rb") as file:
                            st.download_button(
                                label="📥 Download do Relatório",
                                data=file.read(),
                                file_name=output_path,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.error("❌ Erro durante o processamento dos dados")
                else:
                    st.error("❌ Erro ao carregar os dados")
        
        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")
        
        finally:
            # Limpar arquivos temporários
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
    
    else:
        st.info("📁 Por favor, faça o upload dos três arquivos necessários na barra lateral.")
        
        # Mostrar informações sobre os arquivos esperados
        st.subheader("📋 Arquivos Necessários")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            **Arquivo de Rastreabilidade**
            - Formato: CSV ou Excel
            - Colunas necessárias:
              - Item
              - Descrição do Item
              - Endereço Origem
              - Endereço Destino
            """)
        
        with col2:
            st.info("""
            **Arquivo de Status da Ordem**
            - Formato: Excel
            - Colunas necessárias:
              - Item
              - Description
              - Quantidade Não Alocada
            """)
        
        with col3:
            st.info("""
            **Arquivo de Consulta de Estoque**
            - Formato: Excel
            - Colunas necessárias:
              - Item
              - Descrição
              - Endereço
              - Qtd Atual
            """)

if __name__ == "__main__":
    main()
