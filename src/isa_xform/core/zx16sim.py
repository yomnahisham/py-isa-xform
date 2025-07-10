import sys
import struct
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from isa_xform.core.disassembler import Disassembler, DisassembledInstruction
from isa_xform.core.isa_loader import ISADefinition, ISALoader
from isa_xform.core.symbol_table import SymbolTable
from isa_xform.core.modular_sim import Simulator
import threading
from isa_xform.core.graphics import run_graphics

def run_simulator(simulator):
    simulator.run(True)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <machine_code_file>", file=sys.stderr)
        sys.exit(1)


    filename = sys.argv[1]
    print(f"Start: Loading {filename}")
    
    # Check if file exists
    if not Path(filename).exists():
        print(f"Error: File '{filename}' not found", file=sys.stderr)
        sys.exit(1)
    
    isa_loader = ISALoader();
    symbol_table = SymbolTable();
    disassembler = Disassembler(isa_loader.load_isa("zx16"), symbol_table)
    simulator = Simulator(isa_loader.load_isa("zx16"), symbol_table, disassembler)
    if not simulator.load_memory_from_file(filename):
        sys.exit(1)

    sim_thread = threading.Thread(target=run_simulator, args=(simulator,), daemon=True)
    sim_thread.start()

    # ✅ Run graphics on the main thread (must be main thread on macOS!)
    run_graphics(simulator)
    return 0


if __name__ == "__main__":
    main()