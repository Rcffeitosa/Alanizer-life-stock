#!/usr/bin/env python3
"""
Testes básicos para a aplicação de Rastreabilidade
"""
import unittest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Importar módulos da aplicação
from app import RastreabilidadeProcessor
import utils
import config

class TestRastreabilidadeProcessor(unittest.TestCase):
    """Testes para a classe RastreabilidadeProcessor"""
    
    def setUp(self):
        """Configurar dados de teste"""
        self.processor = RastreabilidadeProcessor()
        
        # Criar dados de teste
        self.df_rastreabilidade_test = pd.DataFrame({
            'Item': ['ITEM001', 'ITEM002', 'ITEM003'],
            'Descrição do Item': ['Produto A', 'Produto B', 'Produto C'],
            'Endereço Origem': ['A0001', 'A0002', 'B0001'],
            'Endereço Destino': ['A0003', 'A0004', 'A0005']
        })
        
        self.df_status_test = pd.DataFrame({
            'Item': ['ITEM001', 'ITEM002'],
            'Description': ['Desc A', 'Desc B'],
            'Quantidade Não Alocada': [10, None]
        })
        
        self.df_estoque_test = pd.DataFrame({
            'Item': ['ITEM001', 'ITEM002', 'ITEM003'],
            'Descrição': ['Produto A', 'Produto B', 'Produto C'],
            'Endereço': ['A0001A0003', 'A0002A0004', 'A0005'],
            'Qtd Atual': [5, 0, 15]
        })
    
    def test_init(self):
        """Testar inicialização da classe"""
        self.assertIsNone(self.processor.df_rastreabilidade)
        self.assertIsNone(self.processor.df_status)
        self.assertIsNone(self.processor.df_estoque)
        self.assertIsNone(self.processor.df_resultado)
    
    def test_process_rastreabilidade(self):
        """Testar processamento de dados de rastreabilidade"""
        self.processor.df_rastreabilidade = self.df_rastreabilidade_test.copy()
        
        result = self.processor.process_rastreabilidade()
        self.assertTrue(result)
        
        # Verificar se a coluna 'Endereço' foi criada
        self.assertIn('Endereço', self.processor.df_rastreabilidade.columns)
        
        # Verificar se a coluna 'Chave1' foi criada
        self.assertIn('Chave1', self.processor.df_rastreabilidade.columns)
        
        # Verificar se duplicatas foram removidas
        self.assertEqual(len(self.processor.df_rastreabilidade), 
                        len(self.processor.df_rastreabilidade['Chave1'].unique()))
    
    def test_get_summary_stats(self):
        """Testar geração de estatísticas"""
        # Configurar dados de teste
        self.processor.df_resultado = pd.DataFrame({
            'Item': ['ITEM001', 'ITEM002'],
            'Endereço': ['A0001', 'A0002'],
            'Status': ['VIDA', ''],
            'Qnt endereço': [5, '']
        })
        
        stats = self.processor.get_summary_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_items', stats)
        self.assertIn('items_with_vida_status', stats)
        self.assertIn('items_with_quantity', stats)
        self.assertIn('unique_addresses', stats)
        
        self.assertEqual(stats['total_items'], 2)
        self.assertEqual(stats['items_with_vida_status'], 1)

class TestUtils(unittest.TestCase):
    """Testes para funções utilitárias"""
    
    def test_validate_file_format(self):
        """Testar validação de formato de arquivo"""
        # Formatos válidos
        self.assertTrue(utils.validate_file_format('test.csv'))
        self.assertTrue(utils.validate_file_format('test.xlsx'))
        self.assertTrue(utils.validate_file_format('test.xls'))
        
        # Formatos inválidos
        self.assertFalse(utils.validate_file_format('test.txt'))
        self.assertFalse(utils.validate_file_format('test.pdf'))
        self.assertFalse(utils.validate_file_format('test.doc'))
    
    def test_validate_required_columns(self):
        """Testar validação de colunas obrigatórias"""
        df = pd.DataFrame({
            'Item': [1, 2, 3],
            'Descrição': ['A', 'B', 'C']
        })
        
        required_columns = ['Item', 'Descrição']
        missing = utils.validate_required_columns(df, required_columns)
        self.assertEqual(len(missing), 0)
        
        required_columns = ['Item', 'Descrição', 'Quantidade']
        missing = utils.validate_required_columns(df, required_columns)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0], 'Quantidade')
    
    def test_format_number(self):
        """Testar formatação de números"""
        self.assertEqual(utils.format_number(10), '10')
        self.assertEqual(utils.format_number(10.0), '10')
        self.assertEqual(utils.format_number(10.5), '10.50')
        self.assertEqual(utils.format_number(''), '')
        self.assertEqual(utils.format_number(None), '')
    
    def test_generate_unique_filename(self):
        """Testar geração de nome único"""
        filename1 = utils.generate_unique_filename('test')
        filename2 = utils.generate_unique_filename('test')
        
        self.assertNotEqual(filename1, filename2)
        self.assertTrue(filename1.startswith('test_'))
        self.assertTrue(filename1.endswith('.xlsx'))
    
    def test_get_dataframe_summary(self):
        """Testar resumo de DataFrame"""
        df = pd.DataFrame({
            'A': [1, 2, 3, 1],
            'B': [4, 5, None, 4],
            'C': ['x', 'y', 'z', 'x']
        })
        
        summary = utils.get_dataframe_summary(df)
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['total_rows'], 4)
        self.assertEqual(summary['total_columns'], 3)
        self.assertEqual(summary['null_values'], 1)
        self.assertEqual(summary['duplicate_rows'], 1)

