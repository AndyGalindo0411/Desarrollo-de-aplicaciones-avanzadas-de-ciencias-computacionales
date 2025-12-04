import argparse
import sys
from pathlib import Path

from parser import parse, get_function_directory, get_global_var_table
from tabla_symbolos import SemanticError
from intermediate import dump_quads, quads, const_table
from VM_Patito import VirtualMachine


def compile_and_execute(
    code: str,
    label: str = "fuente",
    show_ast: bool = False,
    show_symbols: bool = False,
    show_quads: bool = False,
    show_consts: bool = False,
    verbose: bool = False,
) -> None:
    if verbose:
        print(f"\n=== Compilando {label} ===")
    ast = parse(code)

    if verbose:
        print("\n--- COMPILACION EXITOSA ---")

    if show_ast and verbose:
        print("\n=== AST ===")
        print(ast)

    if show_symbols and verbose:
        print("\n=== SIMBOLOS ===")
        print_symbols()

    if show_consts and verbose:
        print("\n--- TABLA DE CONSTANTES (VALOR -> DIRECCION) ---")
        if const_table:
            for valor, direccion in sorted(const_table.items(), key=lambda x: x[1]):
                print(f"  {valor} : {direccion}")
        else:
            print("  (vacia)")

    if show_quads and verbose:
        print("\n--- LISTA DE CUADRUPLOS (DIRS) ---")
        if quads:
            for i, quad in enumerate(quads):
                op, op1, op2, res = quad
                op1_str = str(op1) if op1 is not None else "None"
                op2_str = str(op2) if op2 is not None else "None"
                res_str = str(res) if res is not None else "None"
                print(f"  {i}: ({op}, {op1_str}, {op2_str}, {res_str})")
        else:
            print("  (sin cuadruplos)")

    if verbose:
        print("\n--- EJECUCION (Maquina Virtual) ---")
    vm = VirtualMachine(quads, const_table, get_function_directory())
    vm.run()


def print_symbols() -> None:
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
        print(f"\nFuncion: {fname}")
        print(f"  Retorno: {finfo.return_type}")
        if finfo.parameters:
            print("  Parametros:")
            for (pname, ptype, paddr) in finfo.parameters:
                print(f"    {pname} : {ptype} @ {paddr}")
        else:
            print("  Parametros: (ninguno)")

        vdict = finfo.var_table.all_variables()
        if vdict:
            print("  Vars locales:")
            for vname, vinfo in vdict.items():
                rol = "parametro" if vinfo.is_param else "local"
                print(f"    {vname} : {vinfo.var_type} ({rol}) @ {vinfo.address}")
        else:
            print("  Vars locales: (ninguna)")


def run_suite(dir_path: str, label: str) -> None:
    print(f"\n=== Ejecutando suite {label} en {dir_path} ===")
    base = Path(dir_path)
    if not base.exists():
        print(f"No existe el directorio {dir_path}")
        return

    expected_fail_keywords = [
        "no_declarada",
        "inexistente",
        "mas",
        "menos",
        "otro_tipo",
        "faltante",
        "fuera",
        "nula",
        "redec",
        "booleana",
    ]

    txt_files = sorted(base.glob("*.txt"))
    if not txt_files:
        print("No se encontraron .txt de prueba.")
        return

    total = 0
    passed = 0
    for file in txt_files:
        total += 1
        name = file.name
        expected_fail = any(k in name for k in expected_fail_keywords)

        try:
            code = file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[{name}] ERROR al leer: {e}")
            continue

        try:
            parse(code)
            if expected_fail:
                print(f"[{name}] FALLO (se esperaba error y parseo ok)")
            else:
                print(f"[{name}] OK")
                passed += 1
        except (SemanticError, SyntaxError) as e:
            if expected_fail:
                print(f"[{name}] OK (fallo como se esperaba): {e}")
                passed += 1
            else:
                print(f"[{name}] FALLO: {e}")
        except Exception as e:
            print(f"[{name}] ERROR inesperado: {e}")

    print(f"Resumen {label}: {passed}/{total} pasaron segun expectativa")


