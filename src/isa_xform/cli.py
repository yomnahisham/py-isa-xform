"""
Command-line interface for xform
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional, Any, Tuple
import json

from .core.isa_loader import ISALoader
from .core.parser import Parser, LabelNode, InstructionNode, DirectiveNode, CommentNode
from .core.assembler import Assembler
from .core.disassembler import Disassembler
from .core.symbol_table import SymbolTable
from .utils.error_handling import ISAError, ErrorReporter, ISALoadError, ParseError, AssemblerError, DisassemblerError


def load_isa_smart(isa_arg: str) -> Any:
    """Load ISA definition, handling both file paths and names"""
    loader = ISALoader()
    isa_path = Path(isa_arg)
    if isa_path.exists() or isa_path.is_absolute():
        return loader.load_isa_from_file(isa_arg)
    else:
        return loader.load_isa(isa_arg)


def parse_data_regions(data_regions_arg: Optional[List[str]]) -> Optional[List[Tuple[int, int]]]:
    """Parse data regions from command line arguments
    
    Args:
        data_regions_arg: List of strings like ["0x0-0xA", "0x100-0x200"]
    
    Returns:
        List of (start_addr, end_addr) tuples, or None if no regions specified
    """
    if not data_regions_arg:
        return None
    
    regions = []
    for region_str in data_regions_arg:
        try:
            if '-' not in region_str:
                raise ValueError(f"Invalid data region format: {region_str}. Expected 'start-end'")
            
            start_str, end_str = region_str.split('-', 1)
            start_addr = int(start_str, 0)  # Auto-detect base
            end_addr = int(end_str, 0)      # Auto-detect base
            
            if start_addr >= end_addr:
                raise ValueError(f"Invalid data region: start ({start_addr}) must be less than end ({end_addr})")
            
            regions.append((start_addr, end_addr))
            
        except ValueError as e:
            raise ValueError(f"Failed to parse data region '{region_str}': {e}")
    
    return regions


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="~xform -: Full Ecosystem for ISA Transformation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s assemble --isa simple_risc --input main.s --output program.bin
  %(prog)s disassemble --isa simple_risc --input program.bin --output disassembled.s
  %(prog)s disassemble --isa zx16 --input program.bin --output disassembled.s --start-address 0x20
  %(prog)s disassemble --isa zx16 --input program.bin --output disassembled.s --data-regions 0x100-0x200
  %(prog)s validate --isa simple_risc
  %(prog)s list-isas

Data Region Detection:
  The disassembler automatically detects data regions based on your ISA's memory layout
  when --data-regions is not specified. This includes interrupt vectors, data sections,
  and MMIO regions defined in your ISA. Use --data-regions to override automatic detection.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Assemble command
    assemble_parser = subparsers.add_parser('assemble', help='Assemble source files to machine code')
    assemble_parser.add_argument('--isa', required=True, help='ISA definition file or name')
    assemble_parser.add_argument('--input', required=True, nargs='+', help='Input assembly files')
    assemble_parser.add_argument('--output', required=True, help='Output binary file')
    assemble_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    assemble_parser.add_argument('--list-symbols', action='store_true', help='List resolved symbols')
    assemble_parser.add_argument('--raw', action='store_true', help='Output raw binary with no header (for legacy/bootloader use)')
    
    # Disassemble command
    disassemble_parser = subparsers.add_parser('disassemble', 
                                              help='Disassemble machine code to assembly with automatic data region detection',
                                              description='Disassemble binary files to assembly code. Automatically detects data regions based on ISA memory layout unless --data-regions is specified.',
                                              formatter_class=argparse.RawDescriptionHelpFormatter,
                                              epilog="""
Disassembly Modes:
  Raw Mode (default): Shows only real hardware instructions as encoded in the binary.
  Smart Mode (--smart): Reconstructs pseudo-instructions using patterns from the ISA definition.

Data Region Detection:
  The disassembler automatically detects data regions based on your ISA's memory layout
  when --data-regions is not specified. This includes:
  • Interrupt vectors (treated as data)
  • Data sections (treated as data)
  • MMIO regions (treated as data)
  • Code sections (treated as instructions)

  Use --data-regions to override automatic detection with custom regions.