class TestConfig(unittest.TestCase):
    """Testes para configurações"""
    
    def test_config_constants(self):
        """Testar constantes de configuração"""
        self.assertIsInstance(config.SUPPORTED_FORMATS, list)
        self.assertIsInstance(config.REQUIRED_COLUMNS, dict)
        self.assertIsInstance(config.ERROR_MESSAGES, dict)
        self.assertIsInstance(config.SUCCESS_MESSAGES, dict)
        
        # Verificar se formatos suportados incluem CSV e Excel
        self.assertIn('csv', config.SUPPORTED_FORMATS)
        self.assertIn('xlsx', config.SUPPORTED_FORMATS)
        
        # Verificar se colunas obrigatórias estão definidas
        self.assertIn('rastreabilidade', config.REQUIRED_COLUMNS)
        self.assertIn('status', config.REQUIRED_COLUMNS)
        self.assertIn('estoque', config.REQUIRED_COLUMNS)

class TestIntegration(unittest.TestCase):
    """Testes de integração"""
    
    def test_full_workflow(self):
        """Testar fluxo completo de processamento"""
        # Criar arquivos temporários
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Criar dados de teste
            df_rastreabilidade = pd.DataFrame({
                'Item': ['ITEM001', 'ITEM002'],
                'Descrição do Item': ['Produto A', 'Produto B'],
                'Endereço Origem': ['A0001', 'A0002'],
                'Endereço Destino': ['A0003', 'A0004']
            })
            
            df_status = pd.DataFrame({
                'Item': ['ITEM001', 'ITEM002'],
                'Description': ['Desc A', 'Desc B'],
                'Quantidade Não Alocada': [10, None]
            })
            
            df_estoque = pd.DataFrame({
                'Item': ['ITEM001', 'ITEM002'],
                'Descrição': ['Produto A', 'Produto B'],
                'Endereço': ['A0001A0003', 'A0002A0004'],
                'Qtd Atual': [5, 0]
            })
            
            # Salvar arquivos temporários
            rastreabilidade_file = temp_path / 'rastreabilidade.csv'
            status_file = temp_path / 'status.xlsx'
            estoque_file = temp_path / 'estoque.xlsx'
            
            df_rastreabilidade.to_csv(rastreabilidade_file, index=False)
            df_status.to_excel(status_file, index=False)
            df_estoque.to_excel(estoque_file, index=False)
            
            # Testar processamento
            processor = RastreabilidadeProcessor()
            
            # Carregar dados
            success = processor.load_data(rastreabilidade_file, status_file, estoque_file)
            self.assertTrue(success)
            
            # Processar dados
            self.assertTrue(processor.process_rastreabilidade())
            self.assertTrue(processor.merge_with_status())
            self.assertTrue(processor.process_estoque())
            self.assertTrue(processor.apply_business_rules())
            
            # Gerar relatório
            output_file = temp_path / 'output.xlsx'
            df_final = processor.generate_final_report(str(output_file))
            
            self.assertIsInstance(df_final, pd.DataFrame)
            self.assertTrue(output_file.exists())
            
            # Verificar estatísticas
            stats = processor.get_summary_stats()
            self.assertIsInstance(stats, dict)
            self.assertGreaterEqual(stats['total_items'], 0)

def run_tests():
    """Executar todos os testes"""
    # Configurar suite de testes
    test_suite = unittest.TestSuite()
    
    # Adicionar testes
    test_suite.addTest(unittest.makeSuite(TestRastreabilidadeProcessor))
    test_suite.addTest(unittest.makeSuite(TestUtils))
    test_suite.addTest(unittest.makeSuite(TestConfig))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("🧪 Executando testes da aplicação...")
    success = run_tests()
    
    if success:
        print("✅ Todos os testes passaram!")
        exit(0)
    else:
        print("❌ Alguns testes falharam!")
        exit(1)