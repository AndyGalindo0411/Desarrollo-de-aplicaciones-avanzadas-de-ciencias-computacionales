from ply import yacc
from scanner import tokens, lexer as _lexer  

# ------------------
# Precedencia (de menor a mayor)
# ------------------
precedence = (
    ('nonassoc', 'OP_IGUAL', 'OP_DIF', 'OP_MAYOR', 'OP_MENOR'),
    ('left', 'OP_SUMA', 'OP_RESTA'),
    ('left', 'OP_MULT', 'OP_DIV'),
    
)

# AST ligero (puedes reemplazarlo por tus propias clases/nodos)
def node(tag, *kids):
    return (tag,) + kids

# =======================
# 1) <TIPO>
# =======================
def p_tipo(p):
    '''tipo : ENTERO
            | FLOTANTE'''
    p[0] = p[1]

# =======================
# 2) <CTE>
# =======================
def p_cte(p):
    '''cte : CTE_ENT
           | CTE_FLOT'''
    p[0] = ('cte', p[1])

# =======================
# 3) <ASIGNA>
# =======================
def p_asigna(p):
    'asigna : ID OP_ASIG expresion PUNTO_Y_COMA'
    p[0] = ('assign', p[1], p[3])

# =======================
# 4) <ESTATUTO>  y  <LIST_ESTATUTO>
# =======================
def p_estatuto(p):
    '''estatuto : asigna
                | condicion
                | ciclo
                | llamada PUNTO_Y_COMA
                | imprime
                | CORA_ABRE list_estatuto CORA_CIERRA'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ('call_stmt', p[1])
    else:
        p[0] = ('block_square', p[2] or [])

def p_list_estatuto(p):
    '''list_estatuto : empty
                     | estatuto list_estatuto'''
    if len(p) == 3:
        p[0] = [p[1]] + (p[2] or [])
    else:
        p[0] = []

# =======================
# 5) <CUERPO>  y  <CUERPO_ESTATUTO>
# =======================
def p_cuerpo(p):
    'cuerpo : LLAVE_ABRE cuerpo_estat LLAVE_CIERRA'
    p[0] = p[2] or []

def p_cuerpo_estat(p):
    '''cuerpo_estat : empty
                    | estatuto cuerpo_estat'''
    if len(p) == 3:
        p[0] = [p[1]] + (p[2] or [])
    else:
        p[0] = []

# =======================
# 6) <EXPRESIÓN>  y  <EXPRESIÓN_EXP>
# =======================
def p_expresion(p):
    'expresion : exp expresion_exp'
    if p[2] is None:
        p[0] = p[1]
    else:
        op, rhs = p[2]
        p[0] = ('rel', op, p[1], rhs)

def p_expresion_exp(p):
    '''expresion_exp : empty
                     | OP_MAYOR exp
                     | OP_MENOR exp
                     | OP_DIF   exp
                     | OP_IGUAL exp'''
    if len(p) == 3:
        p[0] = (p[1], p[2])
    else:
        p[0] = None

# =======================
# 7) <CICLO>
# =======================
def p_ciclo(p):
    'ciclo : MIENTRAS PAR_ABRE expresion PAR_CIERRA HAZ cuerpo PUNTO_Y_COMA'
    p[0] = ('while', p[3], p[6])

# =======================
# 8) <CONDICIÓN>  y  <CONDICIÓN_CUERPO>
# =======================
def p_condicion(p):
    'condicion : SI PAR_ABRE expresion PAR_CIERRA cuerpo condicion_cuerpo PUNTO_Y_COMA'
    p[0] = ('if', p[3], p[5], p[6])

def p_condicion_cuerpo(p):
    '''condicion_cuerpo : empty
                        | SINO cuerpo'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None

# =======================
# 9) <IMPRIME>, <IMPRIME_EXP>, <IMPRIME_EXP’>
# =======================
def p_imprime(p):
    'imprime : ESCRIBE PAR_ABRE imprime_exp PAR_CIERRA PUNTO_Y_COMA'
    p[0] = ('print', p[3])

def p_imprime_exp(p):
    '''imprime_exp : expresion imprime_exp_p
                   | LETRERO  imprime_exp_p'''
    head = p[1]
    tail = p[2] or []
    p[0] = [head] + tail

