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
    print("🚀 Iniciando propulsão orbital (git push origin)...")
    
    # Pegar o nome da branch atual:
    try:
        branch = run_cmd("git rev-parse --abbrev-ref HEAD")
    except Exception:
        branch = "main"
        
    try:
        # Check if remote exists
        remotes = subprocess.run("git remote -v", shell=True, capture_output=True, text=True).stdout
        if "origin" not in remotes:
            print("\n⚠️ [ALERTA DE SISTEMA] Repositório remoto 'origin' não configurado.")
            print("Para completar a sincronização orbital, execute no terminal:")
            print("  git remote add origin <URL_DO_SEU_REPOSITORIO_GITHUB>")
            print("  git push -u origin main")
            print("✅ Commit OMEGA forjado localmente com sucesso. Aguardando link de uplink.")
            return

        run_cmd(f"git push origin {branch}")
        print("\n✅ Sincronização OMEGA concluída com sucesso absoluto. O código é imortal.")
    except Exception as e:
        print(f"\n❌ Falha na propulsão orbital: {e}")
        print("❗ DICA: Verifique se o remote origin está configurado corretamente: git remote -v")

if __name__ == "__main__":
    github_sync()
