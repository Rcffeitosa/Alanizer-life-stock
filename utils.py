"""
Módulo de utilitários para a aplicação de Rastreabilidade
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Union, List, Dict, Optional
import streamlit as st
from datetime import datetime
import config

logger = logging.getLogger(__name__)

def validate_file_format(file_path: Union[str, Path]) -> bool:
    """
    Valida se o formato do arquivo é suportado
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        bool: True se o formato é suportado
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    return file_path.suffix.lower().lstrip('.') in config.SUPPORTED_FORMATS

def validate_file_size(file_path: Union[str, Path]) -> bool:
    """
    Valida se o tamanho do arquivo está dentro do limite
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        bool: True se o tamanho está dentro do limite
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    return file_path.stat().st_size <= config.MAX_FILE_SIZE

def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Valida se as colunas obrigatórias existem no DataFrame
    
    Args:
        df: DataFrame a ser validado
        required_columns: Lista de colunas obrigatórias
        
    Returns:
        List[str]: Lista de colunas faltando
    """
    return [col for col in required_columns if col not in df.columns]

def load_file(file_path: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    Carrega um arquivo CSV ou Excel
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        pd.DataFrame ou None: DataFrame carregado ou None em caso de erro
    """
    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(config.ERROR_MESSAGES['file_not_found'].format(file_path))
            return None
        
        if not validate_file_format(file_path):
            logger.error(config.ERROR_MESSAGES['invalid_format'].format(file_path.suffix))
            return None
        
        if not validate_file_size(file_path):
            logger.error(config.ERROR_MESSAGES['file_too_large'].format(config.MAX_FILE_SIZE / (1024*1024)))
            return None
        
        # Carregar o arquivo
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_excel(file_path)
        
        # Validar se não está vazio
        if df.empty:
            logger.error(config.ERROR_MESSAGES['empty_file'])
            return None
        
        # Validar número de linhas
        if len(df) > config.VALIDATION_RULES['max_rows']:
            logger.warning(f"Arquivo muito grande ({len(df)} linhas). Considere dividir em arquivos menores.")
        
        logger.info(f"Arquivo carregado com sucesso: {file_path.name} ({len(df)} linhas)")
        return df
        
    except Exception as e:
        logger.error(config.ERROR_MESSAGES['processing_error'].format(str(e)))
        return None

def clean_string_column(series: pd.Series) -> pd.Series:
    """
    Limpa uma coluna de strings removendo espaços e padronizando
    
    Args:
        series: Série pandas para limpeza
        
    Returns:
        pd.Series: Série limpa
    """
    return series.astype(str).str.strip().str.upper()

def generate_unique_filename(base_name: str, extension: str = '.xlsx') -> str:
    """
    Gera um nome único para o arquivo usando timestamp
    
    Args:
        base_name: Nome base do arquivo
        extension: Extensão do arquivo
        
    Returns:
        str: Nome único do arquivo
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}{extension}"

def format_number(value: Union[int, float, str]) -> str:
    """
    Formata números para exibição
    
    Args:
        value: Valor a ser formatado
        
    Returns:
        str: Valor formatado
    """
    try:
        if pd.isna(value) or value == '':
            return ''
        
        num_value = float(value)
        
        if num_value == int(num_value):
            return str(int(num_value))
        else:
            return f"{num_value:.2f}"
            
    except (ValueError, TypeError):
        return str(value)

def create_download_link(df: pd.DataFrame, filename: str) -> bytes:
    """
    Cria um link de download para o DataFrame
    
    Args:
        df: DataFrame a ser baixado
        filename: Nome do arquivo
        
    Returns:
        bytes: Dados do arquivo Excel
    """
    import io
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    
    return output.getvalue()

def log_dataframe_info(df: pd.DataFrame, name: str):
    """
    Registra informações sobre o DataFrame no log
    
    Args:
        df: DataFrame
        name: Nome do DataFrame
    """
    logger.info(f"{name} - Forma: {df.shape}")
    logger.info(f"{name} - Colunas: {list(df.columns)}")
    logger.info(f"{name} - Tipos: {df.dtypes.to_dict()}")

def display_error_message(message: str, details: Optional[str] = None):
    """
    Exibe mensagem de erro no Streamlit
    
    Args:
        message: Mensagem principal
        details: Detalhes adicionais (opcional)
    """
    st.error(f"❌ {message}")
    if details:
        st.error(f"Detalhes: {details}")

def display_success_message(message: str):
    """
    Exibe mensagem de sucesso no Streamlit
    
    Args:
        message: Mensagem de sucesso
    """
    st.success(f"✅ {message}")

def display_info_message(message: str):
    """
    Exibe mensagem informativa no Streamlit
    
    Args:
        message: Mensagem informativa
    """
    st.info(f"ℹ️ {message}")

def display_warning_message(message: str):
    """
    Exibe mensagem de aviso no Streamlit
    
    Args:
        message: Mensagem de aviso
    """
    st.warning(f"⚠️ {message}")

def save_uploaded_file(uploaded_file, temp_dir: Path = None) -> Path:
    """
    Salva um arquivo carregado no Streamlit em um diretório temporário
    
    Args:
        uploaded_file: Arquivo carregado do Streamlit
        temp_dir: Diretório temporário (opcional)
        
    Returns:
        Path: Caminho do arquivo salvo
    """
    if temp_dir is None:
        temp_dir = config.TEMP_DIR
    
    temp_dir.mkdir(exist_ok=True)
    
    # Criar nome único para o arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_extension = uploaded_file.name.split('.')[-1]
    temp_filename = f"temp_{timestamp}.{file_extension}"
    temp_path = temp_dir / temp_filename
    
    # Salvar o arquivo
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return temp_path

def cleanup_temp_files(temp_paths: List[Path]):
    """
    Remove arquivos temporários
    
    Args:
        temp_paths: Lista de caminhos dos arquivos temporários
    """
    for temp_path in temp_paths:
        try:
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"Arquivo temporário removido: {temp_path}")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário {temp_path}: {str(e)}")

def get_dataframe_summary(df: pd.DataFrame) -> Dict:
    """
    Obtém resumo estatístico do DataFrame
    
    Args:
        df: DataFrame
        
    Returns:
        Dict: Dicionário com estatísticas
    """
    return {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'memory_usage': df.memory_usage(deep=True).sum(),
        'null_values': df.isnull().sum().sum(),
        'duplicate_rows': df.duplicated().sum()
    }