def p_imprime_exp_p(p):
    '''imprime_exp_p : empty
                     | COMA imprime_exp'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = []

# =======================
# 10) <LLAMADA>, <LLAMADA_EXPRESIÓN>, <LLAMADA_EX’>
# =======================
def p_llamada(p):
    'llamada : ID PAR_ABRE llamada_expresion PAR_CIERRA'
    p[0] = ('call', p[1], p[3])

def p_llamada_expresion(p):
    '''llamada_expresion : empty
                         | expresion llamada_ex'''
    if len(p) == 3:
        p[0] = [p[1]] + (p[2] or [])
    else:
        p[0] = []

def p_llamada_ex(p):
    '''llamada_ex : empty
                  | COMA expresion llamada_ex'''
    if len(p) == 4:
        p[0] = [p[2]] + (p[3] or [])
    else:
        p[0] = []

# =======================
# 11) <FACTOR>, <FACTOR_SR>, <FACTOR_RS>, <FACTOR_CTE>
# =======================
def p_factor_group(p):
    'factor : PAR_ABRE expresion PAR_CIERRA'
    p[0] = p[2]

def p_factor_signed(p):
    'factor : factor_sr factor_cte'
    sign, value = p[1], p[2]
    if sign == '+':
        p[0] = ('unary', 'UPLUS', value)
    elif sign == '-':
        p[0] = ('unary', 'UMINUS', value)
    else:
        p[0] = value

def p_factor_sr(p):
    '''factor_sr : empty
                 | factor_rs'''
    p[0] = p[1] if p[1] else None

def p_factor_rs(p):
    '''factor_rs : OP_SUMA
                 | OP_RESTA'''
    p[0] = p[1]

def p_factor_cte(p):
    '''factor_cte : ID
                  | cte
                  | llamada'''
    p[0] = p[1]

# =======================
# 12) <VARS>, <VARS_TODO>, <VARS_COMA>, <VARS_FINAL>
# =======================
def p_vars(p):
    'vars : VARS ID vars_todo'
    extra_ids, tipo, vars_final = p[3]
    p[0] = ('vars', [p[2]] + extra_ids, tipo, vars_final)

def p_vars_todo(p):
    'vars_todo : vars_coma DOS_PUNTOS tipo PUNTO_Y_COMA vars_final'
    p[0] = (p[1], p[3], p[5])  # (extra_ids, tipo, vars_final)

def p_vars_coma(p):
    '''vars_coma : empty
                 | COMA ID vars_coma'''
    if len(p) == 4:
        p[0] = [p[2]] + (p[3] or [])
    else:
        p[0] = []

def p_vars_final(p):
    '''vars_final : empty
                  | vars_todo'''
    p[0] = p[1]

# =======================
# 13) <FUNCS>, <FUNCS_NT>, <FUNC_TIPO>, <FUNCS_COMA>, <FUNC_VARS>
# =======================
def p_funcs(p):
    'funcs : funcs_nt ID PAR_ABRE func_tipo PAR_CIERRA LLAVE_ABRE func_vars cuerpo LLAVE_CIERRA PUNTO_Y_COMA'
    p[0] = ('func', p[1], p[2], p[4], p[7], p[8])

def p_funcs_nt(p):
    '''funcs_nt : NULA
                | tipo'''
    p[0] = p[1]

def p_func_tipo(p):
    '''func_tipo : empty
                 | ID DOS_PUNTOS tipo funcs_coma'''
    if len(p) == 5:
        p[0] = [(p[1], p[3])] + (p[4] or [])
    else:
        p[0] = []

def p_funcs_coma(p):
    '''funcs_coma : empty
                  | COMA ID DOS_PUNTOS tipo funcs_coma'''
    if len(p) == 6:
        p[0] = [(p[2], p[4])] + (p[5] or [])
    else:
        p[0] = []

def p_func_vars(p):
    '''func_vars : empty
                 | vars'''
    p[0] = p[1]

# =======================
# 14) <EXP>  y  <EXP_TÉRMINO>
# =======================
def p_exp(p):
    'exp : termino exp_termino'
    if p[2] is None:
        p[0] = p[1]
    else:
        op, rhs = p[2]
        p[0] = (op, p[1], rhs)

def p_exp_termino(p):
    '''exp_termino : empty
                   | OP_SUMA exp
                   | OP_RESTA exp'''
    if len(p) == 3:
        p[0] = (p[1], p[2])
    else:
        p[0] = None

# =======================
# 15) <TÉRMINO>  y  <TÉRMINO_FACTOR’>
# =======================
def p_termino(p):
    'termino : factor termino_factor'
    if p[2] is None:
        p[0] = p[1]
    else:
        op, rhs = p[2]
        p[0] = (op, p[1], rhs)

def p_termino_factor(p):
    '''termino_factor : empty
                      | OP_MULT termino
                      | OP_DIV  termino'''
    if len(p) == 3:
        p[0] = (p[1], p[2])
    else:
        p[0] = None

# =======================
# 16) <PROGRAMA> (+ envoltorios mínimos para vars/funcs opcionales)
# Programa → programa id ; <PRO_VARS> <PRO_FUNCS> inicio <CUERPO> fin
# <PRO_VARS>  → ε | <VARS>
# <PRO_FUNCS> → ε | <FUNCS> <PRO_FUNCS>
# =======================
def p_programa(p):
    'programa : PROGRAMA ID PUNTO_Y_COMA pro_vars pro_funcs INICIO cuerpo FIN'
    p[0] = node('programa', p[2], p[4], p[5], p[7])

def p_pro_vars(p):
    '''pro_vars : empty
                | vars'''
    p[0] = p[1]

def p_pro_funcs(p):
    '''pro_funcs : empty
                 | pro_funcs_list'''
    p[0] = p[1] if p[1] else None

def p_pro_funcs_list(p):
    '''pro_funcs_list : funcs
                      | pro_funcs_list funcs'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# =======================
# Vacío y manejo de errores
# =======================
def p_empty(p):
    'empty :'
    p[0] = None

def p_error(p):
    if p:
        raise SyntaxError(f"Error de sintaxis cerca de token {p.type} (valor={p.value!r})")
    else:
        raise SyntaxError("Error de sintaxis al final de la entrada")

# Construcción del parser
parser = yacc.yacc(start='programa')

def parse(code: str):
    """Parsea código fuente Patito y devuelve un AST ligero."""
    return parser.parse(code, lexer=_lexer)
