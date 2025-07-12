"""
Configurações da aplicação de Rastreabilidade
"""
import os
from pathlib import Path

# Configurações de arquivo
SUPPORTED_FORMATS = ['csv', 'xlsx', 'xls']
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

# Configurações de colunas obrigatórias
REQUIRED_COLUMNS = {
    'rastreabilidade': ['Item', 'Descrição do Item', 'Endereço Origem', 'Endereço Destino'],
    'status': ['Item', 'Description', 'Quantidade Não Alocada'],
    'estoque': ['Item', 'Descrição', 'Endereço', 'Qtd Atual']
}

# Configurações de processamento
ENDERECO_FILTER_PREFIX = 'A0'
DEFAULT_OUTPUT_NAME = 'Relatorio_Rastreabilidade_Final.xlsx'

# Configurações de logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configurações da interface
APP_TITLE = "Processador de Rastreabilidade"
APP_ICON = "📊"
PAGE_LAYOUT = "wide"

# Configurações de pasta temporária
TEMP_DIR = Path('temp')
TEMP_DIR.mkdir(exist_ok=True)

# Configurações de validação
VALIDATION_RULES = {
    'max_rows': 1000000,  # Máximo de linhas por arquivo
    'min_rows': 1,        # Mínimo de linhas por arquivo
    'required_encoding': 'utf-8'
}

# Mensagens de erro
ERROR_MESSAGES = {
    'file_not_found': 'Arquivo não encontrado: {}',
    'invalid_format': 'Formato de arquivo não suportado: {}',
    'missing_columns': 'Colunas obrigatórias não encontradas: {}',
    'processing_error': 'Erro durante o processamento: {}',
    'empty_file': 'Arquivo vazio ou sem dados válidos',
    'file_too_large': 'Arquivo muito grande (máximo {:.1f}MB)',
}

# Mensagens de sucesso
SUCCESS_MESSAGES = {
    'data_loaded': 'Dados carregados com sucesso',
    'processing_complete': 'Processamento concluído com sucesso',
    'report_generated': 'Relatório gerado: {}',
}

# Configurações de status
STATUS_VIDA = 'VIDA'
STATUS_MAPPING = {
    'null_not_allocated': STATUS_VIDA,
    'empty_quantity': ''
}