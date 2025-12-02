from ply import yacc
from scanner import tokens, lexer as _lexer

# Nuevas importaciones semánticas
from tabla_symbolos import (
    FunctionDirectory,
    FunctionInfo,
    VariableTable,
    VariableInfo,
    SemanticError,
)

# Infraestructura de IR (cuádruplos y temporales)
from intermediate import (
    alloc_global,
    alloc_local,
    emit_quad,
    fill_quad,
    intern_const,
    new_temp,
    next_quad,
    PJumps,
    reset_function_memory,
    reset_ir,
)

# (Opcional) Cubo semántico para tipos
from cube_semantic import (
    result_type,
    TIPO_ENTERO,
    TIPO_FLOTANTE,
    TIPO_BOOL,
    TIPO_LETRERO,
    TIPO_ERROR,
)

# ============================================================
#  ESTRUCTURAS SEMÁNTICAS GLOBALES
# ============================================================

# Directorio de funciones (todas las funciones del programa)
func_dir: FunctionDirectory = FunctionDirectory()

# Tabla de variables globales (vars declaradas antes de 'inicio')
global_var_table: VariableTable = VariableTable()

# Función en contexto (para resolver ámbito local); None = global
current_func: FunctionInfo | None = None


def _reset_semantic_structures():
    """
    Reinicia el directorio de funciones y la tabla de variables globales.
    Se llama al inicio de cada parse(code).
    """
    global func_dir, global_var_table, current_func
    func_dir = FunctionDirectory()
    global_var_table = VariableTable()
    current_func = None


def _extract_var_decls(vars_ast):
    """
    Extrae una lista de (nombre, tipo) a partir del AST de 'vars'.

    Forma del AST de vars (según tus reglas):
        ('vars', [id1, id2, ...], tipo, vars_final)

    donde vars_final es:
        - None, o
        - otro nodo 'vars' anidado con la misma forma.
    """
    result = []

    def visit(node):
        if not node:
            return
        tag = node[0]
        if tag != 'vars':
            return
        _, id_list, var_type, vars_final = node
        for name in id_list:
            result.append((name, var_type))
        if vars_final:
            visit(vars_final)

    visit(vars_ast)
    return result


def _lookup_var_info(name: str) -> VariableInfo:
    """
    Busca la variable en el \u00e1mbito actual (local si estamos dentro de una
    función, o global en caso contrario). Levanta SemanticError si no existe.
    """
    if current_func:
        info = current_func.var_table.lookup(name)
        if info:
            return info
    info = global_var_table.lookup(name)
    if info is None:
        raise SemanticError(f"Variable '{name}' no declarada.")
    return info


def _lookup_var_type(name: str) -> str:
    """Atajo para obtener el tipo de una variable declarada."""
    return _lookup_var_info(name).var_type


# ============================================================
#  PRECEDENCIA (SINTAXIS)
# ============================================================
precedence = (
    ('nonassoc', 'OP_IGUAL', 'OP_DIF', 'OP_MAYOR', 'OP_MENOR'),
    ('left', 'OP_SUMA', 'OP_RESTA'),
    ('left', 'OP_MULT', 'OP_DIV'),
)


# AST ligero para estructuras grandes (programa, func, etc.)
def node(tag, *kids):
    return (tag,) + kids


# =======================
# 1) <TIPO>
# =======================
def p_tipo(p):
    '''tipo : ENTERO
            | FLOTANTE'''
    # p[1] será 'entero' o 'flotante'
    p[0] = p[1]


# =======================
# 2) <CTE>
# =======================
def p_cte(p):
    '''cte : CTE_ENT
           | CTE_FLOT'''
    # Regresamos (dir_constante, tipo)
    token_type = p.slice[1].type
    if token_type == 'CTE_ENT':
        val_type = TIPO_ENTERO
    else:
        val_type = TIPO_FLOTANTE
    addr = intern_const(p[1], val_type)
    p[0] = (addr, val_type)


# =======================
# 3) <ASIGNA>
# =======================
def p_asigna(p):
    'asigna : ID OP_ASIG expresion PUNTO_Y_COMA'
    var_name = p[1]
    var_info = _lookup_var_info(var_name)
    var_type = var_info.var_type
    var_addr = var_info.address

    expr_place, expr_type = p[3]

    # Verificamos tipos con el cubo semántico
    res_type = result_type(var_type, '=', expr_type)
    if res_type == TIPO_ERROR:
        raise SemanticError(
            f"Type-mismatch en asignación a '{var_name}': "
            f"no se puede asignar {expr_type} a {var_type}"
        )

    # Generar cuádruplo de asignación
    # (=, expr_place, -, var_name)
    emit_quad('=', expr_place, None, var_addr)

    # AST opcional
    p[0] = ('assign', var_name, p[3])


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
    left_place, left_type = p[1]

    if p[2] is None:
        # Solo expresión aritmética
        p[0] = (left_place, left_type)
    else:
        op, (right_place, right_type) = p[2]

        res_type = result_type(left_type, op, right_type)
        if res_type == TIPO_ERROR:
            raise SemanticError(
                f"Operación relacional inválida: {left_type} {op} {right_type}"
            )

        temp = new_temp(res_type)
        emit_quad(op, left_place, right_place, temp)
        p[0] = (temp, res_type)


