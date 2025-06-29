# API Reference

This document provides comprehensive API documentation for all py-isa-xform components.

## Table of Contents

- [Core Modules](#core-modules)
  - [isa_xform.core](#isa-xform-core)
    - [ISA Loader](#isa-loader)
    - [Parser](#parser)
    - [Symbol Table](#symbol-table)
- [CLI Interface](#cli-interface)
- [Data Structures](#data-structures)
- [Error Handling](#error-handling)

## Core Modules

### isa_xform.core

#### ISA Loader (`isa_xform.core.isa_loader`)

##### Classes

**ISALoader**

Main class for loading and validating ISA definitions.

```python
class ISALoader:
    def __init__(self):
        """Initialize ISA loader with built-in ISA registry."""
    
    def load_isa(self, name: str) -> ISADefinition:
        """Load built-in ISA by name."""
    
    def load_isa_from_file(self, filepath: str) -> ISADefinition:
        """Load ISA from JSON file."""
    
    def list_available_isas(self) -> List[str]:
        """List names of available built-in ISAs."""
    
    def validate_isa(self, isa_data: dict) -> bool:
        """Validate ISA definition structure."""
```

**ISADefinition**

Complete ISA specification container.

```python
class ISADefinition:
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.description = ""
        self.word_size = 32
        self.endianness = "little"
        self.instruction_size = 32
        self.registers = {}
        self.instructions = []
        self.directives = {}
        self.assembly_syntax = AssemblySyntax()
        self.address_space = AddressSpace()
    
    def get_instruction(self, mnemonic: str) -> Optional[Instruction]:
        """Get instruction by mnemonic."""
    
    def get_register(self, name: str) -> Optional[Register]:
        """Get register by name or alias."""
```

**Instruction**

Individual instruction specification.

```python
class Instruction:
    def __init__(self, mnemonic: str, opcode: str):
        self.mnemonic = mnemonic
        self.opcode = opcode
        self.format = ""
        self.description = ""
        self.syntax = ""
        self.semantics = ""
        self.encoding = {}
        self.operands = []
    
    def matches_pattern(self, machine_code: int) -> bool:
        """Check if machine code matches this instruction."""
```

#### Assembler (`isa_xform.core.assembler`)

##### Classes

**Assembler**

Main assembly engine.

```python
class Assembler:
    def __init__(self, isa_definition: ISADefinition, symbol_table: Optional[SymbolTable] = None):
        """Initialize assembler with ISA definition and optional symbol table."""
    
    def assemble(self, nodes: List[ASTNode], two_pass: bool = True) -> AssembledCode:
        """Assemble AST nodes into machine code."""
    
    def assemble_single_pass(self, nodes: List[ASTNode]) -> AssembledCode:
        """Assemble using single pass (no forward references)."""
```

**AssembledCode**

Result container for assembled output.

```python
class AssembledCode:
    def __init__(self):
        self.machine_code = bytearray()
        self.symbol_table = SymbolTable()
        self.entry_point = None
        self.sections = {}
    
    def to_bytes(self) -> bytes:
        """Convert to bytes object."""
    
    def to_hex_string(self) -> str:
        """Convert to hexadecimal string representation."""
```

#### Disassembler (`isa_xform.core.disassembler`)

##### Classes

**Disassembler**

Main disassembly engine.

```python
class Disassembler:
    def __init__(self, isa_definition: ISADefinition, 
                 symbol_table: Optional[SymbolTable] = None,
                 max_consecutive_nops: int = 8):
        """Initialize disassembler with ISA definition."""
    
    def disassemble(self, machine_code: bytes, start_address: int = 0) -> DisassemblyResult:
        """Disassemble machine code into instructions."""
    
    def format_disassembly(self, result: DisassemblyResult, 
                          include_addresses: bool = True,
                          include_machine_code: bool = False) -> str:
        """Format disassembly result as text."""
```

**DisassemblyResult**

Complete disassembly result container.

```python
class DisassemblyResult:
    def __init__(self):
        self.instructions = []
        self.symbols = {}
        self.data_sections = {}
        self.entry_point = None
    
    def get_instruction_at(self, address: int) -> Optional[DisassembledInstruction]:
        """Get instruction at specific address."""
```

#### Parser (`isa_xform.core.parser`)

##### Classes

**Parser**

Assembly language parser.

```python
class Parser:
    def __init__(self, isa_definition: Optional[ISADefinition] = None):
        """Initialize parser with optional ISA definition for syntax rules."""
    
    def parse(self, source: str, filename: Optional[str] = None) -> List[ASTNode]:
        """Parse assembly source code into AST nodes."""
    
    def parse_line(self, line: str, line_num: int, filename: Optional[str] = None) -> Optional[ASTNode]:
        """Parse single line of assembly code."""
```

**ASTNode**

Base class for all AST nodes.

```python
class ASTNode:
    def __init__(self, line: int, column: int, file: Optional[str] = None):
        self.line = line
        self.column = column
        self.file = file
    
    def accept(self, visitor):
        """Accept visitor for AST traversal."""
```

#### Symbol Table (`isa_xform.core.symbol_table`)

##### Classes

**SymbolTable**

Symbol management container.

```python
class SymbolTable:
    def __init__(self):
        self.symbols = {}
    
    def define_symbol(self, name: str, value: int, symbol_type: SymbolType = SymbolType.LABEL) -> Symbol:
        """Define a new symbol."""
    
    def get_symbol(self, name: str) -> Optional[Symbol]:
        """Get symbol by name."""
    
    def resolve_symbol(self, name: str) -> int:
        """Resolve symbol to its value."""
    
    def list_symbols(self, symbol_type: Optional[SymbolType] = None) -> List[Symbol]:
        """List all symbols, optionally filtered by type."""
```

**Symbol**

Individual symbol representation.

```python
class Symbol:
    def __init__(self, name: str, value: int, symbol_type: SymbolType):
        self.name = name
        self.value = value
        self.type = symbol_type
        self.defined = True
        self.references = []
        self.line = None
        self.file = None
```

### Utilities

#### Bit Utils (`isa_xform.utils.bit_utils`)

##### Functions

**Bit Field Operations**

```python
def extract_bits(value: int, high: int, low: int) -> int:
    """Extract bits from value between high and low positions (inclusive)."""

def set_bits(value: int, high: int, low: int, new_value: int) -> int:
    """Set bits in value between high and low positions."""

def parse_bit_range(bit_range: str) -> Tuple[int, int]:
    """Parse bit range string in format 'high:low'."""

def create_mask(bit_width: int) -> int:
    """Create mask with specified number of bits set."""
```

**Sign Extension**

```python
def sign_extend(value: int, source_bit_width: int, target_bit_width: int = 32) -> int:
    """Sign extend value from source to target bit width."""
```

**Alignment Operations**

```python
def align_up(value: int, alignment: int) -> int:
    """Align value up to nearest multiple of alignment."""

def align_down(value: int, alignment: int) -> int:
    """Align value down to nearest multiple of alignment."""

def is_power_of_two(value: int) -> bool:
    """Check if value is a power of 2."""
```

**Bit Analysis**

```python
def count_leading_zeros(value: int, bit_width: int) -> int:
    """Count leading zero bits in value."""

def count_trailing_zeros(value: int) -> int:
    """Count trailing zero bits in value."""
```

**Endianness Conversion**

```python
def bytes_to_int(bytes_data: bytes, endianness: str = 'little') -> int:
    """Convert byte array to integer with specified endianness."""

def int_to_bytes(value: int, byte_count: int, endianness: str = 'little') -> bytes:
    """Convert integer to byte array with specified endianness."""
```

#### Error Handling (`isa_xform.utils.error_handling`)

##### Classes

**Error Base Classes**

```python
class ISAError(Exception):
    def __init__(self, message: str, location: Optional[ErrorLocation] = None, 
                 suggestion: Optional[str] = None):
        """Base exception for ISA-related errors."""

class ErrorLocation:
    def __init__(self, line: int, column: int, file: Optional[str] = None, 
                 context: Optional[str] = None):
        """Error location context."""
```

**Specific Error Types**

```python
class ISALoadError(ISAError):
    """Raised when ISA definition loading fails."""

class ISAValidationError(ISAError):
    """Raised when ISA definition validation fails."""

class ParseError(ISAError):
    """Raised during assembly parsing."""

class SymbolError(ISAError):
    """Raised for symbol resolution issues."""

class AssemblerError(ISAError):
    """Raised during assembly process."""

class DisassemblerError(ISAError):
    """Raised during disassembly process."""

class BitUtilsError(ISAError):
    """Raised for bit manipulation errors."""
```

**Error Reporter**

```python
class ErrorReporter:
    def __init__(self, max_errors: int = 100):
        """Initialize error reporter with maximum error limit."""
    
    def add_error(self, error: ISAError):
        """Add error to collection."""
    
    def add_warning(self, message: str, location: Optional[ErrorLocation] = None):
        """Add warning to collection."""
    
    def has_errors(self) -> bool:
        """Check if any errors exist."""
    
    def has_warnings(self) -> bool:
        """Check if any warnings exist."""
    
    def format_errors(self) -> str:
        """Format all errors as text."""
    
    def format_warnings(self) -> str:
        """Format all warnings as text."""
    
    def format_summary(self) -> str:
        """Format error/warning summary."""
    
    def raise_if_errors(self):
        """Raise first error if any exist."""
```

### Command Line Interface

#### CLI (`isa_xform.cli`)

##### Main Functions

```python
def main():
    """Main CLI entry point."""

def validate_command(args):
    """Handle ISA validation command."""

def parse_command(args):
    """Handle assembly parsing command."""

def assemble_command(args):
    """Handle assembly command."""

def disassemble_command(args):
    """Handle disassembly command."""

def list_isas_command(args):
    """Handle list ISAs command."""
```

## Usage Examples

### Basic ISA Loading

```python
from isa_xform.core.isa_loader import ISALoader

# Load built-in ISA
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")

# Load custom ISA from file
custom_isa = loader.load_isa_from_file("my_isa.json")

# List available ISAs
available = loader.list_available_isas()
print("Available ISAs:", available)
```

### Assembly Parsing

```python
from isa_xform.core.parser import Parser
from isa_xform.core.isa_loader import ISALoader

# Load ISA and create parser
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")
parser = Parser(isa_def)

# Parse assembly code
source_code = """
start:
    ADD $r1, $r2, $r3
    JMP end
end:
    NOP
"""

nodes = parser.parse(source_code, "example.s")
for node in nodes:
    print(f"{type(node).__name__}: {node}")
```

### Complete Assembly Workflow

```python
from isa_xform.core.isa_loader import ISALoader
from isa_xform.core.parser import Parser
from isa_xform.core.assembler import Assembler
from isa_xform.utils.error_handling import ErrorReporter

# Setup components
loader = ISALoader()
isa_def = loader.load_isa("simple_risc")
parser = Parser(isa_def)
assembler = Assembler(isa_def)
error_reporter = ErrorReporter()

try:
    # Parse source code
    nodes = parser.parse(source_code, "program.s")
    
    # Assemble to machine code
    result = assembler.assemble(nodes)
    
    # Access results
    machine_code = result.machine_code
    symbols = result.symbol_table.symbols
    
    print(f"Generated {len(machine_code)} bytes of machine code")
    print(f"Defined {len(symbols)} symbols")

except Exception as e:
    error_reporter.add_error(e)
    print(error_reporter.format_errors())
```

### Disassembly Workflow

```python
from isa_xform.core.disassembler import Disassembler

# Create disassembler
disassembler = Disassembler(isa_def)

# Read binary file
with open("program.bin", "rb") as f:
    machine_code = f.read()

# Disassemble
result = disassembler.disassemble(machine_code, start_address=0x1000)

# Format output
assembly_text = disassembler.format_disassembly(
    result, 
    include_addresses=True,
    include_machine_code=True
)
print(assembly_text)
```

### Symbol Table Operations

```python
from isa_xform.core.symbol_table import SymbolTable, SymbolType

# Create symbol table
symbols = SymbolTable()

# Define symbols
main_symbol = symbols.define_symbol("main", 0x1000, SymbolType.LABEL)
data_symbol = symbols.define_symbol("buffer", 0x2000, SymbolType.DATA)

# Resolve symbols
main_address = symbols.resolve_symbol("main")
print(f"Main function at: 0x{main_address:04X}")

# List symbols by type
labels = symbols.list_symbols(SymbolType.LABEL)
print(f"Found {len(labels)} labels")
```

### Bit Manipulation

```python
from isa_xform.utils.bit_utils import *

# Extract instruction fields
opcode = extract_bits(0x12345678, 31, 28)  # Extract bits 31:28
register = extract_bits(0x12345678, 27, 24)  # Extract bits 27:24

# Build instruction
instruction = 0
instruction = set_bits(instruction, 31, 28, 0x1)  # Set opcode
instruction = set_bits(instruction, 27, 24, 0x2)  # Set register

# Sign extend immediate
immediate = sign_extend(0xFF, 8, 16)  # Extend 8-bit to 16-bit

# Alignment operations
aligned_addr = align_up(0x1003, 4)  # Align to 4-byte boundary
```

### Error Handling

```python
from isa_xform.utils.error_handling import *

# Create error reporter
reporter = ErrorReporter(max_errors=50)

# Add errors with context
location = ErrorLocation(line=15, column=20, file="main.s", 
                        context="LDI $r1, #256")
error = AssemblerError("Immediate value too large", location, 
                      "Use value 0-255 or different instruction")
reporter.add_error(error)

# Add warnings
reporter.add_warning("Deprecated syntax", location)

# Check and report
if reporter.has_errors():
    print("Compilation failed!")
    print(reporter.format_summary())
    print(reporter.format_errors())

if reporter.has_warnings():
    print("Warnings:")
    print(reporter.format_warnings())
```

## Advanced Usage

### Custom ISA Definition

```python
# Define custom ISA programmatically
from isa_xform.core.isa_loader import ISADefinition, Instruction, Register

isa_def = ISADefinition("CustomISA", "1.0")
isa_def.word_size = 16
isa_def.instruction_size = 16
isa_def.endianness = "big"

# Add registers
isa_def.registers["R0"] = Register("R0", 16, ["ZERO"], "Zero register")
isa_def.registers["R1"] = Register("R1", 16, ["TMP"], "Temporary register")

# Add instructions
add_instr = Instruction("ADD", "0001")
add_instr.encoding = {
    "fields": [
        {"name": "opcode", "bits": "15:12", "value": "0001"},
        {"name": "rd", "bits": "11:8", "type": "register"},
        {"name": "rs1", "bits": "7:4", "type": "register"},
        {"name": "rs2", "bits": "3:0", "type": "register"}
    ]
}
isa_def.instructions.append(add_instr)
```

### Batch Processing

```python
import os
from pathlib import Path

def assemble_directory(directory: str, isa_name: str):
    """Assemble all .s files in directory."""
    loader = ISALoader()
    isa_def = loader.load_isa(isa_name)
    parser = Parser(isa_def)
    assembler = Assembler(isa_def)
    reporter = ErrorReporter()
    
    for asm_file in Path(directory).glob("*.s"):
        try:
            with open(asm_file, 'r') as f:
                source = f.read()
            
            nodes = parser.parse(source, str(asm_file))
            result = assembler.assemble(nodes)
            
            # Write binary output
            bin_file = asm_file.with_suffix(".bin")
            with open(bin_file, 'wb') as f:
                f.write(result.machine_code)
            
            print(f"Assembled {asm_file} -> {bin_file}")
            
        except Exception as e:
            reporter.add_error(e)
    
    if reporter.has_errors():
        print("Batch assembly completed with errors:")
        print(reporter.format_errors())
```

### Performance Optimization

```python
# Pre-build lookup tables for large batch processing
class OptimizedAssembler(Assembler):
    def __init__(self, isa_definition):
        super().__init__(isa_definition)
        self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Pre-build instruction and register lookup tables."""
        self.instruction_lookup = {
            instr.mnemonic.upper(): instr 
            for instr in self.isa_definition.instructions
        }
        self.register_lookup = {
            reg.name.upper(): reg 
            for reg in self.isa_definition.registers.values()
        }
```

## Best Practices

### Error Handling

1. Always use try-except blocks around component operations
2. Collect multiple errors when possible instead of failing fast
3. Provide context information (file, line, column) in errors
4. Use appropriate error types for different failure modes
5. Include helpful suggestions in error messages

### Performance

1. Reuse ISA definitions across multiple operations
2. Use single-pass assembly when forward references aren't needed
3. Pre-build lookup tables for batch processing
4. Stream large files instead of loading entirely into memory
5. Cache parsed ISA definitions for repeated use

### Memory Management

1. Clear symbol tables between independent assemblies
2. Use appropriate data structures for large symbol tables
3. Stream process large machine code files
4. Release AST nodes after assembly completes
5. Monitor memory usage for long-running processes 