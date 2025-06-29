# Getting Started

This guide provides a comprehensive introduction to py-isa-xform, covering installation, basic usage, and practical examples.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
git clone https://github.com/your-org/py-isa-xform.git
cd py-isa-xform
pip install -e .
```

### Verify Installation

```bash
# Test CLI
python -m isa_xform --help

# Test Python API
python -c "from isa_xform.core.isa_loader import ISALoader; print('Installation successful!')"
```

## Quick Start

### 1. Load an ISA Definition

```python
from isa_xform.core.isa_loader import ISALoader

# Load a built-in ISA
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")

print(f"Loaded ISA: {isa_def.name} v{isa_def.version}")
print(f"Word size: {isa_def.word_size} bits")
print(f"Instruction size: {isa_def.instruction_size} bits")
print(f"Endianness: {isa_def.endianness}")
```

### 2. Parse Assembly Code

```python
from isa_xform.core.parser import Parser

# Create parser with ISA-specific syntax
parser = Parser(isa_def)

# Sample assembly code
assembly_code = """
; Simple program
start:
    ADD $r1, $r2, $r3    ; Add registers
    SUB $r4, $r1, $r2    ; Subtract
    JMP end              ; Jump to end
    
data_section:
    .word 0x12345678     ; Data definition
    
end:
    NOP                  ; No operation
"""

# Parse the code
nodes = parser.parse(assembly_code, filename="example.s")

# Display parsed nodes
for i, node in enumerate(nodes):
    print(f"{i}: {type(node).__name__} - {node}")
```

### 3. Assemble to Machine Code

```python
from isa_xform.core.assembler import Assembler

# Create assembler
assembler = Assembler(isa_def)

# Assemble the parsed nodes
result = assembler.assemble(nodes)

print(f"Generated {len(result.machine_code)} bytes of machine code")
print(f"Machine code: {result.machine_code.hex()}")

# Display symbol table
symbols = result.symbol_table.symbols
print(f"\nSymbol Table ({len(symbols)} symbols):")
for name, symbol in symbols.items():
    print(f"  {name}: 0x{symbol.value:04X} ({symbol.type})")
```

### 4. Disassemble Machine Code

```python
from isa_xform.core.disassembler import Disassembler

# Create disassembler
disassembler = Disassembler(isa_def)

# Disassemble the machine code
disasm_result = disassembler.disassemble(result.machine_code, start_address=0x1000)

# Format and display
output = disassembler.format_disassembly(
    disasm_result,
    include_addresses=True,
    include_machine_code=False
)
print("\nDisassembled Code:")
print(output)
```

## Core Concepts

### ISA Definitions

ISA definitions are JSON files that specify the complete architecture:

```json
{
  "name": "SimpleRISC",
  "version": "1.0",
  "description": "Educational RISC processor",
  "word_size": 32,
  "endianness": "little",
  "instruction_size": 32,
  "assembly_syntax": {
    "comment_char": ";",
    "label_suffix": ":",
    "register_prefix": "$",
    "immediate_prefix": "#"
  },
  "registers": {
    "general_purpose": [
      {"name": "R0", "size": 32, "alias": ["ZERO"]},
      {"name": "R1", "size": 32, "alias": ["AT"]}
    ]
  },
  "instructions": [
    {
      "mnemonic": "ADD",
      "opcode": "0001",
      "description": "Add two registers",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "31:28", "value": "0001"},
          {"name": "rd", "bits": "27:24", "type": "register"},
          {"name": "rs1", "bits": "23:20", "type": "register"},
          {"name": "rs2", "bits": "19:16", "type": "register"}
        ]
      },
      "syntax": "ADD $rd, $rs1, $rs2"
    }
  ]
}
```

### Assembly Syntax

The assembler supports configurable syntax based on the ISA definition:

```assembly
; Comments start with semicolon (configurable)
main:                    ; Labels end with colon
    ADD $r1, $r2, $r3   ; Instructions with register prefix
    LDI $r1, #42        ; Immediate values with prefix
    JMP end             ; Label references
    
    .org 0x2000         ; Assembler directives
    .word 0x12345678    ; Data definitions
    
