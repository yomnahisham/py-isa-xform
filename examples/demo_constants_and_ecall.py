#!/usr/bin/env python3
"""
Demonstration of accessing constants and ecall services from ISA definitions.
"""

from isa_xform.core.isa_loader import ISALoader

def demo_constants_and_ecall_services():
    """Demonstrate loading and accessing constants and ecall services"""
    
    # Load the ZX16 ISA
    loader = ISALoader()
    isa_def = loader.load_isa("zx16")
    
    print(f"ISA: {isa_def.name} v{isa_def.version}")
    print(f"Description: {isa_def.description}")
    print()
    
    # Display constants
    print("=== Constants ===")
    for const_name, constant in isa_def.constants.items():
        print(f"  {const_name}: {constant.value} (0x{constant.value:X})")
        if constant.description:
            print(f"    Description: {constant.description}")
    print()
    
    # Display ecall services
    print("=== ECALL Services ===")
    for service_id, service in isa_def.ecall_services.items():
        print(f"  {service_id}: {service.name}")
        print(f"    Description: {service.description}")
        if service.parameters:
            print(f"    Parameters:")
            for param_name, param_desc in service.parameters.items():
                print(f"      {param_name}: {param_desc}")
        print(f"    Returns: {service.return_value}")
        print()
    
    # Demonstrate practical usage
    print("=== Practical Usage Examples ===")
    
    # Access specific constants
    code_start = isa_def.constants["CODE_START"].value
    mmio_base = isa_def.constants["MMIO_BASE"].value
    print(f"Code starts at: 0x{code_start:X}")
    print(f"MMIO base address: 0x{mmio_base:X}")
    
    # Access specific ecall services
    print_char_service = isa_def.ecall_services["0x000"]
    exit_service = isa_def.ecall_services["0x00A"]
    
    print(f"To print a character: ECALL {print_char_service.name} (service 0x000)")
    print(f"  Parameter: {list(print_char_service.parameters.keys())[0]}")
    print(f"To exit program: ECALL {exit_service.name} (service 0x00A)")
    print(f"  Parameter: {list(exit_service.parameters.keys())[0]}")

if __name__ == "__main__":
    demo_constants_and_ecall_services() 