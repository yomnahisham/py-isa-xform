#!/usr/bin/env python3

import sys
sys.path.append('../../../src')
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.assembler import Assembler
from isa_xform.core.disassembler import Disassembler
from isa_xform.core.parser import Parser

def test_ascii_detection():
    """Test ASCII string detection in disassembler"""
    loader = ISALoader()
    isa = loader.load_isa('zx16')
    
    # Read the test file
    with open('tests/TC-ZX16/comprehensive/test_ascii_data.s', 'r') as f:
        program = f.read()
    
    print("Original assembly:")
    print(program)
    print("\n" + "="*50 + "\n")
    
    # Parse and assemble
    parser = Parser(isa)
    nodes = parser.parse(program)
    assembler = Assembler(isa)
    result = assembler.assemble(nodes)
    
    # Save binary for inspection
    with open('test_ascii_data.bin', 'wb') as f:
        f.write(result.machine_code)
    
    print(f"Binary size: {len(result.machine_code)} bytes")
    print("Raw bytes:")
    for i in range(0, len(result.machine_code), 16):
        chunk = result.machine_code[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{i:04X}: {hex_str:<48} {ascii_str}")
    
    print("\n" + "="*50 + "\n")
    
    # Disassemble
    disassembler = Disassembler(isa)
    dis_result = disassembler.disassemble(result.machine_code, 0x100)
    
    print("Disassembly with ASCII detection:")
    print(disassembler.format_disassembly(dis_result, include_addresses=False))

if __name__ == '__main__':
    test_ascii_detection() 