end:
    NOP
```

### Symbol Management

Symbols are automatically collected and resolved:

```python
from isa_xform.core.symbol_table import SymbolTable, SymbolType

# Access symbol table from assembly result
symbol_table = result.symbol_table

# Get specific symbol
main_symbol = symbol_table.get_symbol("main")
if main_symbol:
    print(f"Main at: 0x{main_symbol.value:04X}")

# List symbols by type
labels = symbol_table.list_symbols(SymbolType.LABEL)
constants = symbol_table.list_symbols(SymbolType.CONSTANT)
```

## Command Line Interface

### Available Commands

```bash
# Validate ISA definition
python -m isa_xform validate my_isa.json

# Parse assembly file
python -m isa_xform parse --isa simple_risc program.s

# Assemble to binary
python -m isa_xform assemble --isa simple_risc --output program.bin program.s

# Disassemble binary
python -m isa_xform disassemble --isa simple_risc --output program.s program.bin

# List available ISAs
python -m isa_xform list-isas
```

### Common Options

- `--isa NAME`: Specify ISA to use
- `--isa-file PATH`: Use custom ISA definition file
- `--output PATH`: Specify output file
- `--verbose`: Enable verbose output
- `--start-address ADDR`: Set starting address for disassembly

## Working with Custom ISAs

### Creating a Custom ISA

Create a JSON file defining your custom ISA:

```json
{
  "name": "TinyProcessor",
  "version": "1.0",
  "description": "8-bit educational processor",
  "word_size": 8,
  "endianness": "big",
  "instruction_size": 16,
  "assembly_syntax": {
    "comment_char": "#",
    "label_suffix": ":",
    "register_prefix": "%",
    "immediate_prefix": "@"
  },
  "address_space": {
    "default_code_start": 256,
    "default_data_start": 512
  },
  "registers": {
    "general_purpose": [
      {"name": "A", "size": 8, "description": "Accumulator"},
      {"name": "B", "size": 8, "description": "General purpose"},
      {"name": "C", "size": 8, "description": "General purpose"}
    ]
  },
  "instructions": [
    {
      "mnemonic": "LOAD",
      "opcode": "0001",
      "description": "Load immediate into register",
      "encoding": {
        "fields": [
          {"name": "opcode", "bits": "15:12", "value": "0001"},
          {"name": "reg", "bits": "11:8", "type": "register"},
          {"name": "immediate", "bits": "7:0", "type": "immediate"}
        ]
      },
      "syntax": "LOAD %reg, @immediate"
    }
  ]
}
```

### Using Custom ISA

```python
# Load custom ISA
loader = ISALoader()
custom_isa = loader.load_isa_from_file("tiny_processor.json")

# Use with standard workflow
parser = Parser(custom_isa)
assembler = Assembler(custom_isa)

# Assembly code using custom syntax
custom_code = """
# TinyProcessor assembly
start:
    LOAD %A, @42    # Load 42 into accumulator
    LOAD %B, @10    # Load 10 into B register
end:
"""

nodes = parser.parse(custom_code)
result = assembler.assemble(nodes)
```

## Error Handling

### Understanding Errors

```python
from isa_xform.utils.error_handling import ErrorReporter, ISAError

def safe_assembly(source_code, isa_definition):
    """Safely assemble code with comprehensive error handling."""
    reporter = ErrorReporter()
    
    try:
        parser = Parser(isa_definition)
        assembler = Assembler(isa_definition)
        
        # Parse source
        nodes = parser.parse(source_code, "input.s")
        
        # Assemble
        result = assembler.assemble(nodes)
        
        return result, reporter
        
    except ISAError as e:
        reporter.add_error(e)
        print("Assembly failed:")
        print(reporter.format_errors())
        return None, reporter
```

### Common Error Types

```python
# ISA loading errors
try:
    isa_def = loader.load_isa("nonexistent")
except ISALoadError as e:
    print(f"ISA loading failed: {e}")

# Parsing errors
try:
    nodes = parser.parse("INVALID_INSTRUCTION")
