# tests_quads.py
from parser import parse
from intermediate import dump_quads

TESTS = [
    ("prueba1", """
    programa prueba1;
    vars
        x : entero;
        y : entero;
    inicio
        x = 3 + 4 * 2;
        y = x - 1;
        escribe("x =", x, "y =", y);
    fin
    """),
    ("prueba2", """
    programa prueba2;
    vars
        a : flotante;
        b : entero;
        c : flotante;
    inicio
        a = 3.5;
        b = 2;
        c = a + b * 2;
        escribe("a =", a, "b =", b, "c =", c);
    fin
    """),
    ("prueba3", """
    programa prueba3;
    vars
        x : entero;
        y : entero;
    inicio
        x = 5;
        y = 10;
        escribe("x<y:", x < y,
                "x>y:", x > y,
                "x==y:", x == y,
                "x!=y:", x != y);
    fin
    """),
    ("prueba4_error", """
    programa prueba4;
    vars
        x : entero;
    inicio
        x = 3.5;
    fin
    """),
    ("prueba5_unario", """
    programa prueba5;
    vars
        x : entero;
        y : entero;
    inicio
        x = -3;
        y = -(x + 2);
        escribe("x:", x, "y:", y);
    fin
    """),
]


def run_test(name: str, code: str):
    print(f"\n======= TEST: {name} =======")
    try:
        parse(code)
        dump_quads()
    except Exception as e:
        print("ERROR:", e)


def run_all_tests():
    for name, code in TESTS:
        run_test(name, code)


