"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SOLÉNN ASI — GITHUB OMEGA SYNCHRONIZER                  ║
║      Motor de Sincronização Assíncrona e Uplink de Integridade Global      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Tuple, List

# [V1.1.1] Configuração de Logging PhD-Grade (Ω-15)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SOLÉNN-SYNC-Ω] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubOmegaSync:
    """
    Sincronizador OMEGA para SOLÉNN v2.
    Gerencia repositório, branches e uplink com o GitHub.
    """

    def __init__(self, branch: str = "omega-intelligence"):
        self.branch = branch
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    async def _run_git(self, *args: str) -> Tuple[int, str, str]:
        """Executa comando git de forma assíncrona (Ω-6)."""
        process = await asyncio.create_subprocess_exec(
            'git', *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.root_dir
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode().strip(), stderr.decode().strip()

    async def initialize_repo(self):
        """Inicializa o repositório se não existir (Genesis)."""
        if not os.path.exists(os.path.join(self.root_dir, '.git')):
            logger.info("Initializing Genesis Repository...")
            await self._run_git('init')
            await self._run_git('checkout', '-b', self.branch)

    async def get_status(self) -> str:
        """Verifica arquivos modificados."""
        _, stdout, _ = await self._run_git('status', '--short')
        return stdout

    async def sync(self):
        """Ciclo principal de sincronização OMEGA."""
        logger.info(f"⚡ Iniciando Uplink OMEGA [Branch: {self.branch}]")

        # 1. Garantir que estamos na branch correta
        code, current_branch, _ = await self._run_git('rev-parse', '--abbrev-ref', 'HEAD')
        if current_branch != self.branch:
            logger.info(f"Switching to branch: {self.branch}")
            await self._run_git('checkout', '-b', self.branch)

        # 2. Verificar alterações
        status = await self.get_status()
        if status:
            logger.info("📦 Artefatos detectados para transmutação:")
            for line in status.splitlines():
                logger.info(f"  > {line}")

            # 3. Add e Commit
            await self._run_git('add', '.')
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"⚡ SOLÉNN OMEGA UPDATE: {timestamp} | Integrated Uplink & Intelligence Upgraded"
            
            logger.info(f"✍️ Forjando commit: '{commit_msg}'")
            code, _, stderr = await self._run_git('commit', '-m', commit_msg)
            
            if code != 0:
                logger.error(f"Falha no commit: {stderr}")
                return
        else:
            logger.info("✅ Local Tree is Green. Verificando Uplink pendente...")

        # 4. Push (Uplink Orbital) - Sempre tentar se houver remote
        logger.info(f"🚀 Iniciando propulsão orbital na branch {self.branch}...")
        code, stdout, stderr = await self._run_git('push', 'origin', self.branch)
        
        if code != 0:
            if "remote name" in stderr.lower() or "not find" in stderr.lower():
                logger.warning("⚠️ Remote 'origin' não configurado. Commit local realizado com sucesso.")
                logger.info("Para uplink global, configure o remoto: git remote add origin <URL>")
            else:
                logger.error(f"Erro no uplink: {stderr}")
        else:
            logger.info("✅ Sincronização OMEGA concluída. A inteligência é imortal.")

async def main():
    # Carregar branch da config ou usar default do CEO
    sync_engine = GitHubOmegaSync(branch="omega-intelligence")
    await sync_engine.initialize_repo()
    await sync_engine.sync()

if __name__ == "__main__":
    asyncio.run(main())
