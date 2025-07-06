#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.parser import Parser
from isa_xform.core.symbol_table import SymbolTable

def debug_lui_encoding():
    """Debug LUI instruction encoding"""
    print("=== Debugging LUI Instruction Encoding ===")
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa = loader.load_isa_from_file('src/isa_xform/isa_definitions/zx16.json')
    
    # Find LUI instruction
    lui_instruction = None
    for instr in isa.instructions:
        if instr.mnemonic.upper() == 'LUI':
            lui_instruction = instr
            break
    
    print(f"LUI Instruction Encoding Fields:")
    for field in lui_instruction.encoding['fields']:
        print(f"  {field['name']}: bits {field['bits']}, type: {field.get('type', 'fixed')}, value: {field.get('value', 'dynamic')}")
    
    # Test different values
    test_values = [50, 100, 200, 300, 400, 500]
    
    for test_value in test_values:
        print(f"\n--- Testing LUI t0, {test_value} ---")
        
        # Create test assembly
        test_asm = f"""# Test LUI instruction
LUI t0, {test_value}
ECALL 0x3FF  # Exit
"""
        
        try:
            parser = Parser(isa)
            nodes = parser.parse(test_asm)
            
            symbol_table = SymbolTable()
            assembler = Assembler(isa, symbol_table)
            result = assembler.assemble(nodes)
            
            print(f"✓ Assembled {len(result.machine_code)} bytes")
            print(f"Machine code: {[f'0x{b:02X}' for b in result.machine_code]}")
            
            # Analyze the machine code
            if len(result.machine_code) >= 2:
                instruction_word = int.from_bytes(result.machine_code[:2], 'little')
                print(f"Instruction word: 0x{instruction_word:04X}")
                
                # Extract fields according to U-type encoding
                flag = (instruction_word >> 15) & 1
                imm_high = (instruction_word >> 9) & 0x3F  # 6 bits
                rd = (instruction_word >> 6) & 0x7          # 3 bits
                imm_mid = (instruction_word >> 3) & 0x7     # 3 bits
                opcode = instruction_word & 0x7             # 3 bits
                
                print(f"Decoded fields:")
                print(f"  flag: {flag}")
                print(f"  imm_high: {imm_high} (0x{imm_high:X})")
                print(f"  rd: {rd}")
                print(f"  imm_mid: {imm_mid} (0x{imm_mid:X})")
                print(f"  opcode: {opcode}")
                
                # Reconstruct immediate
                reconstructed_imm = (imm_high << 3) | imm_mid
                print(f"Reconstructed immediate: {reconstructed_imm}")
                print(f"Expected immediate: {test_value}")
                
                if reconstructed_imm == test_value:
                    print("✅ Immediate encoding matches!")
                else:
                    print("❌ Immediate encoding mismatch!")
            
            # Disassemble to verify
            disassembler = Disassembler(isa)
            dis_result = disassembler.disassemble(result.machine_code)
            
            print(f"Disassembled: {disassembler.format_disassembly(dis_result).strip()}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_lui_100():
    """Test LUI t0, 100 specifically"""
    print("\n=== Testing LUI t0, 100 ===")
    
    # Load ZX16 ISA
    loader = ISALoader()
    isa = loader.load_isa_from_file('src/isa_xform/isa_definitions/zx16.json')
    
    # Create test assembly
    test_asm = """# Test LUI instruction
LUI t0, 100
ECALL 0x3FF  # Exit
"""
    
    print(f"Test assembly:")
    print(test_asm)
    
    try:
        parser = Parser(isa)
        nodes = parser.parse(test_asm)
        print(f"✓ Parsed {len(nodes)} nodes")
        
        # Debug the parsed nodes
        for i, node in enumerate(nodes):
            print(f"Node {i}: {type(node).__name__}")
            if hasattr(node, 'mnemonic'):
                print(f"  Mnemonic: {node.mnemonic}")
                print(f"  Operands: {node.operands}")
        
        symbol_table = SymbolTable()
        assembler = Assembler(isa, symbol_table)
        result = assembler.assemble(nodes)
        
        print(f"✓ Assembled {len(result.machine_code)} bytes")
        print(f"Machine code: {[f'0x{b:02X}' for b in result.machine_code]}")
        
        # Disassemble to verify
        disassembler = Disassembler(isa)
        dis_result = disassembler.disassemble(result.machine_code)
        
        print(f"\nDisassembled output:")
        print(disassembler.format_disassembly(dis_result))
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_lui_encoding()
    test_lui_100() 