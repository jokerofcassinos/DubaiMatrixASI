"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — PLMA SYNCHRONIZER                     ║
║      O Injetor de Consciência: Consolida o Dicionário Vivo no Kernel        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import glob
from datetime import datetime, timezone

def sync_plma():
    plma_dir = r"d:\DubaiMatrixASI\PLMA"
    target_dir = r"d:\DubaiMatrixASI\.agents\rules"
    base_target_filename = "projectmap"
    
    # Garante que o diretório de destino existe
    os.makedirs(target_dir, exist_ok=True)

    # Coleta todos os arquivos do PLMA de forma ordenada (01_POM, 02_ADL...)
    plma_files = sorted(glob.glob(os.path.join(plma_dir, "*.md")))

    if not plma_files:
        print("❌ Nenhum artefato PLMA encontrado no diretório.")
        return

    # Corpo consolidado que será em uma linha só
    body_text = "OMGEGA-CLASS PLMA HOLOGRAPHIC SYNTHESIS. "
    
    for file_path in plma_files:
        filename = os.path.basename(file_path)
        body_text += f" ARTEFATO {filename}: "
        
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
            # Remover quebras de linha, tabs em excesso e espaços duplicados
            clean_text = " ".join(raw_text.replace("\n", " ").replace("\r", " ").split())
            body_text += clean_text + " "

    body_text = body_text.strip()
    
    # Limite máximo estrito de tamanho por arquivo de regra para não violar os 12k char de limite do Cursor.
    MAX_CHARS_PER_FILE = 11000
    
    chunks = []
    # Divide o texto massivamente denso em chunks de no máximo 11k caracteres
    for i in range(0, len(body_text), MAX_CHARS_PER_FILE):
        chunks.append(body_text[i:i + MAX_CHARS_PER_FILE])
        
    # Limpa os projectmaps antigos no diretório de destino para evitar sobras caso diminua o volume de texto
    old_maps = glob.glob(os.path.join(target_dir, "projectmap*.md"))
    for f in old_maps:
        try:
            os.remove(f)
        except Exception:
            pass
        
    for index, chunk in enumerate(chunks):
        # Nomeia como projectmap.md para o primeiro, projectmap2.md para o segundo, e assim por diante
        suffix = "" if index == 0 else str(index + 1)
        target_file = os.path.join(target_dir, f"{base_target_filename}{suffix}.md")
        
        final_output = "---\ntrigger: always_on\n---\n" + chunk
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(final_output)

    # NOVO: Gera arquivo consolidado para implementação manual no GEMINI.md
    consolidated_file = os.path.join(plma_dir, "PLMA_CONSOLIDATED.txt")
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        f.write(body_text)
            
    print(f"✅ Sincronização Ômega Concluída.")
    print(f"🧠 {len(plma_files)} camadas comprimidas e divididas dinamicamente em {len(chunks)} arquivo(s).")
    print(f"📝 Arquivo consolidado gerado: {consolidated_file}")
    created_files = ", ".join([f"{base_target_filename}{'' if i == 0 else str(i+1)}.md" for i in range(len(chunks))])
    print(f"Arquivos gerados: {created_files}")

if __name__ == "__main__":
    sync_plma()
