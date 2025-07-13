#!/usr/bin/env python3
"""
Test script for RV32I ISA definition
"""

from src.isa_xform.core.isa_loader import ISALoader
from src.isa_xform.core.assembler import Assembler
from src.isa_xform.core.disassembler import Disassembler

def test_rv32i():
    print("Testing RV32I ISA definition...")
    
    # Load the ISA
    loader = ISALoader()
    isa = loader.load_isa('rv32i')
    
    print(f"✓ Loaded ISA: {isa.name} v{isa.version}")
    print(f"✓ Registers: {isa.register_count}")
    print(f"✓ Instructions: {len(isa.instructions)}")
    
    # Test assembly
    assembler = Assembler(isa)
    disassembler = Disassembler(isa)
    
    # Simple test program
    test_program = """
# RV32I test program
start:
    addi x1, x0, 10      # x1 = 10
    addi x2, x0, 20      # x2 = 20
    add x3, x1, x2       # x3 = x1 + x2
    sub x4, x2, x1       # x4 = x2 - x1
    sw x3, 0(x0)         # store x3 to memory[0]
    lw x5, 0(x0)         # load from memory[0] to x5
    beq x3, x5, start    # branch if equal
    jal x6, start        # jump and link
"""
    
    print("\nTesting assembly...")
    try:
        # Assemble the program
        assembled = assembler.assemble(test_program)
        print(f"✓ Assembly successful: {len(assembled.machine_code)} bytes")
        
        # Disassemble the program
        disassembled = disassembler.disassemble(assembled.machine_code)
        print(f"✓ Disassembly successful: {len(disassembled.instructions)} instructions")
        
        print("\nFirst few instructions:")
        for i, instr in enumerate(disassembled.instructions[:5]):
            print(f"  {i*4:04x}: {instr}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    print("\n✓ RV32I ISA test completed successfully!")
    return True

if __name__ == "__main__":
    test_rv32i() 