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
    if %ERRORLEVEL% EQU 0 (
        cmake --build . --config Release
        if exist Release\asi_core.dll (
            copy /Y Release\asi_core.dll ..\..\asi_core.dll
            echo ✅ asi_core.dll compilado e copiado para raiz do projeto!
            cd ..
            goto :done
        )
    )
    echo [CMAKE] Falha na configuracao ou build do CMake. Tentando fallbacks...
    cd ..
)

REM Fallback: compilação direta com cl.exe (MSVC)
where cl >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [MSVC] Compilando com cl.exe diretamente...
    cl /O2 /Ob2 /Oi /Ot /GL /fp:fast /EHsc /std:c++17 /LD /DASI_EXPORTS ^
        src\quantum_indicators.cpp src\orderflow_processor.cpp src\signal_aggregator.cpp ^
    src\agent_cluster.cpp src\hyperspace_core.cpp src\liquidity_graph.cpp src\entropy_processor.cpp ^
    src\vector_storage.cpp src\risk_engine.cpp src\causal_engine.cpp src\topology_core.cpp ^
    src\tensor_networks.cpp src\pheromone_field.cpp src\info_geometry.cpp ^
    src\spiking_neuron.cpp src\mean_field_games.cpp src\chaos_detector.cpp ^
    src\liquid_state_engine.cpp src\holographic_matrix.cpp src\omega_extreme.cpp ^
    src\phd_omega_math.cpp ^
    /Fe:..\asi_core_v2.dll /link /LTCG
    echo ✅ Compilação MSVC concluída!
    goto :done
)

REM Fallback: g++ (MinGW)
where g++ >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [G++] Compilando com g++...
    g++ -O3 -shared -march=native -ffast-math -flto -std=c++17 ^
        -DASI_EXPORTS ^
        src\quantum_indicators.cpp src\orderflow_processor.cpp src\signal_aggregator.cpp ^
    src\agent_cluster.cpp src\hyperspace_core.cpp src\liquidity_graph.cpp src\entropy_processor.cpp ^
    src\vector_storage.cpp src\risk_engine.cpp src\causal_engine.cpp src\topology_core.cpp ^
    src\tensor_networks.cpp src\pheromone_field.cpp src\info_geometry.cpp ^
    src\spiking_neuron.cpp src\mean_field_games.cpp src\chaos_detector.cpp ^
    src\liquid_state_engine.cpp src\holographic_matrix.cpp src\omega_extreme.cpp ^
    src\phd_omega_math.cpp ^
    -o ..\asi_core_v3.dll
    echo ✅ Compilação G++ concluída!
    goto :done
)

echo ❌ Nenhum compilador C++ encontrado (CMake, cl.exe, ou g++).
echo    Instale Visual Studio Build Tools ou MinGW.
exit /b 1

:done
echo.
echo ⚡ Build completo. DLL pronta para uso pela ASI.