Examples:
  # Raw disassembly (hardware instructions only) (default)
  %(prog)s --isa zx16 --input program.bin --output program.s

  # Smart disassembly with pseudo-instruction reconstruction
  %(prog)s --isa zx16 --input program.bin --output program.s --smart

  # Manual override with custom data regions
  %(prog)s --isa zx16 --input program.bin --output program.s --data-regions 0x100-0x200

  # Start disassembly at specific address
  %(prog)s --isa zx16 --input program.bin --output program.s --start-address 0x20
                                              """)
    disassemble_parser.add_argument('--isa', required=True, help='ISA definition file or name')
    disassemble_parser.add_argument('--input', required=True, help='Input binary file')
    disassemble_parser.add_argument('--output', required=True, help='Output assembly file')
    disassemble_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    disassemble_parser.add_argument('--debug', action='store_true', help='Show detailed PC progression and mode switches')
    disassemble_parser.add_argument('--show-addresses', action='store_true', help='Show addresses in output')
    disassemble_parser.add_argument('--show-machine-code', action='store_true', help='Show machine code in output')
    disassemble_parser.add_argument('--start-address', type=lambda x: int(x, 0), default=0, help='Starting address for disassembly')
    disassemble_parser.add_argument('--data-regions', nargs='+', 
                                   help='Data regions as start-end pairs (e.g., 0x0-0xA 0x100-0x200). '
                                        'If not specified, automatically detects data regions based on ISA memory layout.')
    disassemble_parser.add_argument('--smart', action='store_true', 
                                   help='Reconstruct pseudo-instructions using patterns from the ISA definition')
    disassemble_parser.add_argument('--reconstruct-labels', action='store_true',
                                   help='Reconstruct labels in branch and jump instructions (default: show raw addresses)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate ISA definition')
    validate_parser.add_argument('--isa', required=True, help='ISA definition file or name')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse assembly to AST')
    parse_parser.add_argument('--isa', required=True, help='ISA definition file or name')
    parse_parser.add_argument('--input', required=True, help='Input assembly file')
    parse_parser.add_argument('--output', help='Output AST file (JSON)')
    parse_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # List ISAs command
    list_parser = subparsers.add_parser('list-isas', help='List available ISA definitions')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Scaffold command
    scaffold_parser = subparsers.add_parser('scaffold', help='Generate a new ISA scaffold definition')
    scaffold_parser.add_argument('--name', required=True, help='Name of the ISA')
    scaffold_parser.add_argument('--instructions', required=True, help='Comma-separated list of instructions to include')
    scaffold_parser.add_argument('--directives', help='Comma-separated list of directives to include')
    scaffold_parser.add_argument('--word-size', type=int, default=16, help='Word size in bits (default: 16)')
    scaffold_parser.add_argument('--instruction-size', type=int, default=16, help='Instruction size in bits (default: 16)')
    scaffold_parser.add_argument('--register-count', type=int, default=8, help='Number of general-purpose registers (default: 8)')
    scaffold_parser.add_argument('--registers', help='Comma-separated list of register names (overrides --register-count)')
    scaffold_parser.add_argument('--output', help='Output file path (default: {name}_isa.json)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'assemble':
            return assemble_command(args)
        elif args.command == 'disassemble':
            return disassemble_command(args)
        elif args.command == 'validate':
            return validate_command(args)
        elif args.command == 'parse':
            return parse_command(args)
        elif args.command == 'list-isas':
            return list_isas_command(args)
        elif args.command == 'scaffold':
            return scaffold_command(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except ISAError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
            return 1


def assemble_command(args) -> int:
    """Handle assemble command"""
    error_reporter = ErrorReporter()
    
    try:
        # Load ISA definition
        isa_definition = load_isa_smart(args.isa)
        if args.verbose:
            print(f"Loaded ISA: {isa_definition.name} v{isa_definition.version}")
        
        # Parse all input files
        parser = Parser(isa_definition)
        all_nodes = []
        
        for input_file in args.input:
            if args.verbose:
                print(f"Parsing {input_file}...")
            
            try:
                with open(input_file, 'r') as f:
                    source = f.read()
                
                nodes = parser.parse(source)
                all_nodes.extend(nodes)
                
                if args.verbose:
                    print(f"  Parsed {len(nodes)} nodes")
                    
            except FileNotFoundError:
                error_reporter.add_error(ParseError(f"Input file not found: {input_file}"))
            except Exception as e:
                error_reporter.add_error(ParseError(f"Failed to parse {input_file}: {e}"))
        
        error_reporter.raise_if_errors()
        
        # Assemble
        symbol_table = SymbolTable()
        assembler = Assembler(isa_definition, symbol_table)
        
        if args.verbose:
            print("Assembling...")
        
        assembled_result = assembler.assemble(all_nodes)
        
        # Check for assembly errors
        if not assembled_result.success:
            print("Assembly failed with errors:", file=sys.stderr)
            for error in assembled_result.errors:
                print(f"  Line {error.line_number}: {error.message}", file=sys.stderr)
                if error.instruction:
                    print(f"    Instruction: {error.instruction}", file=sys.stderr)
                if error.operand:
                    print(f"    Operand: {error.operand}", file=sys.stderr)
                if error.expected and error.found:
                    print(f"    Expected: {error.expected}, Found: {error.found}", file=sys.stderr)
                if error.context:
                    print(f"    Context: {error.context}", file=sys.stderr)
            return 1
        
        # Display warnings if any
        if assembled_result.warnings:
            print("Assembly completed with warnings:", file=sys.stderr)
            for warning in assembled_result.warnings:
                print(f"  Line {warning.line_number}: {warning.message}", file=sys.stderr)
        
        machine_code = assembled_result.machine_code
        
        # Check if the assembler already created an ISAX header
        if machine_code.startswith(b'ISAX'):
            # Assembler created ISAX format, use it directly
            final_binary = machine_code
        elif args.raw:
            # Raw binary requested
            final_binary = machine_code
        else:
            # Create legacy ISA binary header format:
            # Magic: "ISA\x01" (4 bytes)
            # ISA name length: 1 byte
            # ISA name: variable length
            # Code size: 4 bytes (little endian)
            # Entry point: 4 bytes (little endian)
            # Machine code follows
            
            isa_name = isa_definition.name.encode('ascii')
            header = bytearray()
            header.extend(b'ISA\x01')  # Magic number
            header.extend(len(isa_name).to_bytes(1, 'little'))  # ISA name length
            header.extend(isa_name)  # ISA name
            header.extend(len(machine_code).to_bytes(4, 'little'))  # Total size
            entry_point = assembled_result.entry_point or 0
            header.extend(entry_point.to_bytes(4, 'little'))  # Entry point
            
            final_binary = header + machine_code
        
        # Write output
        with open(args.output, 'wb') as f:
            f.write(final_binary)
        
        if args.verbose:
            print(f"Generated {len(machine_code)} bytes of machine code")
            print(f"Output written to {args.output}")
        
        # List symbols if requested
        if args.list_symbols:
            print("\nSymbols:")
            for name, symbol in symbol_table.symbols.items():
                print(f"  {name}: 0x{symbol.value:04X} ({symbol.type.value})")
        
        return 0
        
    except ISAError as e:
        error_reporter.add_error(e)
        print(error_reporter.format_errors(), file=sys.stderr)
        return 1


def disassemble_command(args) -> int:
    """Handle disassemble command"""
    error_reporter = ErrorReporter()
    
    try:
        # Load ISA definition
        isa_definition = load_isa_smart(args.isa)
        if args.verbose:
            print(f"Loaded ISA: {isa_definition.name} v{isa_definition.version}")
        
        # Read binary file
        try:
            with open(args.input, 'rb') as f:
                binary_data = f.read()
        except FileNotFoundError:
            error_reporter.add_error(DisassemblerError(f"Input file not found: {args.input}"))
            error_reporter.raise_if_errors()
            return 1
        
        if args.verbose:
            print(f"Read {len(binary_data)} bytes from {args.input}")
        
        # Check for ISA header
        machine_code = binary_data
        entry_point = args.start_address
        
        # Check for ISAX header format (new format)
        if binary_data.startswith(b'ISAX'):
            # Check version to determine parsing
            if len(binary_data) >= 8:
                version = int.from_bytes(binary_data[4:8], 'little')
                
                if version == 2:
                    # ISAX v2 with symbols: [magic][version][entry_point][code_start][code_size][data_start][data_size][symbol_size][code][data][symbols]
                    if len(binary_data) >= 32:  # Minimum header size for v2
                        file_entry_point = int.from_bytes(binary_data[8:12], 'little')
                        code_start = int.from_bytes(binary_data[12:16], 'little')
                        code_size = int.from_bytes(binary_data[16:20], 'little')
                        data_start = int.from_bytes(binary_data[20:24], 'little')
                        data_size = int.from_bytes(binary_data[24:28], 'little')
                        symbol_size = int.from_bytes(binary_data[28:32], 'little')
                        
                        if args.verbose:
                            print(f"ISAX v2 header detected:")
                            print(f"  Entry point: 0x{file_entry_point:X}")
                            print(f"  Code start: 0x{code_start:X}, size: {code_size} bytes")
                            print(f"  Data start: 0x{data_start:X}, size: {data_size} bytes")
                            print(f"  Symbol table size: {symbol_size} bytes")
                            print(f"  Total binary size: {len(binary_data)} bytes")
                        
                        # Use file entry point if not specified
                        if entry_point == 0:
                            entry_point = file_entry_point
                else:
                    # ISAX v1: [magic][entry_point][code_start][code_size][data_start][data_size][code][data]
                    if len(binary_data) >= 24:  # Minimum header size for v1
                        file_entry_point = int.from_bytes(binary_data[4:8], 'little')
                        code_start = int.from_bytes(binary_data[8:12], 'little')
                        code_size = int.from_bytes(binary_data[12:16], 'little')
                        data_start = int.from_bytes(binary_data[16:20], 'little')
                        data_size = int.from_bytes(binary_data[20:24], 'little')
                        
                        if args.verbose:
                            print(f"ISAX v1 header detected:")
                            print(f"  Entry point: 0x{file_entry_point:X}")
                            print(f"  Code start: 0x{code_start:X}, size: {code_size} bytes")
                            print(f"  Data start: 0x{data_start:X}, size: {data_size} bytes")
                            print(f"  Total binary size: {len(binary_data)} bytes")
                        
                        # Use file entry point if not specified
                        if entry_point == 0:
                            entry_point = file_entry_point
            
            # For both v1 and v2, pass the full binary to the disassembler
            machine_code = binary_data
        # Check for old ISA header format
        elif binary_data.startswith(b'ISA\x01'):
            # Has header - extract machine code
            offset = 4  # Magic + version
            if len(binary_data) > offset:
                name_len = binary_data[offset]
                offset += 1 + name_len  # Name length + name
                if len(binary_data) > offset + 8:  # Size + entry point
                    code_size = int.from_bytes(binary_data[offset:offset+4], 'little')
                    file_entry_point = int.from_bytes(binary_data[offset+4:offset+8], 'little')
                    offset += 8
                    # Extract only the code section
                    machine_code = binary_data[offset:offset+code_size]
                    if args.verbose:
                        print(f"Extracted {len(machine_code)} bytes of code from header")
                        print(f"File entry point: 0x{file_entry_point:X}")
                    # Use file entry point if not specified
                    if entry_point == 0:
                        entry_point = file_entry_point
        
        # Parse data regions if specified
        data_regions = None
        if args.data_regions:
            try:
                data_regions = parse_data_regions(args.data_regions)
                if args.verbose and data_regions:
                    print("Data regions:")
                    for start, end in data_regions:
                        print(f"  0x{start:X}-0x{end:X}")
            except ValueError as e:
                error_reporter.add_error(DisassemblerError(f"Invalid data regions: {e}"))
                error_reporter.raise_if_errors()
                return 1
        
        # Disassemble
        try:
            # Calculate the correct start address for disassembly
            # For ISAX format, the disassembler handles the header parsing and uses the correct addresses
            # For legacy format, start from the beginning of the extracted machine code
            if binary_data.startswith(b'ISAX'):
                # ISAX format: pass the full binary, disassembler will handle header parsing
                disassemble_start = 0  # Disassembler will use code_start from header when it detects ISAX
            else:
                # Legacy format: start from beginning of extracted machine code
                disassemble_start = 0
            
            disassembler = Disassembler(isa_definition)
            result = disassembler.disassemble(machine_code, disassemble_start, debug=args.debug, data_regions=data_regions, reconstruct_pseudo=args.smart, reconstruct_labels=args.reconstruct_labels)
            
            # Format output
            output_text = disassembler.format_disassembly(
                result, 
                include_addresses=args.show_addresses,
                include_machine_code=args.show_machine_code,
                reconstruct_pseudo=args.smart,
                reconstruct_labels=args.reconstruct_labels
            )
            
            # Write output
            with open(args.output, 'w') as f:
                f.write(output_text)
            
            if args.verbose:
                print(f"Disassembled {len(result.instructions)} instructions")
                print(f"Found {len(result.data_sections)} data sections")
                print(f"Output written to {args.output}")
            
            return 0
            
        except Exception as e:
            error_reporter.add_error(DisassemblerError(f"Disassembly failed: {e}"))
            error_reporter.raise_if_errors()
            return 1
        
    except ISAError as e:
        error_reporter.add_error(e)
        print(error_reporter.format_errors(), file=sys.stderr)
        return 1


def validate_command(args) -> int:
    """Handle validate command"""
    error_reporter = ErrorReporter()
    
    try:
        # Load ISA definition
        isa_definition = load_isa_smart(args.isa)
        
        print(f"[OK] ISA Definition: {isa_definition.name} v{isa_definition.version}")
        print(f"[OK] Word size: {isa_definition.word_size} bits")
        print(f"[OK] Endianness: {isa_definition.endianness}")
        print(f"[OK] Instruction size: {isa_definition.instruction_size} bits")
        print(f"[OK] Instructions: {len(isa_definition.instructions)}")
        print(f"[OK] Registers: {sum(len(regs) for regs in isa_definition.registers.values())}")
        print(f"[OK] Directives: {len(isa_definition.directives)}")
        
        if args.verbose:
            print("\nInstructions:")
            for instr in isa_definition.instructions:
                print(f"  {instr.mnemonic}: {instr.description}")
            
            print("\nRegisters:")
            for category, registers in isa_definition.registers.items():
                print(f"  {category}:")
                for reg in registers:
                    print(f"    {reg.name}: {reg.description}")
        
        print("\n[OK] ISA definition is valid!")
        return 0
        
    except ISAError as e:
        error_reporter.add_error(e)
        print("[ERROR] ISA definition validation failed:")
        print(error_reporter.format_errors(), file=sys.stderr)
        return 1


def parse_command(args) -> int:
    """Handle parse command"""
    error_reporter = ErrorReporter()
    
    try:
        # Load ISA definition
        isa_definition = load_isa_smart(args.isa)
        if args.verbose:
            print(f"Loaded ISA: {isa_definition.name} v{isa_definition.version}")
        
        # Parse input file
        parser = Parser(isa_definition)
        
        with open(args.input, 'r') as f:
            source = f.read()
        
        nodes = parser.parse(source)
        
        if args.verbose:
            print(f"Parsed {len(nodes)} nodes")
        
        # Output AST
        if args.output:
            ast_data = []
            for node in nodes:
                node_dict = {
                    'type': type(node).__name__,
                    'line': getattr(node, 'line', 0),
                    'column': getattr(node, 'column', 0)
                }
                if isinstance(node, LabelNode):
                    node_dict['name'] = node.name
                if isinstance(node, InstructionNode):
                    node_dict['mnemonic'] = node.mnemonic
                    node_dict['operands'] = [str(op) for op in node.operands]
                if isinstance(node, DirectiveNode):
                    node_dict['name'] = node.name
                    node_dict['arguments'] = node.arguments
                if isinstance(node, CommentNode):
                    node_dict['text'] = node.text
                ast_data.append(node_dict)
            
            with open(args.output, 'w') as f:
                json.dump(ast_data, f, indent=2)
            
            if args.verbose:
                print(f"AST written to {args.output}")
        else:
            # Print to stdout
            for node in nodes:
                print(node)
        
        return 0
        
    except ISAError as e:
        error_reporter.add_error(e)
        print(error_reporter.format_errors(), file=sys.stderr)
        return 1


def list_isas_command(args) -> int:
    """Handle list-isas command"""
    try:
        loader = ISALoader()
        isa_names = loader.list_available_isas()
        
        if not isa_names:
            print("No ISA definitions found")
            return 1
        
        print("Available ISA definitions:")
        for isa_name in sorted(isa_names):
            try:
                isa_definition = loader.load_isa(isa_name)
                print(f"  {isa_name}: {isa_definition.name} v{isa_definition.version}")
                if args.verbose:
                    print(f"    Description: {isa_definition.description}")
                    print(f"    Word size: {isa_definition.word_size} bits")
                    print(f"    Instructions: {len(isa_definition.instructions)}")
                    print()
            except Exception as e:
                print(f"  {isa_name}: Error loading ({e})")
        
        return 0
        
    except Exception as e:
        print(f"Error listing ISAs: {e}", file=sys.stderr)
        return 1


def scaffold_command(args) -> int:
    """Handle scaffold command by invoking the scaffold generator module"""
    import subprocess
    import shlex
    cmd = [sys.executable, '-m', 'src.isa_xform.core.isa_scaffold',
           '--name', args.name,
           '--instructions', args.instructions]
    if args.directives:
        cmd += ['--directives', args.directives]
    if args.word_size:
        cmd += ['--word-size', str(args.word_size)]
    if args.instruction_size:
        cmd += ['--instruction-size', str(args.instruction_size)]
    if args.register_count:
        cmd += ['--register-count', str(args.register_count)]
    if args.registers:
        cmd += ['--registers', args.registers]
    if args.output:
        cmd += ['--output', args.output]
    print('Running:', ' '.join(shlex.quote(c) for c in cmd))
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main()) 