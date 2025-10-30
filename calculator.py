# calculator.py
import ply.lex as lex
import ply.yacc as yacc

# --- SECCIÓN 1: ESPECIFICACIÓN LÉXICA (LEXER) ---

# 1. Definición de tokens requeridos por el parser
tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
)

# 2. Especificación de tokens mediante expresiones regulares
t_PLUS  = r'\+'
t_MINUS = r'-'

# Regla para números (se asume que son enteros para este ejemplo)
def t_NUMBER(t):
    r'\d+'
    # Convierte el lexema (valor de cadena) a un valor entero
    t.value = int(t.value)
    return t

# 3. Caracteres que deben ser ignorados (espacios y tabulaciones)
t_ignore = ' \t'

# 4. Manejo de errores léxicos
def t_error(t):
    print(f"Error léxico: Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Construir el analizador léxico
lexer = lex.lex()

# --- SECCIÓN 2: ESPECIFICACIÓN SINTÁCTICA (PARSER) ---

# 1. Definición del símbolo inicial (la expresión completa)
start = 'expression'

# 2. Reglas de gramática y acciones semánticas (en código Python)

# Gramática: expression -> expression PLUS term
def p_expression_plus(p):
    'expression : expression PLUS term'
    # Acción: p[0] (valor de 'expression') es el resultado de sumar p[1] y p[3]
    p[0] = p[1] + p[3]

# Gramática: expression -> expression MINUS term
def p_expression_minus(p):
    'expression : expression MINUS term'
    # Acción: p[0] es el resultado de restar p[3] a p[1]
    p[0] = p[1] - p[3]

# Gramática: expression -> term
def p_expression_term(p):
    'expression : term'
    # Acción: p[0] simplemente toma el valor de p[1]
    p[0] = p[1]

# Gramática: term -> NUMBER
def p_term_number(p):
    'term : NUMBER'
    # Acción: p[0] toma el valor entero del token NUMBER (ya convertido por el lexer)
    p[0] = p[1]

# 3. Manejo de errores sintácticos
def p_error(p):
    if p:
        print(f"Error de sintaxis en el token '{p.type}' con valor '{p.value}'")
    else:
        print("Error de sintaxis: Fin de archivo inesperado")

# Construir el analizador sintáctico
parser = yacc.yacc()

# --- SECCIÓN 3: EJECUCIÓN ---

while True:
    try:
        s = input('Calc > ')
        if not s: continue
    except EOFError:
        break
        
    # El método .parse() invoca al lexer y al parser
    result = parser.parse(s)
    print("Resultado:", result)