def p_expresion_exp(p):
    '''expresion_exp : empty
                     | OP_MAYOR exp
                     | OP_MENOR exp
                     | OP_DIF   exp
                     | OP_IGUAL exp'''
    if len(p) == 3:
        op = p[1]           # '>', '<', '!=', '=='
        right = p[2]        # (place, tipo)
        p[0] = (op, right)
    else:
        p[0] = None


# =======================
# 7) <CICLO>
# =======================
def p_ciclo(p):
    'ciclo : MIENTRAS PAR_ABRE expresion PAR_CIERRA HAZ cuerpo PUNTO_Y_COMA'
    loop_start = next_quad

    cond_place, cond_type = p[3]
    if cond_type != TIPO_BOOL:
        raise SemanticError("La condici?n de 'mientras' debe ser de tipo bool")

    # GOTOF para salir del ciclo si la condici?n es falsa
    false_jump = emit_quad('GOTOF', cond_place, None, None)
    PJumps.append(false_jump)

    body = p[6]

    # Al final del cuerpo, regresar al inicio
    emit_quad('GOTO', None, None, loop_start)

    # Rellenar el salto falso para que apunte despu?s del ciclo
    end_false = PJumps.pop()
    fill_quad(end_false, next_quad)

    p[0] = ('while', p[3], body)



# =======================
# 8) <CONDICIÓN>  y  <CONDICIÓN_CUERPO>
# =======================
def p_condicion(p):
    'condicion : SI PAR_ABRE expresion PAR_CIERRA cuerpo condicion_cuerpo PUNTO_Y_COMA'
    cond_place, cond_type = p[3]
    if cond_type != TIPO_BOOL:
        raise SemanticError("La condici?n de 'si' debe ser de tipo bool")

    # GOTOF hacia el else (o al final si no hay else)
    false_jump = emit_quad('GOTOF', cond_place, None, None)
    PJumps.append(false_jump)

    then_body = p[5]
    else_body = p[6]

    if else_body is not None:
        # Saltar el bloque else al terminar el then
        goto_end = emit_quad('GOTO', None, None, None)
        # Rellenar el GOTOF para que apunte al inicio del else
        fill_quad(PJumps.pop(), next_quad)
        PJumps.append(goto_end)
        p[0] = ('if_else', p[3], then_body, else_body)
        # Rellenar el salto al final
        fill_quad(PJumps.pop(), next_quad)
    else:
        # Sin else: el GOTOF apunta al final del if
        fill_quad(PJumps.pop(), next_quad)
        p[0] = ('if', p[3], then_body)



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
    items = p[3]  # lista de ('expr', (place,tipo)) o ('str', lexema)

    for kind, val in items:
        if kind == 'expr':
            place, _tipo = val
            emit_quad('PRINT', place, None, None)
        else:  # 'str'
            lex_addr, _tipo = val
            emit_quad('PRINT', lex_addr, None, None)

    p[0] = ('print', items)


def p_imprime_exp(p):
    '''imprime_exp : expresion imprime_exp_p
                   | LETRERO  imprime_exp_p'''
    if p.slice[1].type == 'LETRERO':
        addr = intern_const(p[1], TIPO_LETRERO)
        head = ('str', (addr, TIPO_LETRERO))      # cadena literal
    else:
        head = ('expr', p[1])     # (place, tipo)

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
    # En el futuro: aquí podremos validar existencia de la función,
    # tipos/cantidad de parámetros y generar ERA/PARAM/GOSUB.
    # Por ahora solo devolvemos un AST ligero.
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
    # Solo regresamos el resultado de la expresión interna
    p[0] = p[2]  # (place, tipo)


def p_factor_signed(p):
    'factor : factor_sr factor_cte'
    sign, (place, tipo) = p[1], p[2]

    if sign is None:
        p[0] = (place, tipo)
    elif sign == '+':
        # +x no cambia el valor
        p[0] = (place, tipo)
    else:  # '-'
        # unary minus: generamos UMINUS si es numérico
        if tipo not in (TIPO_ENTERO, TIPO_FLOTANTE):
            raise SemanticError(f"No se puede aplicar signo '-' a tipo {tipo}")
        temp = new_temp(tipo)
        emit_quad('UMINUS', place, None, temp)
        p[0] = (temp, tipo)


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
    sym_type = p.slice[1].type

    if sym_type == 'ID':
        name = p[1]
        info = _lookup_var_info(name)
        p[0] = (info.address, info.var_type)
    elif sym_type == 'cte':
        # p[1] es (valor, tipo) ya
        p[0] = p[1]
    else:
        # llamada: por ahora no soportamos llamadas que regresen valor
        raise SemanticError("Uso de llamadas en expresiones no está soportado en esta etapa.")


