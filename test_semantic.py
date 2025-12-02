# test_semantics.py
# Prueba de estructuras semánticas:
#   - Directorio de Funciones
#   - Tabla de Variables Globales

from parser import (
    parse,
    get_function_directory,
    get_global_var_table,
)
from tabla_symbolos import SemanticError


# Programa Patito de prueba (válido según tu gramática)
PROGRAM_OK = r"""
programa demo;
vars g1, g2 : entero;
entero suma(a : entero, b : entero) {
  vars r : entero;
  {
    r = a + b;
  }
} ;
nula hola() {
  {
    escribe("hola");
  }
} ;
inicio {
  g1 = 10;
  g2 = 20;
  escribe("fin");
} fin
"""


def print_global_vars():
    print("\n=== TABLA DE VARIABLES GLOBALES ===")
    global_table = get_global_var_table()
    vars_dict = global_table.all_variables()
    if not vars_dict:
        print("  (sin variables globales)")
    else:
        for name, vinfo in vars_dict.items():
            print(f"  {name} : {vinfo.var_type}")


def print_function_directory():
    print("\n=== DIRECTORIO DE FUNCIONES ===")
    func_dir = get_function_directory()
    funcs_dict = func_dir.all_functions()

    if not funcs_dict:
        print("  (sin funciones registradas)")
        return

    for fname, finfo in funcs_dict.items():
        print(f"\nFunción: {fname}")
        print(f"  Tipo de retorno: {finfo.return_type}")

        # Parámetros
        if finfo.parameters:
            print("  Parámetros:")
            for (pname, ptype, paddr) in finfo.parameters:
                print(f"    {pname} : {ptype} @ {paddr}")
        else:
            print("  Parámetros: (ninguno)")

        # Variables (incluye parámetros marcados como is_param)
        vtable = finfo.var_table
        vdict = vtable.all_variables()
        if vdict:
            print("  Variables en ámbito de la función:")
            for vname, vinfo in vdict.items():
                rol = "parámetro" if vinfo.is_param else "local"
                print(f"    {vname} : {vinfo.var_type}  ({rol}) @ {vinfo.address}")
        else:
            print("  Variables en ámbito de la función: (ninguna)")


def main():
    print("=== PROGRAMA DE PRUEBA ===")
    print(PROGRAM_OK)

    try:
        print("\n=== PARSEANDO PROGRAMA... ===")
        ast = parse(PROGRAM_OK)
        print("Parseo exitoso.\n")

        # (Opcional) Mostrar un resumen del AST
        print("=== AST (resumen) ===")
        print(ast)

        # Mostrar tablas semánticas
        print_global_vars()
        print_function_directory()

    except SemanticError as se:
        print("\n*** ERROR SEMÁNTICO ***")
        print(se)
    except SyntaxError as se:
        print("\n*** ERROR SINTÁCTICO ***")
        print(se)


if __name__ == "__main__":
    main()
