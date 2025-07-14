# Getting Started

This guide provides a comprehensive introduction to py-isa-xform, covering installation, basic usage, and practical examples.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
git clone https://github.com/yomnahisham/py-isa-xform.git
cd py-isa-xform
pip install -r requirements.txt
pip install -e .
```

### Verify Installation

```bash
# Test CLI
python -m isa_xform.cli --help

# List available ISAs
python -m isa_xform.cli list-isas

# Test Python API
python -c "from isa_xform.core.isa_loader import ISALoader; print('Installation successful!')"
```

## Quick Start

### 1. Your First Assembly Program

Create a simple assembly program:

```assembly
# program.s
.org 32
_start:
    LI x0, 10          # Load immediate value 10 into x0
    LI x1, 5           # Load immediate value 5 into x1
    ADD x0, x1         # Add x1 to x0 (x0 = x0 + x1)
    ECALL 0x3FF        # Exit program
```

### 2. Assemble the Program

```bash
# Assemble the program
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin
```

### 3. Disassemble to Verify

```bash
# Disassemble the binary
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program_dis.s
```

### 4. Compare Results

```bash
# View the disassembled output
cat program_dis.s
```

You should see output similar to your original program, demonstrating that the assembly and disassembly process works correctly.

### 5. Simulate the Program

```bash
# Run the program in the simulator
python -m isa_xform.cli simulate --isa zx16 --input program.bin

# Or step through it instruction by instruction
python -m isa_xform.cli simulate --isa zx16 --input program.bin --step
```

The simulator will execute your program and show the register states and execution flow. You can use the `--step` option to execute one instruction at a time for debugging.

## Using the Python API

### 1. Load an ISA Definition

```python
from isa_xform.core.isa_loader import ISALoader

# Load a built-in ISA
loader = ISALoader()
isa_def = loader.load_isa("zx16")

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
# ZX16 program
.org 32
start:
    LI x0, 10          # Load immediate
    LI x1, 5           # Load immediate
    ADD x0, x1         # Add registers
    ECALL 0x3FF        # Exit
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
disasm_result = disassembler.disassemble(result.machine_code, start_address=32)

# Format and display
output = disassembler.format_disassembly(
    disasm_result,
    include_addresses=True,
    include_machine_code=False
)
print("\nDisassembled Code:")
print(output)
```

## Built-in ISA Examples

### ZX16 ISA

The ZX16 ISA is the reference implementation, featuring:

- 16-bit instructions and data words
- 8 general-purpose registers (x0-x7)
- RISC-V inspired instruction set
- Comprehensive instruction coverage

```bash
# Explore ZX16 ISA
python -m isa_xform.cli validate --isa zx16 --verbose

# Run ZX16 example
python -m isa_xform.cli assemble --isa zx16 --input examples/zx16_example.s --output zx16_example.bin
```

### Variable Length ISA Example

Demonstrates support for variable-length instructions:

```bash
# Explore variable length ISA
python -m isa_xform.cli validate --isa variable_length_example --verbose
```

### RISC-V RV32I

Standard RISC-V 32-bit integer instruction set:

```bash
# Explore RISC-V ISA
python -m isa_xform.cli validate --isa riscv_rv32i --verbose
```

## Creating Your Own ISA

### Using the Scaffold Generator

The easiest way to create a new ISA:

```bash
# Generate a basic ISA
python -m isa_xform.cli scaffold --name "MY_ISA" \
  --instructions "ADD,SUB,LI,J,ECALL" \
  --directives ".org,.word,.byte" \
  --output my_isa.json

