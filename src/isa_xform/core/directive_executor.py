"""
Directive Executor: Executes custom directive implementations
"""

import ast
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from ..utils.error_handling import InstructionExecutionError

@dataclass
class DirectiveContext:
    """Context for directive execution"""
    assembler: Any  # Reference to the assembler instance
    symbol_table: Any
    memory: bytearray
    current_address: int
    section: str
    args: List[Any]
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

class DirectiveExecutor:
    """Executes custom directive implementations"""
    def __init__(self):
        self._compiled_implementations: Dict[str, Any] = {}
        self._safe_globals = {
            '__builtins__': {
                'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool, 'chr': chr, 'divmod': divmod,
                'enumerate': enumerate, 'filter': filter, 'format': format, 'frozenset': frozenset, 'getattr': getattr,
                'hasattr': hasattr, 'hash': hash, 'hex': hex, 'id': id, 'int': int, 'isinstance': isinstance,
                'issubclass': issubclass, 'iter': iter, 'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
                'next': next, 'oct': oct, 'ord': ord, 'pow': pow, 'print': print, 'range': range, 'repr': repr,
                'reversed': reversed, 'round': round, 'set': set, 'slice': slice, 'sorted': sorted, 'str': str,
                'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip, 'bytes': bytes, 'bytearray': bytearray,
            }
        }
    def compile_implementation(self, name: str, implementation_code: str) -> bool:
        try:
            ast.parse(implementation_code)
            compiled_code = compile(implementation_code, f'<{name}_directive_impl>', 'exec')
            self._compiled_implementations[name] = compiled_code
            return True
        except SyntaxError as e:
            raise InstructionExecutionError(f"Syntax error in {name} directive implementation: {e}")
        except Exception as e:
            raise InstructionExecutionError(f"Error compiling {name} directive implementation: {e}")
    def execute_directive(self, name: str, context: DirectiveContext) -> Any:
        if name not in self._compiled_implementations:
            raise InstructionExecutionError(f"No implementation found for directive: {name}")
        try:
            exec_globals = self._safe_globals.copy()
            exec_locals = {
                'assembler': context.assembler,
                'symbol_table': context.symbol_table,
                'memory': context.memory,
                'current_address': context.current_address,
                'section': context.section,
                'args': context.args,
                'extra': context.extra,
                'context': context,
            }
            exec(self._compiled_implementations[name], exec_globals, exec_locals)
            return exec_locals.get('result', None)
        except Exception as e:
            raise InstructionExecutionError(f"Error executing {name} directive: {e}")
    def has_implementation(self, name: str) -> bool:
        return name in self._compiled_implementations
    def list_implementations(self) -> List[str]:
        return list(self._compiled_implementations.keys())
    def clear_implementations(self):
        self._compiled_implementations.clear()

_global_directive_executor = DirectiveExecutor()

def get_directive_executor() -> DirectiveExecutor:
    return _global_directive_executor

def compile_directive_implementations(isa_definition) -> None:
    executor = get_directive_executor()
    for directive in isa_definition.directives.values():
        if directive.implementation:
            # Compile for the canonical name
            executor.compile_implementation(directive.name, directive.implementation)
            # Also compile for all aliases
            for alias in getattr(directive, 'aliases', []):
                executor.compile_implementation(alias, directive.implementation) 