# =======================
# 12) <VARS>, <VARS_TODO>, <VARS_COMA>, <VARS_FINAL>
# =======================
def p_vars(p):
    'vars : VARS ID vars_todo'
    extra_ids, tipo, vars_final = p[3]
    # AST de vars
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
def p_func_header(p):
    'func_header : funcs_nt ID PAR_ABRE func_tipo PAR_CIERRA'
    return_type = p[1]
    func_name = p[2]
    params = p[4] or []  # lista de (nombre, tipo)

    # Reiniciar memoria local/temporal para la nueva funci?n
    reset_function_memory()

    # Crear entrada de funci?n (lanza error si ya exist?a)
    func_info = func_dir.add_function(func_name, return_type)

    # Registrar par?metros
    for param_name, param_type in params:
        addr = alloc_local(param_type)
        func_info.add_parameter(param_name, param_type, addr)

    # Establecer contexto actual
    global current_func
    current_func = func_info

    p[0] = (func_info, return_type, func_name, params)


def p_funcs(p):
    'funcs : func_header LLAVE_ABRE func_vars cuerpo LLAVE_CIERRA PUNTO_Y_COMA'
    func_info, return_type, func_name, params = p[1]
    vars_ast = p[3]  # AST de vars locales (o None)

    # Registrar variables locales declaradas en 'func_vars'
    if vars_ast:
        for var_name, var_type in _extract_var_decls(vars_ast):
            addr = alloc_local(var_type)
            func_info.var_table.add_variable(var_name, var_type, addr, is_param=False)

    body = p[4]
    p[0] = ('func', return_type, func_name, params, vars_ast, body)

    # Salir del contexto de funci?n
    global current_func
    current_func = None


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
    left_place, left_type = p[1]
    if p[2] is None:
        p[0] = (left_place, left_type)
    else:
        op, (right_place, right_type) = p[2]

        res_type = result_type(left_type, op, right_type)
        if res_type == TIPO_ERROR:
            raise SemanticError(
                f"Operación aritmética inválida: {left_type} {op} {right_type}"
            )

        temp = new_temp(res_type)
        emit_quad(op, left_place, right_place, temp)
        p[0] = (temp, res_type)


def p_exp_termino(p):
    '''exp_termino : empty
                   | OP_SUMA exp
                   | OP_RESTA exp'''
    if len(p) == 3:
        op = p[1]   # '+' o '-'
        right = p[2]  # (place, tipo)
        p[0] = (op, right)
    else:
        p[0] = None


# =======================
# 15) <TÉRMINO>  y  <TÉRMINO_FACTOR’>
# =======================
def p_termino(p):
    'termino : factor termino_factor'
    left_place, left_type = p[1]
    if p[2] is None:
        p[0] = (left_place, left_type)
    else:
        op, (right_place, right_type) = p[2]

        res_type = result_type(left_type, op, right_type)
        if res_type == TIPO_ERROR:
            raise SemanticError(
                f"Operación aritmética inválida: {left_type} {op} {right_type}"
            )

        temp = new_temp(res_type)
        emit_quad(op, left_place, right_place, temp)
        p[0] = (temp, res_type)


def p_termino_factor(p):
    '''termino_factor : empty
                      | OP_MULT termino
                      | OP_DIV  termino'''
    if len(p) == 3:
        op = p[1]     # '*' o '/'
        right = p[2]  # (place, tipo)
        p[0] = (op, right)
    else:
        p[0] = None


# =======================
# 16) <PROGRAMA>  (PRO_VARS, PRO_FUNCS)
# Programa → programa id ; <PRO_VARS> <PRO_FUNCS> inicio <CUERPO> fin
# =======================
def p_programa(p):
    'programa : PROGRAMA ID PUNTO_Y_COMA pro_vars pro_funcs INICIO cuerpo FIN'
    prog_name = p[2]

    # ========= ACCIÓN SEMÁNTICA: Variables globales =========
    # p[4] = pro_vars, que puede ser None o un AST 'vars'
    if p[4] is not None:
        for var_name, var_type in _extract_var_decls(p[4]):
            addr = alloc_global(var_type)
            global_var_table.add_variable(var_name, var_type, addr)

    # AST del programa (como antes)
    p[0] = node('programa', prog_name, p[4], p[5], p[7])


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


# ============================================================
#  API PÚBLICA DEL PARSER
# ============================================================
def parse(code: str):
    """
    Parsea código fuente Patito y devuelve un AST ligero.
    Además, llena:
      - func_dir  (Directorio de Funciones)
      - global_var_table  (Tabla de Variables Global)
      - y limpia las pilas/cuádruplos de IR antes de usarlo.
    """
    _reset_semantic_structures()
    reset_ir()  # limpiar PilaO, PTypes, POper, PJumps, quads, temporales
    ast = parser.parse(code, lexer=_lexer)
    return ast


def get_function_directory() -> FunctionDirectory:
    """
    Devuelve el directorio de funciones construido en el último parse().
    """
    return func_dir


def get_global_var_table() -> VariableTable:
    """
    Devuelve la tabla de variables globales construida en el último parse().
    """
    return global_var_table