except ParseError as e:
    print(f"Parse error at line {e.location.line}: {e}")

# Assembly errors
try:
    result = assembler.assemble(nodes)
except AssemblerError as e:
    print(f"Assembly error: {e}")
    if e.suggestion:
        print(f"Suggestion: {e.suggestion}")
```

## Advanced Features

### Bit Manipulation

```python
from isa_xform.utils.bit_utils import *

# Extract instruction fields
def decode_instruction(machine_code):
    """Decode a 32-bit instruction."""
    opcode = extract_bits(machine_code, 31, 28)
    rd = extract_bits(machine_code, 27, 24)
    rs1 = extract_bits(machine_code, 23, 20)
    rs2 = extract_bits(machine_code, 19, 16)
    
    return {
        'opcode': opcode,
        'rd': rd,
        'rs1': rs1,
        'rs2': rs2
    }

# Build instruction
def encode_r_type(opcode, rd, rs1, rs2):
    """Encode R-type instruction."""
    instruction = 0
    instruction = set_bits(instruction, 31, 28, opcode)
    instruction = set_bits(instruction, 27, 24, rd)
    instruction = set_bits(instruction, 23, 20, rs1)
    instruction = set_bits(instruction, 19, 16, rs2)
    return instruction

# Sign extension
immediate = sign_extend(0xFF, 8, 32)  # Extend 8-bit to 32-bit
```

### Two-Pass Assembly

```python
def demonstrate_forward_references():
    """Show how two-pass assembly handles forward references."""
    
    code_with_forward_ref = """
    start:
        JMP end        ; Forward reference to 'end'
        ADD $r1, $r2, $r3
        
    middle:
        SUB $r1, $r2, $r3
        JMP start      ; Backward reference to 'start'
        
    end:
        NOP
    """
    
    parser = Parser(isa_def)
    assembler = Assembler(isa_def)
    
    nodes = parser.parse(code_with_forward_ref)
    
    # Two-pass assembly resolves forward references
    result = assembler.assemble(nodes, two_pass=True)
    
    print("Forward references resolved successfully!")
    return result
```

### Custom Directives

```python
def handle_custom_directive():
    """Example of processing custom assembly directives."""
    
    code_with_directives = """
    .org 0x1000        ; Set origin address
    main:
        ADD $r1, $r2, $r3
        
    .align 16          ; Align to 16-byte boundary
    data_area:
        .word 0x12345678, 0x9ABCDEF0
        .byte 0x42
        .ascii "Hello"
        .space 64      ; Reserve 64 bytes
        
    .equ STACK_SIZE, 1024  ; Define constant
    """
    
    parser = Parser(isa_def)
    assembler = Assembler(isa_def)
    
    nodes = parser.parse(code_with_directives)
    result = assembler.assemble(nodes)
    
    return result
