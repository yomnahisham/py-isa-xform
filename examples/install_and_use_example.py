#!/usr/bin/env python3
"""
Example: Using py-isa-xform after installing from GitHub Release

This example shows how to use the library once it's installed from a GitHub release.
Users can install it with:
    pip install git+https://github.com/yomnahisham/py-isa-xform.git@v1.0.0
    or
    pip install https://github.com/yomnahisham/py-isa-xform/releases/download/v1.0.0/py_isa_xform-1.0.0-py3-none-any.whl
"""

from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.parser import Parser
from isa_xform.core.assembler import Assembler
from isa_xform.core.disassembler import Disassembler

def main():
    print("🚀 py-isa-xform Library Usage Example")
    print("=" * 50)
    
    # 1. Load an ISA definition
    print("\n1️⃣ Loading ISA definition...")
    loader = ISALoader()
    isa_def = loader.load_isa("zx16")
    
    print(f"   ✅ Loaded ISA: {isa_def.name}")
    print(f"   📏 Word size: {isa_def.word_size} bits")
    print(f"   🔢 Endianness: {isa_def.endianness}")
    
    # 2. Access constants
    print("\n2️⃣ Accessing constants...")
    if isa_def.constants:
        for name, constant in isa_def.constants.items():
            print(f"   📊 {name}: {constant.value} (0x{constant.value:X})")
    else:
        print("   ℹ️  No constants defined in this ISA")
    
    # 3. Access ecall services
    print("\n3️⃣ Accessing ECALL services...")
    if isa_def.ecall_services:
        for service_id, service in isa_def.ecall_services.items():
            print(f"   🔧 Service {service_id}: {service.name}")
            print(f"      📝 Description: {service.description}")
            if service.parameters:
                print(f"      📋 Parameters: {service.parameters}")
            if service.return_value:
                print(f"      📤 Returns: {service.return_value}")
    else:
        print("   ℹ️  No ECALL services defined in this ISA")
    
    # 4. Assemble some code
    print("\n4️⃣ Assembling code...")
    source_code = """
    LI a0, 10      ; Load immediate value 10 into a0
    LI a1, 5       ; Load immediate value 5 into a1
    ADD t0, a0, a1 ; Add a0 and a1, store in t0
    ECALL 0        ; System call
    """
    
    parser = Parser(isa_def)
    assembler = Assembler(isa_def)
    
    try:
        ast_nodes = parser.parse(source_code)
        result = assembler.assemble(ast_nodes)
        
        print(f"   ✅ Assembly successful!")
        print(f"   📦 Machine code: {result.machine_code.hex()}")
        print(f"   📍 Entry point: 0x{result.entry_point:X}" if result.entry_point else "   📍 Entry point: Not set")
        
        # 5. Disassemble the machine code
        print("\n5️⃣ Disassembling machine code...")
        disassembler = Disassembler(isa_def)
        # Convert bytearray to bytes and use default start address
        disassembly = disassembler.disassemble(bytes(result.machine_code))
        
        print("   📝 Disassembly:")
        for instruction in disassembly.instructions:
            print(f"      {instruction.address:04X}: {instruction.mnemonic}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Example completed successfully!")
    print("\n💡 This shows how to use py-isa-xform as a library")
    print("   after installing it from a GitHub release.")

if __name__ == "__main__":
    main() 