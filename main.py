import argparse
from pathlib import Path
import sys

from parser import parse, get_function_directory
from intermediate import quads, const_table
from tabla_symbolos import SemanticError
from VM_Patito import VirtualMachine

def print_const_table() -> None:
    print("TABLA DE CONSTANTES")
    if not const_table:
        print("  (ERROR)")
        return
    for (_tipo, valor), direccion in sorted(const_table.items(), key=lambda x: x[1]):
        print(f"  {valor} : {direccion}")


def print_quads() -> None:
    print("LISTA DE DIRECCIONES")
    if not quads:
        print("  (ERROR)")
        return
    for i, (op, op1, op2, res) in enumerate(quads):
        op1_str = str(op1) if op1 is not None else "None"
        op2_str = str(op2) if op2 is not None else "None"
        res_str = str(res) if res is not None else "None"
        print(f"  {i}: ({op}, {op1_str}, {op2_str}, {res_str})")


def run_file(src_path: Path) -> None:
    print(f"\n=== COMPILANDO Y EJECUTANDO {src_path} ===")
    if not src_path.exists():
        print(f"No se encontro el archivo: {src_path}", file=sys.stderr)
        return
    try:
        code = src_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"No se pudo leer '{src_path}': {e}", file=sys.stderr)
        return

    try:
        parse(code)
        print("RESULTADOS")
        print_const_table()
        print_quads()
        print("-" * 42)
        print("Maquina Virtual")
        vm = VirtualMachine(quads, const_table, get_function_directory())
        vm.run()
    except (SemanticError, SyntaxError) as e:
        print("ERROR")
        print(e, file=sys.stderr)
    except Exception as e:
        import traceback
        print("\n--- ERROR INESPERADO ---")
        print(e, file=sys.stderr)
        traceback.print_exc()


def main(argv=None) -> None:
    argp = argparse.ArgumentParser(description="Runner Patito")
    argp.add_argument(
        "--test",
        default="tests/fibonacci_recursivo.txt",
        help="Ruta al archivo Patito a compilar/ejecutar",
    )
    args = argp.parse_args(argv)
    run_file(Path(args.test))


if __name__ == "__main__":
    main()