```

## Performance Optimization

### Batch Processing

```python
def process_multiple_files(file_list, isa_name):
    """Efficiently process multiple assembly files."""
    
    # Load ISA once
    loader = ISALoader()
    isa_def = loader.load_isa(isa_name)
    
    # Create reusable components
    parser = Parser(isa_def)
    assembler = Assembler(isa_def)
    
    results = []
    
    for filename in file_list:
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            # Parse and assemble
            nodes = parser.parse(source, filename)
            result = assembler.assemble(nodes)
            
            # Save binary output
            bin_filename = filename.replace('.s', '.bin')
            with open(bin_filename, 'wb') as f:
                f.write(result.machine_code)
            
            results.append((filename, result))
            print(f"Processed: {filename} -> {bin_filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    return results
```

### Memory-Efficient Processing

```python
def stream_large_disassembly(binary_file, isa_def, chunk_size=4096):
    """Process large binary files in chunks."""
    
    disassembler = Disassembler(isa_def)
    instruction_size = isa_def.instruction_size // 8
    
    with open(binary_file, 'rb') as f:
        address = 0
        
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            # Process complete instructions only
            instruction_count = len(chunk) // instruction_size
            complete_chunk = chunk[:instruction_count * instruction_size]
            
            if complete_chunk:
                result = disassembler.disassemble(complete_chunk, address)
                output = disassembler.format_disassembly(result)
                print(output)
                
                address += len(complete_chunk)
            
            # Handle remaining bytes in next iteration
            if len(chunk) % instruction_size != 0:
                f.seek(f.tell() - (len(chunk) % instruction_size))
```

## Testing and Validation

### Unit Testing

```python
import unittest
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.parser import Parser
from isa_xform.core.assembler import Assembler

class TestAssembly(unittest.TestCase):
    
    def setUp(self):
        self.loader = ISALoader()
        self.isa_def = self.loader.load_isa("simple_risc")
        self.parser = Parser(self.isa_def)
        self.assembler = Assembler(self.isa_def)
    
    def test_basic_instruction(self):
        """Test assembly of basic instruction."""
        code = "ADD $r1, $r2, $r3"
        nodes = self.parser.parse(code)
        result = self.assembler.assemble(nodes)
        
        self.assertEqual(len(result.machine_code), 4)  # 32-bit instruction
        self.assertGreater(len(result.machine_code), 0)
    
    def test_forward_reference(self):
        """Test forward reference resolution."""
        code = """
        JMP end
        ADD $r1, $r2, $r3
        end:
            NOP
        """
        nodes = self.parser.parse(code)
        result = self.assembler.assemble(nodes)
        
        self.assertIn("end", result.symbol_table.symbols)

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```python
def test_round_trip():
    """Test assembly -> disassembly round trip."""
    
    original_code = """
    main:
        ADD $r1, $r2, $r3
        SUB $r4, $r1, $r2
        JMP end
    end:
        NOP
    """
    
    # Assemble
    parser = Parser(isa_def)
    assembler = Assembler(isa_def)
    nodes = parser.parse(original_code)
    asm_result = assembler.assemble(nodes)
    
    # Disassemble
    disassembler = Disassembler(isa_def)
    disasm_result = disassembler.disassemble(asm_result.machine_code)
    
    # Compare
    reconstructed = disassembler.format_disassembly(disasm_result)
    print("Original:")
    print(original_code)
    print("\nReconstructed:")
    print(reconstructed)
    
    # Verify key instructions are preserved
    assert "ADD" in reconstructed
    assert "SUB" in reconstructed
    assert "JMP" in reconstructed
    assert "NOP" in reconstructed
```

## Best Practices

### Code Organization

1. **Load ISA definitions once** and reuse across operations
2. **Handle errors gracefully** with proper exception handling
3. **Use symbol tables** for complex programs with many labels
4. **Validate input** before processing to catch errors early
5. **Test round-trip** assembly/disassembly for verification

### Error Prevention

1. **Validate ISA definitions** before use
2. **Check file existence** before processing
3. **Use appropriate data types** for addresses and values
4. **Validate operand ranges** against ISA constraints
5. **Provide clear error messages** with context

### Performance Tips

1. **Reuse component instances** for batch processing
2. **Use single-pass assembly** when no forward references exist
3. **Process large files in chunks** to manage memory usage
4. **Cache ISA lookups** for frequently used operations
5. **Profile critical paths** in performance-sensitive applications

## Next Steps

Now that you understand the basics, explore these advanced topics:

1. **[Architecture Overview](architecture.md)** - System design and component interactions
2. **[ISA Definition Format](isa-definition.md)** - Complete ISA specification reference
3. **[API Reference](api-reference.md)** - Detailed API documentation
4. **[Assembler Documentation](assembler.md)** - Advanced assembly features
5. **[Disassembler Documentation](disassembler.md)** - Disassembly techniques
6. **[Error Handling Guide](error-handling.md)** - Comprehensive error management
7. **[Testing Guide](testing.md)** - Testing strategies and frameworks

## Support and Community

- **Documentation**: Complete guides in the `docs/` directory
- **Examples**: Sample ISAs and programs in `examples/`
- **Issues**: Report bugs and request features on GitHub
- **Contributing**: See [Contributing Guide](contributing.md) for development setup 