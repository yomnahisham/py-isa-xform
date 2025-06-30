from isa_xform.core.simulator import ZX16Simulator
import sys
import struct
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from isa_xform.core.disassembler import Disassembler, DisassembledInstruction
from isa_xform.core.isa_loader import ISADefinition, Instruction
from isa_xform.core.symbol_table import SymbolTable


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <machine_code_file>", file=sys.stderr)
        sys.exit(1)


    filename = sys.argv[1]
    print(f"Start: Loading {filename}")
    
    # Check if file exists
    if not Path(filename).exists():
        print(f"Error: File '{filename}' not found", file=sys.stderr)
        sys.exit(1)
    
    simulator = ZX16Simulator()
    if not simulator.load_memory_from_file(filename):
        sys.exit(1)

    print(f"Registers before execution: {simulator.regs}") 
    
    instruction_count = 0
    while simulator.pc < len(simulator.memory) and instruction_count < 1000:  # Add safety limit
        # Fetch a 16-bit instruction from memory (little-endian)
        inst = simulator.memory[simulator.pc] | (simulator.memory[simulator.pc + 1] << 8)
        
        # Skip if instruction is 0 (might indicate end of program)
        if inst == 0:
            print(f"Encountered null instruction at 0x{simulator.pc:04X}, stopping")
            break
        
        # Use advanced disassembler
        disasm = simulator.disassemble_instruction(inst, simulator.pc)
        print(f"0x{simulator.pc:04X}: {inst:04X} {disasm}")
        
        # Execute instruction
        if not simulator.execute_instruction(inst):
            print("Execution terminated by instruction")
            break
            
        instruction_count += 1
        
        # Terminate if PC goes out of bounds
        if simulator.pc >= len(simulator.memory):
            print("PC out of bounds, stopping")
            break
    print(f"Execution completed after {instruction_count} instructions")
    print(f"Registers after execution: {simulator.regs}") 
    return 0


if __name__ == "__main__":
    main()