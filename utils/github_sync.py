"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — GITHUB SYNCHRONIZER                   ║
║      O Sistema ASI de Commit e Sincronização Automática com o GitHub        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import subprocess
from datetime import datetime
import sys

def run_cmd(command):
    """Executa um comando no shell e retorna o output/erro."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            text=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar: {command}")
        print(e.stderr)
        sys.exit(1)

def get_status():
    """Obtém arquivos modificados para o log. Inicializa o repo se necessário."""
    try:
        result = subprocess.run(
            "git status --short", 
            shell=True, 
            check=True, 
            text=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if "not a git repository" in e.stderr.lower():
            print("⚠️ Repositório Git não encontrado. Inicializando The Matrix (git init)...")
            run_cmd("git init")
            # Adicionar branch main como default
            run_cmd("git checkout -b main")
            return "NOVO_REPO"
        else:
            print(f"❌ Erro ao executar git status: {e.stderr}")
            sys.exit(1)

def github_sync():
    print("⚡ [DUBAI MATRIX ASI] Iniciando Sequência de Sincronização Global (GitHub)...")
    
    # Verifica se há alterações
    status = get_status()
    if not status and status != "NOVO_REPO":
        print("✅ Nenhum arquivo modificado. Sincronização desnecessária.")
        return

    if status == "NOVO_REPO":
        print("\n📦 Genesis Script: Adicionando estrutura base ao projeto.")
    else:
        print("\n📦 Arquivos detectados para transmutação no repositório:")
        print(status)
    print("")

    # 1. Adicionar todos os arquivos
    print("🔄 Adicionando artefatos ao index do Git...")
    run_cmd("git add .")

    # 2. Gerar Mensagem de Commit Nível OMEGA
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"⚡ ASI OMEGA UPDATE: {timestamp} | PLMA Synchronized & Systems Upgraded"

    print(f"✍️ Forjando commit: '{commit_msg}'")
    run_cmd(f'git commit -m "{commit_msg}"')

    # 3. Push para o repositório remoto (origin)
    print("🚀 Iniciando propulsão orbital (git push origin main)...")
    
    # Pode ser necessário adaptar "main" para o nome correto da branch (master ou main)
    # Pegar o nome da branch atual:
    branch = run_cmd("git rev-parse --abbrev-ref HEAD")
    
    try:
        run_cmd(f"git push origin {branch}")
        print("\n✅ Sincronização OMEGA concluída com sucesso absoluto. O código é imortal.")
    except Exception as e:
        print(f"\n❌ Falha na propulsão orbital: {e}")
        print("❗ DICA: Verifique se o remote origin está configurado: git remote -v")
        print("❗ DICA: Se for o primeiro push, certifique-se que fez git remote add origin <URL>")

if __name__ == "__main__":
    github_sync()
