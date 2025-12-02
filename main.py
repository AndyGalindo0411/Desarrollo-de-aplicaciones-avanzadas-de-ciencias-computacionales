import argparse
from pathlib import Path
import sys

from parser import parse, get_function_directory, get_global_var_table
from tabla_symbolos import SemanticError
from intermediate import dump_quads


def print_symbols():
    func_dir = get_function_directory()
    globals_tbl = get_global_var_table()

    print("=== VARIABLES GLOBALES ===")
    gvars = globals_tbl.all_variables()
    if not gvars:
        print("  (ninguna)")
    else:
        for name, info in gvars.items():
            print(f"  {name} : {info.var_type} @ {info.address}")

    print("\n=== FUNCIONES ===")
    funcs = func_dir.all_functions()
    if not funcs:
        print("  (ninguna)")
        return

    for fname, finfo in funcs.items():
        print(f"\nFunción: {fname}")
        print(f"  Retorno: {finfo.return_type}")
        if finfo.parameters:
            print("  Parámetros:")
            for (pname, ptype, paddr) in finfo.parameters:
                print(f"    {pname} : {ptype} @ {paddr}")
        else:
            print("  Parámetros: (ninguno)")

        vdict = finfo.var_table.all_variables()
        if vdict:
            print("  Vars locales:")
            for vname, vinfo in vdict.items():
                rol = "parámetro" if vinfo.is_param else "local"
                print(f"    {vname} : {vinfo.var_type} ({rol}) @ {vinfo.address}")
        else:
            print("  Vars locales: (ninguna)")


def main(argv=None):
    argp = argparse.ArgumentParser(description="Frontend Patito")
    argp.add_argument("fuente", help="Archivo con código Patito")
    argp.add_argument("--ast", action="store_true", help="Imprimir AST resultante")
    argp.add_argument("--symbols", action="store_true", help="Imprimir tablas de símbolos")
    argp.add_argument("--quads", action="store_true", help="Imprimir cuádruplos generados")
    args = argp.parse_args(argv)

    src_path = Path(args.fuente)
    if not src_path.exists():
        print(f"No se encontró el archivo: {src_path}", file=sys.stderr)
        sys.exit(1)

    try:
        code = src_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"No pude leer el archivo: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        ast = parse(code)
        print("Parseo exitoso")
        if args.ast:
            print("\n=== AST ===")
            print(ast)
        if args.symbols:
            print("\n=== SÍMBOLOS ===")
            print_symbols()
        if args.quads:
            print("\n=== CUÁDRUPLOS ===")
            dump_quads()
    except SemanticError as e:
        print(f"Error semántico: {e}", file=sys.stderr)
        sys.exit(1)
    except SyntaxError as e:
        print(f"Error de sintaxis: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
