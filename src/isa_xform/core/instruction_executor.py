"""
Instruction Executor: Executes custom instruction implementations
"""

import ast
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from ..utils.error_handling import InstructionExecutionError


@dataclass
class ExecutionContext:
    """Context for instruction execution"""
    registers: Dict[str, int]
    memory: bytearray
    pc: int
    flags: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.flags is None:
            self.flags = {}


class InstructionExecutor:
    """Executes custom instruction implementations"""
    
    def __init__(self):
        self._compiled_implementations: Dict[str, Any] = {}
        self._safe_globals = {
            '__builtins__': {
                'abs': abs,
                'all': all,
                'any': any,
                'bin': bin,
                'bool': bool,
                'chr': chr,
                'divmod': divmod,
                'enumerate': enumerate,
                'filter': filter,
                'format': format,
                'frozenset': frozenset,
                'getattr': getattr,
                'hasattr': hasattr,
                'hash': hash,
                'hex': hex,
                'id': id,
                'int': int,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'iter': iter,
                'len': len,
                'list': list,
                'map': map,
                'max': max,
                'min': min,
                'next': next,
                'oct': oct,
                'ord': ord,
                'pow': pow,
                'print': print,
                'range': range,
                'repr': repr,
                'reversed': reversed,
                'round': round,
                'set': set,
                'slice': slice,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'type': type,
                'zip': zip,
            }
        }
    
    def compile_implementation(self, mnemonic: str, implementation_code: str) -> bool:
        """
        Compile and validate instruction implementation code
        
        Args:
            mnemonic: Instruction mnemonic
            implementation_code: Python code string
            
        Returns:
            True if compilation successful, False otherwise
        """
        try:
            # Parse the code to check syntax
            ast.parse(implementation_code)
            
            # Compile the code
            compiled_code = compile(implementation_code, f'<{mnemonic}_implementation>', 'exec')
            
            # Store the compiled code
            self._compiled_implementations[mnemonic] = compiled_code
            
            return True
        except SyntaxError as e:
            raise InstructionExecutionError(f"Syntax error in {mnemonic} implementation: {e}")
        except Exception as e:
            raise InstructionExecutionError(f"Error compiling {mnemonic} implementation: {e}")
    
    def execute_instruction(self, mnemonic: str, context: ExecutionContext, 
                          operands: Dict[str, Any]) -> bool:
        """
        Execute a custom instruction implementation
        
        Args:
            mnemonic: Instruction mnemonic
            context: Execution context with registers, memory, etc.
            operands: Dictionary of operand values
            
        Returns:
            True if execution successful, False otherwise
        """
        if mnemonic not in self._compiled_implementations:
            raise InstructionExecutionError(f"No implementation found for instruction: {mnemonic}")
        
        try:
            # Create execution environment
            exec_globals = self._safe_globals.copy()
            exec_locals = {
                'registers': context.registers,
                'memory': context.memory,
                'pc': context.pc,
                'flags': context.flags,
                'operands': operands,
                'context': context,
                # Helper functions
                'read_memory': lambda addr: self._read_memory(context.memory, addr),
                'write_memory': lambda addr, value: self._write_memory(context.memory, addr, value),
                'read_register': lambda name: context.registers.get(name, 0),
                'write_register': lambda name, value: context.registers.update({name: value}),
                'set_flag': lambda name, value: context.flags.update({name: bool(value)}),
                'get_flag': lambda name: context.flags.get(name, False),
            }
            
            # Execute the implementation
            exec(self._compiled_implementations[mnemonic], exec_globals, exec_locals)
            
            return True
        except Exception as e:
            raise InstructionExecutionError(f"Error executing {mnemonic}: {e}")
    
    def _read_memory(self, memory: bytearray, address: int) -> int:
        """Read a 16-bit value from memory (little-endian)"""
        if address < 0 or address + 1 >= len(memory):
            return 0
        return memory[address] | (memory[address + 1] << 8)
    
    def _write_memory(self, memory: bytearray, address: int, value: int) -> None:
        """Write a 16-bit value to memory (little-endian)"""
        if address < 0 or address + 1 >= len(memory):
            return
        memory[address] = value & 0xFF
        memory[address + 1] = (value >> 8) & 0xFF
    
    def has_implementation(self, mnemonic: str) -> bool:
        """Check if an instruction has a custom implementation"""
        return mnemonic in self._compiled_implementations
    
    def list_implementations(self) -> List[str]:
        """List all available custom implementations"""
        return list(self._compiled_implementations.keys())
    
    def clear_implementations(self):
        """Clear all compiled implementations"""
        self._compiled_implementations.clear()


# Global executor instance
_global_executor = InstructionExecutor()


def get_instruction_executor() -> InstructionExecutor:
    """Get the global instruction executor instance"""
    return _global_executor


def compile_instruction_implementations(isa_definition) -> None:
    """
    Compile all instruction implementations from an ISA definition
    
    Args:
        isa_definition: ISADefinition object containing instructions
    """
    executor = get_instruction_executor()
    
    for instruction in isa_definition.instructions:
        if instruction.implementation:
            executor.compile_implementation(instruction.mnemonic, instruction.implementation) 