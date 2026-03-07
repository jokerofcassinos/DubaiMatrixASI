cmake_minimum_required(VERSION 3.15)
project(DubaiMatrixASI_CPP VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ═══ OPTIMAL FLAGS PARA MAXIMUM PERFORMANCE ═══
if(MSVC)
    set(CMAKE_CXX_FLAGS_RELEASE "/O2 /Ob2 /Oi /Ot /GL /fp:fast /arch:AVX2 /DNDEBUG")
    set(CMAKE_SHARED_LINKER_FLAGS_RELEASE "/LTCG")
else()
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -ffast-math -flto -DNDEBUG")
endif()

# ═══ SHARED LIBRARY (DLL no Windows) ═══
add_library(asi_core SHARED
    src/quantum_indicators.cpp
    src/orderflow_processor.cpp
    src/signal_aggregator.cpp
    src/agent_cluster.cpp
    src/liquidity_graph.cpp
    src/entropy_processor.cpp
    src/vector_storage.cpp
    src/risk_engine.cpp
    src/causal_engine.cpp
    src/topology_core.cpp
    src/tensor_networks.cpp
    src/pheromone_field.cpp
    src/info_geometry.cpp
    src/hyperspace_core.cpp
)

# Export symbols no Windows
if(WIN32)
    target_compile_definitions(asi_core PRIVATE ASI_EXPORTS)
endif()

# Install target
install(TARGETS asi_core DESTINATION ${CMAKE_SOURCE_DIR}/../)