# Validate the generated ISA
python -m isa_xform.cli validate --isa my_isa.json --verbose
```

### Manual ISA Creation

Create an ISA definition from scratch:

```json
{
  "name": "MyISA",
  "version": "1.0",
  "description": "My custom instruction set architecture",
  "instruction_size": 16,
  "word_size": 16,
  "endianness": "little",
  "address_space": {
    "size": 65536,
    "default_code_start": 32,
    "default_data_start": 32768,
    "default_stack_start": 61438
  },
  "registers": {
    "general_purpose": [
      {"name": "x0", "number": 0, "size": 16, "alias": ["zero"], "description": "Always zero"},
      {"name": "x1", "number": 1, "size": 16, "alias": ["ra"], "description": "Return address"},
      {"name": "x2", "number": 2, "size": 16, "alias": ["sp"], "description": "Stack pointer"}
    ]
  },
  "instructions": [
    {
      "mnemonic": "ADD",
      "format": "R-type",
      "description": "Add registers",
      "syntax": "ADD rd, rs2",
      "semantics": "rd = (rd + rs2) & 0xFFFF",
      "implementation": "# Add instruction\nrd_val = read_register(operands['rd'])\nrs2_val = read_register(operands['rs2'])\nresult = (rd_val + rs2_val) & 0xFFFF\nwrite_register(operands['rd'], result)",
      "encoding": {
        "fields": [
          {"name": "funct4", "bits": "15:12", "value": "0000"},
          {"name": "rs2", "bits": "11:9", "type": "register"},
          {"name": "rd", "bits": "8:6", "type": "register"},
          {"name": "func3", "bits": "5:3", "value": "000"},
          {"name": "opcode", "bits": "2:0", "value": "000"}
        ]
      }
    }
  ]
}
```

## Advanced Features

### Smart Disassembly

The disassembler can reconstruct pseudo-instructions:

```bash
# Smart disassembly with pseudo-instruction reconstruction
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --smart
```

### Automatic Data Region Detection

The disassembler automatically detects data vs code regions:

```bash
# Automatic data region detection (default)
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s

# Manual data region specification
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --data-regions 0x100-0x200
```

### Debug Mode

Get detailed information about the disassembly process:

```bash
# Debug mode with PC progression
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --debug --show-addresses
```

### Symbol Resolution

View resolved symbols during assembly:

```bash
# Assembly with symbol listing
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --list-symbols
```

## Example Programs

### Basic Arithmetic

```assembly
# arithmetic.s
.org 32
main:
    LI x0, 10          # Load first number
    LI x1, 5           # Load second number
    ADD x0, x1         # Add them
    SUB x0, x1         # Subtract second number
    ECALL 0x3FF        # Exit
```

### Control Flow

```assembly
# control_flow.s
.org 32
main:
    LI x0, 10          # Load counter
loop:
    SUB x0, 1          # Decrement counter
    BZ x0, end         # Branch if zero
    J loop             # Jump back to loop
end:
    ECALL 0x3FF        # Exit
```

### Data Operations

```assembly
# data_ops.s
.org 32
main:
    LI x0, 0x1234      # Load immediate
    LUI x1, 0x5678     # Load upper immediate
    ADD x0, x1         # Combine them
    ECALL 0x3FF        # Exit

.data
    .org 0x1000
    .word 0xDEAD       # Data word
    .word 0xBEEF       # Another data word
```

## Testing Your Setup

### Run the Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/important/ -v
python -m pytest tests/custom/ -v

# Run with coverage
python -m pytest tests/ --cov=src/isa_xform --cov-report=html
```

### Test Individual Components

```bash
# Test ISA loading
python -m isa_xform.cli validate --isa zx16 --verbose

# Test assembly
python -m isa_xform.cli assemble --isa zx16 --input tests/important/zx16_simple_test.s --output test.bin

# Test disassembly
python -m isa_xform.cli disassemble --isa zx16 --input test.bin --output test_dis.s

# Compare results
diff tests/important/zx16_simple_test.s test_dis.s
```

## Troubleshooting

### Common Issues

1. **"Module not found"**: Ensure you've installed the package with `pip install -e .`
2. **"Unknown ISA"**: Use `python -m isa_xform.cli list-isas` to see available ISAs
3. **"Invalid ISA definition"**: Use `python -m isa_xform.cli validate --isa <isa>` to check for errors
4. **"Assembly errors"**: Check instruction syntax and operand constraints

### Getting Help

```bash
# General help
python -m isa_xform.cli --help

# Command-specific help
python -m isa_xform.cli assemble --help
python -m isa_xform.cli disassemble --help
python -m isa_xform.cli validate --help
```

### Debug Mode

Enable verbose output for detailed information:

```bash
# Verbose assembly
python -m isa_xform.cli assemble --isa zx16 --input program.s --output program.bin --verbose

# Verbose disassembly
python -m isa_xform.cli disassemble --isa zx16 --input program.bin --output program.s --debug --show-addresses
```

## Next Steps

Now that you have the basics working:

1. **Explore the Examples**: Check out the examples in the `examples/` directory
2. **Read the Documentation**: See the other documentation files for detailed information
3. **Create Your Own ISA**: Use the scaffold generator or create one from scratch
4. **Run the Tests**: Verify everything works with the comprehensive test suite
5. **Contribute**: Check out the contributing guide if you want to help improve the project

## Conclusion

You now have a working py-isa-xform installation and understand the basic workflow. The toolkit provides a complete ecosystem for working with custom instruction set architectures, from definition to assembly and disassembly. The modular design allows you to start simple and gradually add complexity as needed. 