#!/usr/bin/env python3
import os
import shutil
import stat
import sys
from pathlib import Path

# Configura sys.stdout para usar utf-8 se suportado, para evitar erros de unicode
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def setup_sdd():
    print("[SDD] Configurando Spec-Driven Development (SDD) para ALFREDO...")
    
    # 1. Determina a raiz do projeto (onde o script deve rodar ou ser referenciado)
    # Assumindo que este script está em <raiz>/scripts/setup_sdd.py
    project_root = Path(__file__).resolve().parent.parent
    git_dir = project_root / ".git"
    
    if not git_dir.exists():
        print(f"[ERRO] Diretório '.git' não encontrado em: {project_root}")
        print("Este script deve ser executado a partir da pasta raiz do repositório Git.")
        sys.exit(1)
        
    hooks_dir = git_dir / "hooks"
    githooks_src = project_root / "githooks"
    
    if not githooks_src.exists():
        print(f"[ERRO] Diretório de templates de hooks '{githooks_src}' não existe.")
        sys.exit(1)
        
    # 2. Copia os arquivos de hook para a pasta .git/hooks/
    hooks_to_install = ["pre-commit", "pre-commit.cmd", "pre-merge-commit"]
    
    print("\n[HOOKS] Instalando Git Hooks...")
    for hook_name in hooks_to_install:
        src_file = githooks_src / hook_name
        dest_file = hooks_dir / hook_name
        
        if src_file.exists():
            try:
                # Copiar
                shutil.copy2(src_file, dest_file)
                print(f"   [OK] Hook '{hook_name}' instalado com sucesso em .git/hooks/")
                
                # Definir permissão de execução (relevante para Linux/macOS/Git Bash)
                if os.name != 'nt' or hook_name.endswith('.cmd') is False:
                    st = dest_file.stat()
                    dest_file.chmod(st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                    
            except Exception as e:
                print(f"   [ERRO] Erro ao instalar '{hook_name}': {e}")
        else:
            print(f"   [AVISO] Arquivo de origem '{src_file}' não encontrado.")
            
    # 3. Cria as pastas docs e specs se não existirem
    print("\n[PASTAS] Verificando estrutura de diretórios...")
    for folder in ["docs", "specs"]:
        folder_path = project_root / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"   [OK] Pasta '{folder}/' criada.")
        else:
            print(f"   [INFO] Pasta '{folder}/' já existe.")
            
    print("\n[SDD] Disciplina Spec-Driven Ativada:")
    print("   1. Antes de codificar, crie/atualize requisitos em 'docs/prd.md' (formato EARS).")
    print("   2. Mantenha o backlog e tarefas do projeto atualizados em 'docs/tasks.md'.")
    print("   3. Ao realizar um commit, as especificações devem ser incluídas no staging.")
    print("      (Qualquer alteração de código sem atualização de specs será bloqueada).")
    print("   4. Em emergências extremas, use: git commit --no-verify -m \"mensagem\"")
    print("\n[SDD] Configuração concluída com sucesso!")

if __name__ == "__main__":
    setup_sdd()
