from scanner import lexer


def test_input(titulo, data):
    print(f"\n--- {titulo} ---")
    try:
        lexer.input(data)
        for tok in lexer:
            print(f"{tok.type:<12} {str(tok.value):<20}")
    except Exception as e:
        print(f"ERROR: {e}")

# Palabras reservadas
test_input("Palabras reservadas", "programa inicio fin vars entero flotante si sino escribe mientras haz si sino nula return")

# Identificadores validos
test_input("Identificadores", "x var1 abc_123 miVariable")

# Constantes enteras (decimal)
test_input("Constantes enteras", "10 42 123456")

# Constantes flotantes (formato simple)
test_input("Constantes flotantes", "3.14 0.001 10.5")

# Operadores 
test_input("Operadores", "= == != + - * / < > { } [ ] ( ) , : ;")

# Letreros
test_input("Letreros", '"hola" "hola mundo" "hola \"Juan\""')

# Errores l?xicos
test_input("Error", "@variable #otro")

# Programa completo
test_input(
    "Programa completo",
    'programa test; vars x: entero; inicio { escribe("Hola"); } fin'
)
