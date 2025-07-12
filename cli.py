#!/usr/bin/env python3
"""
Interface de linha de comando para o processador de rastreabilidade
"""
import argparse
import logging
from pathlib import Path
import sys
from datetime import datetime

# Importar módulos locais
from app import RastreabilidadeProcessor
import config
import utils

def setup_logging():
    """Configura o sistema de logging"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(f'rastreabilidade_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Função principal da interface de linha de comando"""
    parser = argparse.ArgumentParser(
        description='Processador de Rastreabilidade - Interface de Linha de Comando'
    )
    
    # Argumentos obrigatórios
    parser.add_argument(
        '-r', '--rastreabilidade',
        required=True,
        help='Arquivo de rastreabilidade (CSV ou Excel)'
    )
    
    parser.add_argument(
        '-s', '--status',
        required=True,
        help='Arquivo de status da ordem (Excel)'
    )
    
    parser.add_argument(
        '-e', '--estoque',
        required=True,
        help='Arquivo de consulta de estoque (Excel)'
    )
    
    # Argumentos opcionais
    parser.add_argument(
        '-o', '--output',
        default=config.DEFAULT_OUTPUT_NAME,
        help=f'Nome do arquivo de saída (padrão: {config.DEFAULT_OUTPUT_NAME})'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nível de log (padrão: INFO)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verboso'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Apenas validar arquivos sem processar'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    config.LOG_LEVEL = args.log_level
    setup_logging()
    
    logger = logging.getLogger(__name__)
    
    try:
        # Converter caminhos para objetos Path
        rastreabilidade_path = Path(args.rastreabilidade)
        status_path = Path(args.status)
        estoque_path = Path(args.estoque)
        output_path = Path(args.output)
        
        # Validar se os arquivos existem
        for file_path, name in [(rastreabilidade_path, 'rastreabilidade'),
                               (status_path, 'status'),
                               (estoque_path, 'estoque')]:
            if not file_path.exists():
                logger.error(f"Arquivo não encontrado: {file_path}")
                sys.exit(1)
            
            if not utils.validate_file_format(file_path):
                logger.error(f"Formato não suportado para {name}: {file_path.suffix}")
                sys.exit(1)
            
            if not utils.validate_file_size(file_path):
                logger.error(f"Arquivo muito grande: {file_path}")
                sys.exit(1)
        
        logger.info("Validação inicial dos arquivos concluída")
        
        if args.validate_only:
            logger.info("Modo de validação apenas. Saindo...")
            sys.exit(0)
        
        # Inicializar o processador
        processor = RastreabilidadeProcessor()
        
        # Processar os dados
        logger.info("Iniciando processamento dos dados...")
        
        if not processor.load_data(rastreabilidade_path, status_path, estoque_path):
            logger.error("Erro ao carregar dados")
            sys.exit(1)
        
        if not processor.process_rastreabilidade():
            logger.error("Erro ao processar dados de rastreabilidade")
            sys.exit(1)
        
        if not processor.merge_with_status():
            logger.error("Erro ao fazer merge com dados de status")
            sys.exit(1)
        
        if not processor.process_estoque():
            logger.error("Erro ao processar dados de estoque")
            sys.exit(1)
        
        if not processor.apply_business_rules():
            logger.error("Erro ao aplicar regras de negócio")
            sys.exit(1)
        
        # Gerar relatório final
        logger.info("Gerando relatório final...")
        df_final = processor.generate_final_report(str(output_path))
        
        if df_final is not None:
            # Exibir estatísticas
            stats = processor.get_summary_stats()
            if stats:
                logger.info("=== ESTATÍSTICAS DO RELATÓRIO ===")
                logger.info(f"Total de items: {stats['total_items']}")
                logger.info(f"Items com status VIDA: {stats['items_with_vida_status']}")
                logger.info(f"Items com quantidade: {stats['items_with_quantity']}")
                logger.info(f"Endereços únicos: {stats['unique_addresses']}")
            
            if args.verbose:
                logger.info("=== PREVIEW DOS DADOS ===")
                logger.info(f"\n{df_final.head(10).to_string()}")
            
            logger.info(f"Relatório gerado com sucesso: {output_path}")
            logger.info("Processamento concluído!")
            
        else:
            logger.error("Erro ao gerar relatório final")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Processamento interrompido pelo usuário")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        if args.verbose:
            logger.exception("Detalhes do erro:")
        sys.exit(1)

if __name__ == '__main__':
    main()