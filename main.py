import argparse
import sys
from pathlib import Path

from parser import parse, get_function_directory, get_global_var_table
from tabla_symbolos import SemanticError
from intermediate import dump_quads


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
    """
    Bateria interna de pruebas de parser/semantica.
    Marca OK/FALLO y muestra el error real en los fallos esperados.
    """
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


def main(argv=None) -> None:
    argp = argparse.ArgumentParser(description="Frontend Patito")
    argp.add_argument("fuente", nargs="?", help="Archivo con codigo Patito")
    argp.add_argument("--ast", action="store_true", help="Imprimir AST resultante")
    argp.add_argument("--symbols", action="store_true", help="Imprimir tablas de simbolos")
    argp.add_argument("--quads", action="store_true", help="Imprimir cuadruplos generados")
    argp.add_argument("--quad-tests-dir", help="Ejecuta todos los .txt en el directorio de pruebas de cuadruplos")
    argp.add_argument("--semantic-tests-dir", help="Ejecuta todos los .txt en el directorio de pruebas semanticas")
    argp.add_argument("--run-builtins", action="store_true", help="Ejecuta el set de pruebas internas (parser/cuadruplos)")
    argp.add_argument("--builtins-show-quads", action="store_true", help="Al correr --run-builtins, mostrar cuadruplos de cada caso")
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
            ast = parse(code)
            print("Parseo exitoso")
            if args.ast:
                print("\n=== AST ===")
                print(ast)
            if args.symbols:
                print("\n=== SIMBOLOS ===")
                print_symbols()
            if args.quads:
                print("\n=== CUADRUPLOS ===")
                dump_quads()
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
        print("No se proporciono archivo fuente; se omite parse individual.")

    if args.quad_tests_dir:
        run_suite(args.quad_tests_dir, "QuadrupleTests")
    if args.semantic_tests_dir:
        run_suite(args.semantic_tests_dir, "SemanticTests")
    if args.run_builtins:
        run_builtin_tests(show_quads=args.builtins_show_quads)


if __name__ == "__main__":
    main()