def run_builtin_tests(show_quads: bool = False) -> None:
    cases = [
        ("minimo", True, """
        programa test;
        inicio { } fin
        """),
        ("vars_asign_print", True, """
        programa ejemplo;
        vars x : entero;
        inicio { x = 10; escribe("Hola", x); } fin
        """),
        ("while_loop", True, """
        programa ejemplo;
        vars i : entero;
        inicio {
           i = 0;
           mientras (i < 3) haz { escribe("i=", i); i = i + 1; };
        } fin
        """),
        ("if_else", True, """
        programa ejemplo;
        vars x : entero;
        inicio {
           x = 2;
           si (x > 0) { escribe("pos"); } sino { escribe("neg"); };
        } fin
        """),
        ("func_void", True, """
        programa ejemplo;
        nula hola() { { escribe("hola"); } };
        inicio { hola(); } fin
        """),
        ("func_return", True, """
        programa ejemplo;
        vars res: entero;
        entero suma(a: entero, b: entero) { { return a + b; } };
        inicio { res = suma(5, 3); escribe("res", res); } fin
        """),
        ("call_in_expr", True, """
        programa ejemplo;
        vars x: entero;
        entero inc(a: entero) { { return a + 1; } };
        inicio { x = inc(2) * 3; escribe(x); } fin
        """),
        ("fib_iter", True, """
        programa fib;
        vars n, a, b, i, temp: entero;
        inicio {
          n = 6; a = 0; b = 1; i = 0;
          mientras (i < n) haz {
            escribe(a);
            temp = a + b;
            a = b;
            b = temp;
            i = i + 1;
          };
        } fin
        """),
        ("fib_rec", True, """
        programa fib;
        vars n, res: entero;
        entero fib(n: entero) {
          {
            si (n < 2) { return n; } sino { return fib(n - 1) + fib(n - 2); };
          }
        };
        inicio {
          n = 5;
          res = fib(n);
          escribe("fib", n, res);
        } fin
        """),
        # Errores esperados
        ("assign_bool_to_int", False, """
        programa p;
        vars x: entero;
        inicio { x = (1 < 2); } fin
        """),
        ("return_in_void", False, """
        programa p;
        nula hola() { { return 1; } };
        inicio { hola(); } fin
        """),
        ("call_wrong_args", False, """
        programa p;
        entero f(a: entero) { { return a; } };
        inicio { f(1,2); } fin
        """),
        ("call_nula_in_expr", False, """
        programa p;
        nula hola() { { escribe("x"); } };
        inicio { vars x: entero; x = hola(); } fin
        """),
    ]

    total = len(cases)
    passed = 0
    for name, expect_ok, code in cases:
        try:
            parse(code)
            if show_quads:
                print("  Cuadruplos:")
                dump_quads()
            if expect_ok:
                print(f"[{name}] OK")
                passed += 1
            else:
                print(f"[{name}] FALLO (se esperaba error y parseo ok)")
        except (SemanticError, SyntaxError) as e:
            if expect_ok:
                print(f"[{name}] FALLO: {e}")
            else:
                print(f"[{name}] OK (fallo como se esperaba): {e}")
                passed += 1
        except Exception as e:
            if expect_ok:
                print(f"[{name}] ERROR inesperado: {e}")
            else:
                print(f"[{name}] OK (error inesperado pero se esperaba fallo): {e}")
                passed += 1

    print(f"Resumen built-in: {passed}/{total} pasaron segun expectativa")


def run_guide_tests(show_quads: bool = False) -> None:
    base = Path("tests")
    files = sorted(base.glob("*.txt"))
    if not files:
        return

    print(f"=== Casos encontrados en {base} ===")
    for f in files:
        print(f" - {f.name}")

    for fpath in files:
        fname = fpath.name
        try:
            code = fpath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[{fname}] ERROR al leer: {e}")
            continue

        try:
            compile_and_execute(
                code=code,
                label=f"tests/{fname}",
                show_ast=False,
                show_symbols=False,
                show_quads=show_quads,
                show_consts=False,
                verbose=show_quads,
            )
        except (SemanticError, SyntaxError) as e:
            print(f"[{fname}] FALLO: {e}")
        except Exception as e:
            print(f"[{fname}] ERROR inesperado: {e}")


def main(argv=None) -> None:
    argp = argparse.ArgumentParser(description="Frontend Patito")
    argp.add_argument("fuente", nargs="?", help="Archivo con codigo Patito")
    argp.add_argument("--ast", action="store_true", help="Imprimir AST resultante")
    argp.add_argument("--symbols", action="store_true", help="Imprimir tablas de simbolos")
    argp.add_argument("--quads", action="store_true", help="Imprimir cuadruplos generados")
    argp.add_argument("--consts", action="store_true", help="Imprimir tabla de constantes")
    argp.add_argument("--quad-tests-dir", help="Ejecuta todos los .txt en el directorio de pruebas de cuadruplos")
    argp.add_argument("--semantic-tests-dir", help="Ejecuta todos los .txt en el directorio de pruebas semanticas")
    argp.add_argument("--run-builtins", action="store_true", help="Ejecuta el set de pruebas internas (parser/cuadruplos)")
    argp.add_argument("--builtins-show-quads", action="store_true", help="Al correr --run-builtins, mostrar cuadruplos de cada caso")
    argp.add_argument("--run-guide-tests", action="store_true", help="Ejecuta los casos del main de guia (compila y corre en VM)")
    argp.add_argument("--guide-show-quads", action="store_true", help="Al correr --run-guide-tests, mostrar cuadruplos")
    args = argp.parse_args(argv)

    if args.fuente:
        src_path = Path(args.fuente)
        if not src_path.exists():
            print(f"No se encontro el archivo: {src_path}", file=sys.stderr)
            sys.exit(1)

        try:
            code = src_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"No pude leer el archivo: {e}", file=sys.stderr)
            sys.exit(1)

        try:
            compile_and_execute(
                code=code,
                label=str(src_path),
                show_ast=args.ast,
                show_symbols=args.symbols,
                show_quads=args.quads,
                show_consts=args.consts,
                verbose=(args.ast or args.symbols or args.quads or args.consts),
            )
        except SemanticError as e:
            print(f"Error semantico: {e}", file=sys.stderr)
            sys.exit(1)
        except SyntaxError as e:
            print(f"Error de sintaxis: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error inesperado: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not (
            args.run_guide_tests
            or args.run_builtins
            or args.quad_tests_dir
            or args.semantic_tests_dir
        ):
            print("No se proporciono archivo fuente; se omite parse individual.")

    if args.quad_tests_dir:
        run_suite(args.quad_tests_dir, "QuadrupleTests")
    if args.semantic_tests_dir:
        run_suite(args.semantic_tests_dir, "SemanticTests")
    if args.run_builtins:
        run_builtin_tests(show_quads=args.builtins_show_quads)
    if args.run_guide_tests:
        run_guide_tests(show_quads=args.guide_show_quads)


if __name__ == "__main__":
    main()
