"""
Command-line interface for py-isa-xform
"""

import sys
import click
from pathlib import Path
from typing import Optional

from .core.isa_loader import ISALoader
from .core.parser import Parser, LabelNode, InstructionNode, DirectiveNode, CommentNode
from .core.symbol_table import SymbolTable
from .utils.error_handling import ISAError, ErrorReporter


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    py-isa-xform: A comprehensive ISA transformation toolkit
    
    This tool provides assembler and disassembler capabilities for custom instruction sets.
    """
    pass


@main.command()
@click.option('--isa', '-i', required=True, help='ISA name or path to ISA definition file')
@click.option('--input', '-f', required=True, type=click.Path(exists=True), help='Input assembly file')
@click.option('--output', '-o', type=click.Path(), help='Output binary file (default: input.bin)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--list-symbols', is_flag=True, help='List all symbols after assembly')
def assemble(isa: str, input: str, output: Optional[str], verbose: bool, list_symbols: bool):
    """
    Assemble assembly code to machine code
    """
    try:
        # Load ISA
        loader = ISALoader()
        if Path(isa).exists():
            isa_def = loader.load_isa_from_file(isa)
        else:
            isa_def = loader.load_isa(isa)
        
        if verbose:
            click.echo(f"Loaded ISA: {isa_def.name} v{isa_def.version}")
            click.echo(f"Word size: {isa_def.word_size} bits")
            click.echo(f"Endianness: {isa_def.endianness}")
            click.echo(f"Instructions: {len(isa_def.instructions)}")
        
        # Read input file
        input_path = Path(input)
        with open(input_path, 'r') as f:
            assembly_text = f.read()
        
        if verbose:
            click.echo(f"Read assembly file: {input_path}")
        
        # Parse assembly
        parser = Parser(isa_def)
        try:
            ast_nodes = parser.parse(assembly_text, str(input_path))
            if verbose:
                click.echo(f"Parsed {len(ast_nodes)} statements")
        except Exception as e:
            click.echo(f"Parse error: {e}", err=True)
            sys.exit(1)
        
        # Create symbol table
        symbol_table = SymbolTable()
        
        # First pass: collect symbols
        current_address = 0
        for node in ast_nodes:
            if isinstance(node, LabelNode):
                symbol_table.set_current_address(current_address)
                symbol_table.define_label(node.name, node.line, node.column, node.file)
                if verbose:
                    click.echo(f"Defined label '{node.name}' at address {current_address}")
            elif isinstance(node, InstructionNode):
                # Estimate instruction size (simplified)
                instruction_size = isa_def.instruction_size // 8
                current_address += instruction_size
            elif isinstance(node, DirectiveNode):
                if node.name == '.org':
                    if node.arguments:
                        try:
                            current_address = int(node.arguments[0], 0)
                            symbol_table.set_current_address(current_address)
                            if verbose:
                                click.echo(f"Set origin to {current_address}")
                        except ValueError:
                            click.echo(f"Invalid address in .org directive: {node.arguments[0]}", err=True)
                elif node.name == '.word':
                    current_address += 2
                elif node.name == '.byte':
                    current_address += 1
        
        if verbose:
            click.echo(f"First pass complete. Code size: {current_address} bytes")
        
        # Second pass: generate code (simplified)
        output_path = Path(output) if output else input_path.with_suffix('.bin')
        
        # For now, just create a placeholder binary file
        with open(output_path, 'wb') as f:
            # Write a simple header
            f.write(b'ISA\x00')  # Magic number
            f.write(len(isa_def.name).to_bytes(1, 'little'))
            f.write(isa_def.name.encode('ascii'))
            f.write(current_address.to_bytes(4, 'little'))
            
            # Write placeholder code
            f.write(b'\x00' * current_address)
        
        click.echo(f"Assembly complete. Output: {output_path}")
        
        # List symbols if requested
        if list_symbols:
            click.echo("\nSymbols:")
            for name, symbol in symbol_table.symbols.items():
                status = "DEFINED" if symbol.defined else "UNDEFINED"
                click.echo(f"  {name}: {symbol.value} ({status})")
        
        # Show statistics
        stats = symbol_table.get_statistics()
        if verbose:
            click.echo(f"\nStatistics:")
            click.echo(f"  Total symbols: {stats['total_symbols']}")
            click.echo(f"  Defined symbols: {stats['defined_symbols']}")
            click.echo(f"  Referenced symbols: {stats['referenced_symbols']}")
        
    except ISAError as e:
        click.echo(f"ISA error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--isa', '-i', required=True, help='ISA name or path to ISA definition file')
@click.option('--input', '-f', required=True, type=click.Path(exists=True), help='Input binary file')
@click.option('--output', '-o', type=click.Path(), help='Output assembly file (default: input.s)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def disassemble(isa: str, input: str, output: Optional[str], verbose: bool):
    """
    Disassemble machine code to assembly
    """
    try:
        # Load ISA
        loader = ISALoader()
        if Path(isa).exists():
            isa_def = loader.load_isa_from_file(isa)
        else:
            isa_def = loader.load_isa(isa)
        
        if verbose:
            click.echo(f"Loaded ISA: {isa_def.name} v{isa_def.version}")
        
        # Read input file
        input_path = Path(input)
        with open(input_path, 'rb') as f:
            binary_data = f.read()
        
        if verbose:
            click.echo(f"Read binary file: {input_path} ({len(binary_data)} bytes)")
        
        # Simple disassembly (placeholder)
        output_path = Path(output) if output else input_path.with_suffix('.s')
        
        with open(output_path, 'w') as f:
            f.write(f"; Disassembled from {input_path}\n")
            f.write(f"; ISA: {isa_def.name} v{isa_def.version}\n")
            f.write(f"; Word size: {isa_def.word_size} bits\n")
            f.write(f"; Endianness: {isa_def.endianness}\n\n")
            
            # Write placeholder disassembly
            f.write("; Disassembly not yet implemented\n")
            f.write("; This is a placeholder output\n\n")
            
            # List available instructions
            f.write("; Available instructions:\n")
            for instr in isa_def.instructions:
                f.write(f";   {instr.mnemonic}: {instr.description}\n")
        
        click.echo(f"Disassembly complete. Output: {output_path}")
        
    except ISAError as e:
        click.echo(f"ISA error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--isa-file', '-f', type=click.Path(exists=True), help='ISA definition file to validate')
@click.option('--isa-name', '-n', help='Built-in ISA name to validate')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def validate(isa_file: Optional[str], isa_name: Optional[str], verbose: bool):
    """
    Validate an ISA definition
    """
    if not isa_file and not isa_name:
        click.echo("Error: Must specify either --isa-file or --isa-name", err=True)
        sys.exit(1)
    
    try:
        loader = ISALoader()
        
        if isa_file:
            isa_def = loader.load_isa_from_file(isa_file)
            source = f"file: {isa_file}"
        else:
            assert isa_name is not None  # This is guaranteed by the click validation
            isa_def = loader.load_isa(isa_name)
            source = f"built-in ISA: {isa_name}"
        
        click.echo(f"Validating {source}")
        click.echo(f"✓ ISA loaded successfully")
        
        if verbose:
            click.echo(f"  Name: {isa_def.name}")
            click.echo(f"  Version: {isa_def.version}")
            click.echo(f"  Description: {isa_def.description}")
            click.echo(f"  Word size: {isa_def.word_size} bits")
            click.echo(f"  Endianness: {isa_def.endianness}")
            click.echo(f"  Instruction size: {isa_def.instruction_size} bits")
            
            # Count registers
            total_registers = sum(len(regs) for regs in isa_def.registers.values())
            click.echo(f"  Registers: {total_registers}")
            click.echo(f"  Instructions: {len(isa_def.instructions)}")
            
            # List register categories
            for category, regs in isa_def.registers.items():
                click.echo(f"    {category}: {len(regs)} registers")
        
        # Basic validation
        errors = []
        
        # Check for duplicate instruction mnemonics
        mnemonics = [instr.mnemonic for instr in isa_def.instructions]
        duplicates = [m for m in set(mnemonics) if mnemonics.count(m) > 1]
        if duplicates:
            errors.append(f"Duplicate instruction mnemonics: {duplicates}")
        
        # Check for duplicate register names
        all_registers = []
        for reg_list in isa_def.registers.values():
            all_registers.extend(reg_list)
        
        reg_names = [reg.name for reg in all_registers]
        duplicates = [r for r in set(reg_names) if reg_names.count(r) > 1]
        if duplicates:
            errors.append(f"Duplicate register names: {duplicates}")
        
        if errors:
            click.echo("✗ Validation failed:")
            for error in errors:
                click.echo(f"  - {error}")
            sys.exit(1)
        else:
            click.echo("✓ Validation passed")
        
    except ISAError as e:
        click.echo(f"✗ Validation failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def list_isas(verbose: bool):
    """
    List available ISA definitions
    """
    try:
        loader = ISALoader()
        isas = loader.list_available_isas()
        
        if not isas:
            click.echo("No built-in ISA definitions found")
            return
        
        click.echo("Available ISA definitions:")
        for isa in isas:
            click.echo(f"  {isa}")
            
            if verbose:
                try:
                    isa_def = loader.load_isa(isa)
                    click.echo(f"    Description: {isa_def.description}")
                    click.echo(f"    Word size: {isa_def.word_size} bits")
                    click.echo(f"    Instructions: {len(isa_def.instructions)}")
                except Exception as e:
                    click.echo(f"    Error loading: {e}")
        
    except Exception as e:
        click.echo(f"Error listing ISAs: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--isa', '-i', required=True, help='ISA name or path to ISA definition file')
@click.option('--input', '-f', required=True, type=click.Path(exists=True), help='Input assembly file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def parse(isa: str, input: str, verbose: bool):
    """
    Parse assembly code and show AST
    """
    try:
        # Load ISA
        loader = ISALoader()
        if Path(isa).exists():
            isa_def = loader.load_isa_from_file(isa)
        else:
            isa_def = loader.load_isa(isa)
        
        if verbose:
            click.echo(f"Loaded ISA: {isa_def.name}")
        
        # Read input file
        input_path = Path(input)
        with open(input_path, 'r') as f:
            assembly_text = f.read()
        
        # Parse assembly
        parser = Parser(isa_def)
        ast_nodes = parser.parse(assembly_text, str(input_path))
        
        click.echo(f"Parsed {len(ast_nodes)} statements:")
        click.echo()
        
        for i, node in enumerate(ast_nodes):
            click.echo(f"{i+1:3d}: ", nl=False)
            
            if isinstance(node, LabelNode):
                click.echo(f"LABEL: {node.name}")
            elif isinstance(node, InstructionNode):
                operands = [f"{op.type}:{op.value}" for op in node.operands]
                click.echo(f"INSTR: {node.mnemonic} {' '.join(operands)}")
            elif isinstance(node, DirectiveNode):
                args = ' '.join(node.arguments)
                click.echo(f"DIRECTIVE: {node.name} {args}")
            elif isinstance(node, CommentNode):
                click.echo(f"COMMENT: {node.text}")
            else:
                click.echo(f"UNKNOWN: {node}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 