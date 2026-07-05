@echo off
REM Pre-commit hook para Windows: Valida specs antes de commit
REM Spec-Driven Development Discipline (ALFREDO)

echo 🔍 Verificando disciplina Spec-Driven...

REM Verificar se há alterações em arquivos de código
git diff --cached --name-only | findstr /R "\.\(js\|jsx\|ts\|tsx\|py\|go\|rs\|java\|sql\)$" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 📦 Alterações em código detectadas
    
    REM Verificar se specs foram atualizados
    git diff --cached --name-only | findstr /R "\(prd\.md\|specs\\\|\.spec\.\)" > nul 2>&1
    set SPECS_CHANGED=%ERRORLEVEL%
    
    git diff --cached --name-only | findstr /R "\(tasks\.md\|TODO\|CHECKLIST\)" > nul 2>&1
    set TASKS_CHANGED=%ERRORLEVEL%
    
    if %SPECS_CHANGED% NEQ 0 if %TASKS_CHANGED% NEQ 0 (
        echo.
        echo ❌ BLOQUEADO: Alterações em código sem atualização de specs/tasks!
        echo.
        echo 📋 Requisitos Spec-Driven:
        echo    1. Atualize docs/prd.md com os requisitos afetados
        echo    2. Atualize docs/tasks.md com as novas tarefas
        echo    3. Execute: git add docs/prd.md docs/tasks.md
        echo.
        echo 💡 Alternativas:
        echo    - git commit --no-verify (apenas em emergências)
        echo.
        exit /b 1
    )
    
    echo ✅ Specs/tasks atualizados - commit permitido
)

REM Validar sintaxe EARS no PRD se o arquivo existir
if exist docs\prd.md (
    echo 🔍 Validando formato EARS no PRD...
    
    if exist .venv\Scripts\python.exe (
        set PYTHON_EXEC=.venv\Scripts\python.exe
    ) else if exist venv\Scripts\python.exe (
        set PYTHON_EXEC=venv\Scripts\python.exe
    ) else (
        set PYTHON_EXEC=python
    )
    
    %PYTHON_EXEC% scripts\valida_ears.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ❌ BLOQUEADO: Sintaxe EARS inválida detectada no docs/prd.md!
        echo Corrija os erros listados acima antes de realizar o commit.
        echo.
        exit /b 1
    )
)

echo ✅ Verificação SDD concluída
