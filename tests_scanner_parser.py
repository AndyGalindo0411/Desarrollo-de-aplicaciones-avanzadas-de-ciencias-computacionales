from scanner import lexer
from parser import parse

# -------------------------
# Helpers
# -------------------------
def lex_types(text):
    """Devuelve la lista de tipos de token producidos por el scanner."""
    lexer.input(text)
    types = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        types.append(tok.type)
    return types

def parse_ok(text):
    """Intenta parsear y regresa (True, AST) o (False, Exception)."""
    try:
        ast = parse(text)
        return True, ast
    except Exception as e:
        return False, e

def parse_fail(text):
    """Regresa (True, Exception) si falla como se espera; (False, AST) si no falló."""
    ok, result = parse_ok(text)
    return (not ok), result

# -------------------------
# Casos válidos (Parser OK)
# -------------------------
PROGRAM_MIN = r"""
programa main;
inicio { } fin
"""


PROGRAM_VARS = r"""
programa p;
vars x, y, z : entero;
inicio {
  x = 3;
  y = x + 2 * (3 - 1);
  escribe("ok", x, y);
} fin
"""


PROGRAM_FUNCS = r"""
programa demo;
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
  escribe("sum:", suma(3, 4));
} fin
"""



PROGRAM_FLOW = r"""
programa flow;
vars x : entero;
inicio {
  x = 5;
  si (x > 3) { escribe("mayor"); } sino { escribe("menor"); };
  mientras (x < 8) haz { x = x + 1; };
  [ x = 10; escribe("bloque"); ]
} fin
"""

PROGRAM_REL_PRINT = r"""
programa rel;
inicio {
  escribe("msg", 1, 2+3, 4*5, 6/3, 7-2);
  si (1 == 1) { escribe("eq"); } ;
  si (2 != 3) { escribe("neq"); } ;
  si (4 > 3) { escribe("gt"); } ;
  si (2 < 5) { escribe("lt"); } ;
} fin
"""

PROGRAM_CALLS_EDGE = r"""
programa edge;
inicio {
  f();
  g(1);
  h(1, 2, 3);
  escribe("solo");
  escribe(1);
  escribe("mix", 1, 2+3);
} fin
"""
PROGRAM_UNARY_SIGNS = r"""
programa signos;
vars x : entero;
inicio {
  x = -5;
  x = +x;
  x = -1 * (3 + 2);
  escribe(x);
} fin
"""



# -------------------------
# Casos inválidos (Parser debe fallar)
# -------------------------
BAD_MISSING_SEMI = r"""
programa p;
inicio {
  x = 3
} fin
"""

BAD_UNBALANCED_BRACE = r"""
programa p;
inicio {
  escribe("hola");
fin
"""

BAD_PROGRAM_NO_ID = r"""
programa ;
inicio { } fin
"""

BAD_WHILE_SYNTAX = r"""
programa p;
inicio {
  mientras (x < 10) { x = x + 1; };   # falta 'haz'
} fin
"""

BAD_EXTRA_VARS_BLOCK = r"""
programa p;
vars x : entero;
vars y : entero;   # segundo 'vars' no permitido por la CFG oficial
inicio { } fin
"""

# -------------------------
# Casos de scanner
# -------------------------
LEX_RESERVED_AND_ID = "programa test; vars x, y: entero; inicio { escribe(x); } fin"
LEX_OPERATORS = "a==b; c!=d; e=f; g<h; i>j; k+l-m*n/p;"
LEX_NUMBERS_STR = 'x=10; y=3.14; escribe("hola\\n", x, y);'

LEX_ILLEGAL_CHAR = "programa p; inicio { @ } fin"  # '@' debe disparar SyntaxError

# -------------------------
# Ejecutar pruebas
# -------------------------
def run_scanner_tests():
    print("== SCANNER TESTS ==")

    # 1) Palabras reservadas e IDs
    types = lex_types(LEX_RESERVED_AND_ID)
    must_have = {'PROGRAMA', 'VARS', 'ENTERO', 'INICIO', 'ESCRIBE', 'FIN', 'ID'}
    assert must_have.issubset(set(types)), f"Faltan tokens {must_have - set(types)}"
    print("Reservadas/ID OK")

    # 2) Operadores
    types = lex_types(LEX_OPERATORS)
    must_have_ops = {'OP_IGUAL','OP_DIF','OP_ASIG','OP_MENOR','OP_MAYOR',
                     'OP_SUMA','OP_RESTA','OP_MULT','OP_DIV'}
    assert must_have_ops.issubset(set(types)), f"Faltan operadores {must_have_ops - set(types)}"
    print("Operadores OK")

    # 3) Números y letrero
    types = lex_types(LEX_NUMBERS_STR)
    must_have_cte = {'CTE_ENT','CTE_FLOT','LETRERO'}
    assert must_have_cte.issubset(set(types)), f"Faltan literales {must_have_cte - set(types)}"
    print("Constantes y letrero OK")

    # 4) Error léxico por carácter ilegal
    try:
        _ = lex_types(LEX_ILLEGAL_CHAR)
        raise AssertionError("Se esperaba SyntaxError por carácter ilegal y no ocurrió")
    except SyntaxError:
        print("Error léxico (carácter ilegal) OK")

def run_parser_tests():
    print("\n== PARSER TESTS ==")

    # Válidos
    for name, prog in [
        ("PROGRAM_MIN", PROGRAM_MIN),
        ("PROGRAM_VARS", PROGRAM_VARS),
        ("PROGRAM_FUNCS", PROGRAM_FUNCS),
        ("PROGRAM_FLOW", PROGRAM_FLOW),
        ("PROGRAM_REL_PRINT", PROGRAM_REL_PRINT),
        ("PROGRAM_CALLS_EDGE", PROGRAM_CALLS_EDGE),
        ("PROGRAM_UNARY_SIGNS", PROGRAM_UNARY_SIGNS),
    ]:
        ok, result = parse_ok(prog)
        assert ok, f"{name} debería ser válido. Error: {result}"
        print(f"{name} OK")

    # Inválidos
    for name, prog in [
        ("BAD_MISSING_SEMI", BAD_MISSING_SEMI),
        ("BAD_UNBALANCED_BRACE", BAD_UNBALANCED_BRACE),
        ("BAD_PROGRAM_NO_ID", BAD_PROGRAM_NO_ID),
        ("BAD_WHILE_SYNTAX", BAD_WHILE_SYNTAX),
        ("BAD_EXTRA_VARS_BLOCK", BAD_EXTRA_VARS_BLOCK),
    ]:
        bad, err = parse_fail(prog)
        assert bad, f"{name} debería fallar"
        print(f"{name} falla como se espera")

if __name__ == "__main__":
    run_scanner_tests()
    run_parser_tests()
    print("\nTODOS LOS TESTS PASARON")
