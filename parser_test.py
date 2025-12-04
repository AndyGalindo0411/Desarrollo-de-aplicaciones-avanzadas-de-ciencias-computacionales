from parser import parse


def test_input(titulo, data):
    print(f"\n--- {titulo} ---")
    print("Entrada:")
    print(data)
    try:
        ast = parse(data)
        print("Parseo exitoso")
        print("AST (resumen):", ast)
    except Exception as e:
        print(f"ERROR: {e}")

# Programa m?nimo
test_input("Programa minimo valido", """
programa test;
inicio {
} fin
""")

# Vars y print
test_input("Programa con variables y una impresion", """
programa ejemplo;
vars x : entero;
inicio {
   escribe("Hola");
} fin
""")

# Vars m?ltiples
test_input("Programa con variables mas complejas", """
programa ejemplo;
vars a, b, c : entero;
inicio {
} fin
""")

# Asignaci?n
test_input("Programa con variables y una asignacion", """
programa ejemplo;
vars x : entero;
inicio {
   x = 10;
   escribe("Hola");
} fin
""")

# Ciclo while
test_input("Programa con un ciclo", """
programa ejemplo;
vars i : entero;
inicio {
   i = 0;
   mientras (i < 10) haz {
      escribe("i = ", i);
      i = i + 1;
   };
} fin
""")

# Condicion if/else
test_input("Programa con una condicion", """
programa ejemplo;
vars x : entero;
inicio {
   si (x > 0) {
      escribe("Positivo");
   } sino {
      escribe("Negativo");
   };
} fin
""")

# Funciones con retorno y void
test_input("Programa con funcion", """
programa ejemplo;
vars res: entero;
entero suma(a: entero, b: entero) {
   vars c: entero;
    {
        c = a + b;
        return c;
    }
};   
nula hola_mundo() {
    {
        escribe("Hola mundo");
    }
};
inicio {
    hola_mundo();
    res = suma(5, 3);
    escribe("Resultado: ", res);
} fin
""")

# Expresiones complejas
test_input("Programa con expresiones complejas", """
programa ejemplo;
vars resultado_1, resultado_2, a: entero;
entero suma(a: entero, b: entero) {
   vars resultado: entero;
    {
        resultado = a + b;
        return resultado;
    }
};
inicio {
   resultado_1 = (3 + 5) * (10 - 2) / 4 + suma(2, 3) + a * - a;
   resultado_2 = 5 + 3 + 5 * 10;
   escribe("Resultado: ", resultado_1);
   escribe("Resultado: ", resultado_2);
} fin
""")

# Bloque de estatutos con corchetes
test_input("Programa con arreglo de estatutos", """
programa ejemplo;
vars x: entero;
inicio {
   [ 
        escribe("Hola"); 
        escribe("Mundo");
        x = 10;
        si (x > 5) { 
           escribe("x es mayor que 5");
        } sino { 
           escribe("x no es mayor que 5");
        };
    ]
} fin
""")

# Programa con error esperado
test_input("Programa con errores", """
programa fail;
{
   escribe("Hola");
} fin
""")
