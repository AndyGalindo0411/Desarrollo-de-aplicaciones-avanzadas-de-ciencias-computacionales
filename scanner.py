from ply import lex # type: ignore

# Palabras reservadas (en minúsculas en el código fuente)
reserved = {
    'programa': 'PROGRAMA',
    'inicio':   'INICIO',
    'fin':      'FIN',
    'vars':     'VARS',
    'entero':   'ENTERO',
    'flotante': 'FLOTANTE',
    'escribe':  'ESCRIBE',
    'mientras': 'MIENTRAS',
    'haz':      'HAZ',
    'si':       'SI',
    'sino':     'SINO',
    'nula':     'NULA',
    'return':   'RETURN',
}

# Lista de tokens (incluye reservadas + símbolos + literales)
tokens = [
    # Operadores
    'OP_IGUAL', 'OP_DIF', 'OP_ASIG',
    'OP_MAYOR', 'OP_MENOR', 'OP_MAYORIGUAL', 'OP_MENORIGUAL',
    'OP_SUMA', 'OP_RESTA', 'OP_MULT', 'OP_DIV',

    # Delimitadores
    'LLAVE_ABRE', 'LLAVE_CIERRA',
    'CORA_ABRE', 'CORA_CIERRA',
    'PAR_ABRE', 'PAR_CIERRA',
    'COMA', 'DOS_PUNTOS', 'PUNTO_Y_COMA',

    # Literales / identificadores
    'LETRERO', 'CTE_FLOT', 'CTE_ENT', 'ID',
] + list(reserved.values())

# ------------------
# Tokens por ER (según tu tabla)
# ------------------
# Operadores (dobles primero por máxima voracidad)
t_OP_MAYORIGUAL = r'>='
t_OP_MENORIGUAL = r'<='
t_OP_IGUAL = r'=='
t_OP_DIF   = r'!='
t_OP_ASIG  = r'='
t_OP_MAYOR = r'>'
t_OP_MENOR = r'<'
t_OP_SUMA  = r'\+'
t_OP_RESTA = r'-'
t_OP_MULT  = r'\*'
t_OP_DIV   = r'/'

# Delimitadores
t_LLAVE_ABRE   = r'\{'
t_LLAVE_CIERRA = r'\}'
t_CORA_ABRE    = r'\['
t_CORA_CIERRA  = r'\]'
t_PAR_ABRE     = r'\('
t_PAR_CIERRA   = r'\)'
t_COMA         = r','
t_DOS_PUNTOS   = r':'
t_PUNTO_Y_COMA = r';'

# Literales (letrero = "(l|d|s|op|vacío)*")
# Implementación robusta como cadena con escapes estilo C (sin salto de línea adentro)
def t_LETRERO(t):
    r'"([^\\\n]|(\\.))*?"'
    return t

def t_CTE_FLOT(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t

def t_CTE_ENT(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Identificadores y reservadas: id = l (l|d|(_l|_d))*
def t_ID(t):
    r'[A-Za-z][A-Za-z0-9_]*'
    tipo = reserved.get(t.value)
    if tipo:
        t.type = tipo
    return t

# Ignorar espacios y tabs (WS)
t_ignore = ' \t\r'

# Contador de líneas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Errores léxicos
def t_error(t):
    raise SyntaxError(f"Carácter ilegal '{t.value[0]}' en línea {t.lexer.lineno}")

lexer = lex.lex()
