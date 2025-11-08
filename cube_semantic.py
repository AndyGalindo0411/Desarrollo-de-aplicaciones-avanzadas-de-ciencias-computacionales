
# Tipos manejados a nivel semántico
TIPO_ENTERO   = "entero"
TIPO_FLOTANTE = "flotante"
TIPO_BOOL     = "bool"
TIPO_LETRERO  = "letrero"
TIPO_ERROR    = "error"

# Operadores (como aparecerán en el AST / tokens)
OP_SUMA   = "+"
OP_RESTA  = "-"
OP_MULT   = "*"
OP_DIV    = "/"
OP_MAYOR  = ">"
OP_MENOR  = "<"
OP_IGUAL  = "=="
OP_DIF    = "!="
OP_ASIG   = "="

# Cubo semántico:
#   cubo[tipo_izq][operador][tipo_der] = tipo_resultante  (o TIPO_ERROR)
SEMANTIC_CUBE = {}

def _init_cube():
    # Helper para inicializar estructura
    tipos = [TIPO_ENTERO, TIPO_FLOTANTE, TIPO_BOOL, TIPO_LETRERO]
    ops   = [OP_SUMA, OP_RESTA, OP_MULT, OP_DIV,
             OP_MAYOR, OP_MENOR, OP_IGUAL, OP_DIF, OP_ASIG]

    for t1 in tipos:
        SEMANTIC_CUBE[t1] = {}
        for op in ops:
            SEMANTIC_CUBE[t1][op] = {}
            for t2 in tipos:
                SEMANTIC_CUBE[t1][op][t2] = TIPO_ERROR  # por defecto: error

    # -------------------------
    # Operaciones aritméticas
    # -------------------------
    arith_ops = [OP_SUMA, OP_RESTA, OP_MULT, OP_DIV]

    # entero (op) entero -> entero
    for op in arith_ops:
        SEMANTIC_CUBE[TIPO_ENTERO][op][TIPO_ENTERO] = TIPO_ENTERO

    # entero (op) flotante -> flotante
    for op in arith_ops:
        SEMANTIC_CUBE[TIPO_ENTERO][op][TIPO_FLOTANTE] = TIPO_FLOTANTE

    # flotante (op) entero -> flotante
    for op in arith_ops:
        SEMANTIC_CUBE[TIPO_FLOTANTE][op][TIPO_ENTERO] = TIPO_FLOTANTE

    # flotante (op) flotante -> flotante
    for op in arith_ops:
        SEMANTIC_CUBE[TIPO_FLOTANTE][op][TIPO_FLOTANTE] = TIPO_FLOTANTE

    # -------------------------
    # Operaciones relacionales <, >
    # Solo entre tipos numéricos, resultado bool
    # -------------------------
    rel_ops = [OP_MAYOR, OP_MENOR]

    numeric_pairs = [
        (TIPO_ENTERO,   TIPO_ENTERO),
        (TIPO_ENTERO,   TIPO_FLOTANTE),
        (TIPO_FLOTANTE, TIPO_ENTERO),
        (TIPO_FLOTANTE, TIPO_FLOTANTE),
    ]

    for op in rel_ops:
        for t1, t2 in numeric_pairs:
            SEMANTIC_CUBE[t1][op][t2] = TIPO_BOOL

    # -------------------------
    # Operaciones de igualdad ==, !=
    # -------------------------
    eq_ops = [OP_IGUAL, OP_DIF]

    # Numérico con numérico -> bool
    for op in eq_ops:
        for t1, t2 in numeric_pairs:
            SEMANTIC_CUBE[t1][op][t2] = TIPO_BOOL

    # bool con bool -> bool
    for op in eq_ops:
        SEMANTIC_CUBE[TIPO_BOOL][op][TIPO_BOOL] = TIPO_BOOL

    # letrero con letrero -> bool  (si NO quieres permitir esto, comenta esta parte)
    for op in eq_ops:
        SEMANTIC_CUBE[TIPO_LETRERO][op][TIPO_LETRERO] = TIPO_BOOL

    # -------------------------
    # Asignación =
    # -------------------------
    op = OP_ASIG

    # entero = entero
    SEMANTIC_CUBE[TIPO_ENTERO][op][TIPO_ENTERO] = TIPO_ENTERO
    # flotante = flotante
    SEMANTIC_CUBE[TIPO_FLOTANTE][op][TIPO_FLOTANTE] = TIPO_FLOTANTE
    # flotante = entero (promoción válida)
    SEMANTIC_CUBE[TIPO_FLOTANTE][op][TIPO_ENTERO] = TIPO_FLOTANTE

    # bool = bool
    SEMANTIC_CUBE[TIPO_BOOL][op][TIPO_BOOL] = TIPO_BOOL

    # letrero = letrero
    SEMANTIC_CUBE[TIPO_LETRERO][op][TIPO_LETRERO] = TIPO_LETRERO

    # entero = flotante se queda como error (pérdida de precisión)


# Inicializar el cubo al importar el módulo
_init_cube()

def result_type(left_type: str, operator: str, right_type: str) -> str:
    """
    Devuelve el tipo resultante de (left_type operator right_type)
    según el cubo semántico, o 'error' si la operación es inválida.
    """
    return SEMANTIC_CUBE.get(left_type, {}) \
                        .get(operator, {}) \
                        .get(right_type, TIPO_ERROR)
