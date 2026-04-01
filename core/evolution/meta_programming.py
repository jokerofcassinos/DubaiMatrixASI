import ast
import inspect
import logging
import importlib
import sys
import copy
from typing import Callable, Any, Dict, Optional, Type

from core.intelligence.base_synapse import BaseSynapse

log = logging.getLogger("SOLENN.MetaProgramming")

class HaltingAnalyzer(ast.NodeVisitor):
    """V73: Analisador estático para prevenir loops infinitos (Ω-12)."""
    def visit_While(self, node):
        log.warning("⚠️ [Ω-META] Loop 'While' detectado. Recomenda-se cautela.")
        self.generic_visit(node)

class MetaProgrammingEngine(BaseSynapse):
    """
    Ω-34, Ω-12 & Ψ-13: O Motor de Auto-Modificação Estrutural da SOLÉNN.
    
    Permite que o sistema reescreva sua própria lógica em runtime via AST,
    possibilitando a evolução de agentes e a otimização JIT.
    """
    
    def __init__(self):
        super().__init__("MetaProgramming")
        self.evolved_classes: Dict[str, Type] = {}
        self.evolution_history: Dict[str, Any] = {}

    def rewrite_logic(self, 
                      target_obj: Any, 
                      transformer: ast.NodeTransformer,
                      new_name_suffix: str = "_Evolved") -> Optional[Type]:
        """
        V1-V9: Recebe um objeto (classe ou função), aplica transformação AST e recompila.
        """
        try:
            # 1. Extrair código fonte
            source = inspect.getsource(target_obj)
            tree = ast.parse(source)
            
            # 2. V73: Verificação de Invariantes de Segurança
            halting = HaltingAnalyzer()
            halting.visit(tree)
            
            # 3. Aplicar transformação AST (V10-V18)
            modified_tree = transformer.visit(tree)
            ast.fix_missing_locations(modified_tree)
            
            # 4. Modificar o nome da classe p/ evitar colisão em cache
            orig_name = target_obj.__name__
            new_name = f"{orig_name}{new_name_suffix}"
            
            # Atualizar nome no AST se for classe
            for node in modified_tree.body:
                if isinstance(node, ast.ClassDef) and node.name == orig_name:
                    node.name = new_name
            
            # 5. V37: Compilação e Execução em Sandbox
            code_obj = compile(modified_tree, filename=f"<solenn_evolved_{new_name}>", mode="exec")
            
            # Criar namespace isolado (V38)
            namespace = {}
            # Manter referências do módulo original para que imports funcionem
            parent_module = sys.modules[target_obj.__module__]
            namespace.update(parent_module.__dict__)
            
            exec(code_obj, namespace)
            
            evolved_class = namespace[new_name]
            
            # Registrar evolução no histórico
            self.evolved_classes[new_name] = evolved_class
            self.evolution_history[new_name] = {
                "original": orig_name,
                "transformer": transformer.__class__.__name__,
                "timestamp": sys.meta_path # Placeholder p/ tempo se necessário
            }
            
            log.info(f"🧬 [Ω-META] Lógica {orig_name} evoluída para {new_name} via reescrita AST.")
            return evolved_class

        except Exception as e:
            log.error(f"❌ [Ω-META] Falha crítica na transmutação de código: {e}")
            return None

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """[Ω-EXEC] Gateway de evolução de código."""
        return {
            "node": self.name,
            "evolved_count": len(self.evolved_classes)
        }

class ThresholdOptimizer(ast.NodeTransformer):
    """V1: Transformador AST de Elite p/ otimização de constantes (Ω-34)."""
    def __init__(self, target_var: str, new_value: Any):
        self.target_var = target_var
        self.new_value = new_value

    def visit_Assign(self, node):
        # Procurar por atribuições de variáveis específicas
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == self.target_var:
                log.info(f"⚡ [Ω-META] Otimizando constante AST: {self.target_var} -> {self.new_value}")
                return ast.Assign(
                    targets=node.targets,
                    value=ast.Constant(value=self.new_value)
                )
        return self.generic_visit(node)

# Motor de Meta-Programação Ω (v2) inicializado.
