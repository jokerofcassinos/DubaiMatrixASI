@echo off
REM ╔══════════════════════════════════════════════════════════════╗
REM ║  DUBAI MATRIX ASI — C++ Build Script (Windows)              ║
REM ║  Compila o módulo C++ de alta performance                   ║
REM ╚══════════════════════════════════════════════════════════════╝

echo ⚡ DubaiMatrixASI C++ Build System
echo ═══════════════════════════════════

cd /d "%~dp0"

REM Tentar CMake primeiro
where cmake >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [CMAKE] CMake encontrado. Compilando com CMake...
    if not exist build mkdir build
    cd build
    cmake .. -G "Visual Studio 17 2022" -A x64
    cmake --build . --config Release
    if exist Release\asi_core.dll (
        copy /Y Release\asi_core.dll ..\..\asi_core.dll
        echo ✅ asi_core.dll compilado e copiado para raiz do projeto!
    )
    cd ..
    goto :done
)

REM Fallback: compilação direta com cl.exe (MSVC)
where cl >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [MSVC] Compilando com cl.exe diretamente...
    cl /O2 /Ob2 /Oi /Ot /GL /fp:fast /EHsc /std:c++17 /LD /DASI_EXPORTS ^
        src\quantum_indicators.cpp ^
        src\orderflow_processor.cpp ^
        src\signal_aggregator.cpp ^
        src\agent_cluster.cpp ^
        src\hyperspace_core.cpp ^
        /Fe:..\asi_core.dll /link /LTCG
    echo ✅ Compilação MSVC concluída!
    goto :done
)

REM Fallback: g++ (MinGW)
where g++ >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [G++] Compilando com g++...
    g++ -O3 -shared -march=native -ffast-math -flto -std=c++17 ^
        -DASI_EXPORTS ^
        src\quantum_indicators.cpp ^
        src\orderflow_processor.cpp ^
        src\signal_aggregator.cpp ^
        src\agent_cluster.cpp ^
        src\hyperspace_core.cpp ^
        -o ..\asi_core.dll
    echo ✅ Compilação G++ concluída!
    goto :done
)

echo ❌ Nenhum compilador C++ encontrado (CMake, cl.exe, ou g++).
echo    Instale Visual Studio Build Tools ou MinGW.
exit /b 1

:done
echo.
echo ⚡ Build completo. DLL pronta para uso pela ASI.
