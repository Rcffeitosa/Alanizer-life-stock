#!/usr/bin/env python3
"""
Script para executar a aplicação de Rastreabilidade
"""
import sys
import subprocess
import os
from pathlib import Path
import argparse

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import pandas
        import streamlit
        import openpyxl
        import plotly
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        return False

def run_web_app():
    """Executa a aplicação web"""
    print("🚀 Iniciando aplicação web...")
    print("📍 A aplicação será aberta em: http://localhost:8501")
    print("🔄 Para parar a aplicação, pressione Ctrl+C")
    
    try:
        subprocess.run(["streamlit", "run", "app.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Erro ao executar aplicação web")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✅ Aplicação encerrada pelo usuário")

def run_cli():
    """Executa a interface CLI"""
    print("💻 Executando interface de linha de comando...")
    
    # Passar argumentos para o CLI
    cli_args = sys.argv[2:]  # Remove 'run.py' e 'cli'
    
    try:
        subprocess.run(["python", "cli.py"] + cli_args, check=True)
    except subprocess.CalledProcessError:
        print("❌ Erro ao executar interface CLI")
        sys.exit(1)

def install_dependencies():
    """Instala as dependências"""
    print("📦 Instalando dependências...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Arquivo requirements.txt não encontrado")
        sys.exit(1)
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependências instaladas com sucesso")
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        sys.exit(1)

def run_tests():
    """Executa os testes da aplicação"""
    print("🧪 Executando testes da aplicação...")
    
    try:
        subprocess.run(["python", "test_app.py"], check=True)
        print("✅ Todos os testes passaram!")
    except subprocess.CalledProcessError:
        print("❌ Alguns testes falharam!")
        sys.exit(1)

def show_help():
    """Mostra ajuda sobre como usar o script"""
    help_text = """
📊 Processador de Rastreabilidade - Script de Execução

Uso: python run.py [comando] [opções]

Comandos disponíveis:
  web          Executa a aplicação web (interface Streamlit)
  cli          Executa a interface de linha de comando
  install      Instala as dependências necessárias
  check        Verifica se as dependências estão instaladas
  test         Executa os testes da aplicação
  help         Mostra esta mensagem de ajuda

Exemplos:
  python run.py web                    # Executa aplicação web
  python run.py cli --help            # Mostra ajuda da CLI
  python run.py cli -r data.csv -s status.xlsx -e estoque.xlsx
  python run.py install               # Instala dependências
  python run.py check                 # Verifica dependências
  python run.py test                  # Executa testes

Para mais informações sobre a CLI, use:
  python run.py cli --help
"""
    print(help_text)

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'web':
        if not check_dependencies():
            sys.exit(1)
        run_web_app()
    
    elif command == 'cli':
        if not check_dependencies():
            sys.exit(1)
        run_cli()
    
    elif command == 'install':
        install_dependencies()
    
    elif command == 'check':
        if check_dependencies():
            print("✅ Todas as dependências estão instaladas")
        else:
            print("❌ Algumas dependências estão faltando")
            sys.exit(1)
    
    elif command == 'test':
        if not check_dependencies():
            sys.exit(1)
        run_tests()
    
    elif command == 'help':
        show_help()
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        show_help()
        sys.exit(1)

if __name__ == '__main__':
    main()