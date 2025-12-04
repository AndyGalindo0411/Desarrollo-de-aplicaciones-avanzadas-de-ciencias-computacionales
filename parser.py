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
import intermediate as ir
from intermediate import (
    alloc_global,
    alloc_local,
    emit_quad,
    fill_quad,
    intern_const,
    new_temp,
    PJumps,
    reset_function_memory,
    reset_ir,
    quads,
)
from memory import SEG_LOCAL, SEG_TEMP, memory_manager

# Cubo semántico para tipos
from cube_semantic import (
    result_type,
    TIPO_ENTERO,
    TIPO_FLOTANTE,
    TIPO_BOOL,
    TIPO_LETRERO,
    TIPO_ERROR,
)

#  ESTRUCTURAS SEMÁNTICAS GLOBALES

# Directorio de funciones (todas las funciones del programa)
func_dir: FunctionDirectory = FunctionDirectory()

# Tabla de variables globales (vars declaradas antes de 'inicio')
global_var_table: VariableTable = VariableTable()

# Función en contexto (para resolver ámbito local); None = global
current_func: FunctionInfo | None = None

# Salto inicial para brincar funciones y entrar a main
main_goto: int | None = None
main_start: int | None = None


def _reset_semantic_structures():
    global func_dir, global_var_table, current_func, main_goto, main_start
    func_dir = FunctionDirectory()
    global_var_table = VariableTable()
    current_func = None
    main_goto = None
    main_start = None


def _extract_var_decls(vars_ast):
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
    if current_func:
        info = current_func.var_table.lookup(name)
        if info:
            return info
    info = global_var_table.lookup(name)
    if info is None:
        raise SemanticError(f"Variable '{name}' no declarada.")
    return info


def _lookup_var_type(name: str) -> str:
    return _lookup_var_info(name).var_type


#  SINTAXIS
precedence = (
    ('nonassoc', 'OP_IGUAL', 'OP_DIF', 'OP_MAYOR', 'OP_MENOR', 'OP_MAYORIGUAL', 'OP_MENORIGUAL'),
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
# <RETORNO>
# =======================
def p_retorno(p):
    '''retorno : RETURN expresion PUNTO_Y_COMA
               | RETURN PUNTO_Y_COMA'''
    if current_func is None:
        raise SemanticError("'return' solo es v?lido dentro de una funci?n")

    func_info = current_func
    ret_type = func_info.return_type

    if len(p) == 3:  # RETURN PUNTO_Y_COMA (sin expresi?n)
        if ret_type != 'nula':
            raise SemanticError(f"La funci?n '{func_info.name}' debe regresar {ret_type}")
        emit_quad('RETURN', None, None, None)
        p[0] = ('return', None)
    else:  # RETURN expresion ;
        expr_place, expr_type = p[2]
        if ret_type == 'nula':
            raise SemanticError("Funciones 'nula' no deben regresar valor")
        if expr_type != ret_type:
            raise SemanticError(f"Tipo de retorno invalido: se esperaba {ret_type}, se obtuvo {expr_type}")
        emit_quad('RETURN', expr_place, None, None)
        p[0] = ('return', (expr_place, expr_type))

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
                | retorno
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
                     | OP_MAYORIGUAL exp
                     | OP_MENORIGUAL exp
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
    'ciclo : MIENTRAS ciclo_marca PAR_ABRE expresion ciclo_cond_prep PAR_CIERRA HAZ cuerpo PUNTO_Y_COMA'
    loop_start = p[2]
    body = p[8]

    # Al final del cuerpo, regresar al inicio
    emit_quad('GOTO', None, None, loop_start)

    # Rellenar el salto falso para que apunte despu?s del ciclo
    end_false = PJumps.pop()
    fill_quad(end_false, ir.next_quad)

    p[0] = ('while', p[4], body)


def p_ciclo_cond_prep(p):
    'ciclo_cond_prep : '
    cond_place, cond_type = p[-1]
    if cond_type != TIPO_BOOL:
        raise SemanticError("La condicion de 'mientras' debe ser de tipo bool")
    # GOTOF para salir del ciclo si la condici?n es falsa (se inserta antes del cuerpo)
    false_jump = emit_quad('GOTOF', cond_place, None, None)
    PJumps.append(false_jump)


def p_ciclo_marca(p):
    'ciclo_marca : '
    p[0] = ir.next_quad



# =======================
# 8) <CONDICIÓN>  y  <CONDICIÓN_CUERPO>
# =======================
def p_condicion(p):
    'condicion : SI PAR_ABRE expresion condicion_marca PAR_CIERRA cuerpo condicion_cuerpo PUNTO_Y_COMA'
    then_body = p[6]
    else_body = p[7]

    if else_body is not None:
        p[0] = ('if_else', p[3], then_body, else_body)
        # Rellenar el salto al final (goto_end) que quedó en la pila
        fill_quad(PJumps.pop(), ir.next_quad)
    else:
        # Sin else: el GOTOF apunta al final del if
        fill_quad(PJumps.pop(), ir.next_quad)
        p[0] = ('if', p[3], then_body)


def p_condicion_marca(p):
    'condicion_marca : '
    cond_place, cond_type = p[-1]
    if cond_type != TIPO_BOOL:
        raise SemanticError("La condicion de 'si' debe ser de tipo bool")
    # Emitir GOTOF inmediatamente despues de evaluar la condicion
    false_jump = emit_quad('GOTOF', cond_place, None, None)
    PJumps.append(false_jump)



def p_condicion_cuerpo(p):
    '''condicion_cuerpo : empty
                        | SINO condicion_else_marca cuerpo'''
    if len(p) == 4:
        p[0] = p[3]
    else:
        p[0] = None


def p_condicion_else_marca(p):
    'condicion_else_marca : '
    goto_end = emit_quad('GOTO', None, None, None)
    false_jump = PJumps.pop()
    fill_quad(false_jump, ir.next_quad)
    PJumps.append(goto_end)


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
    func_name = p[1]
    args = p[3] or []

    func_info = func_dir.get_function(func_name)
    if not func_info:
        raise SemanticError(f"Funcion '{func_name}' no declarada")

    expected_params = func_info.parameters
    if len(args) != len(expected_params):
        raise SemanticError(f"Funcion '{func_name}' espera {len(expected_params)} argumentos, recibi? {len(args)}")

    total_size = sum(func_info.locals_size.values()) + sum(func_info.temps_size.values())
    emit_quad('ERA', total_size, None, func_name)

    for idx, ((arg_place, arg_type), (_pname, ptype, _paddr)) in enumerate(zip(args, expected_params), start=1):
        if arg_type != ptype:
            raise SemanticError(f"Argumento {idx} de '{func_name}' debe ser {ptype}, se recibi? {arg_type}")
        emit_quad('PARAMETER', arg_place, None, idx)

    emit_quad('GOSUB', func_name, None, func_info.start_quad)

    ret_place = None
    ret_type = func_info.return_type
    if ret_type != 'nula':
        ret_place = new_temp(ret_type)
        emit_quad('RETVAL', func_name, None, ret_place)

    p[0] = ('call', func_name, args, ret_place, ret_type)





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
        # llamada: usar valor de retorno si no es 'nula'
        call_tag, fname, args, ret_place, ret_type = p[1]
        if ret_type == 'nula':
            raise SemanticError("Llamada a función 'nula' no puede usarse en expresiones")
        p[0] = (ret_place, ret_type)


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

    # Establecer contexto actual y punto de entrada de la funci?n
    global current_func
    current_func = func_info
    func_info.start_quad = ir.next_quad

    p[0] = (func_info, return_type, func_name, params)


def p_funcs(p):
    'funcs : func_header LLAVE_ABRE func_vars cuerpo LLAVE_CIERRA PUNTO_Y_COMA'
    func_info, return_type, func_name, params = p[1]
    vars_ast = p[3]  # AST de vars locales (o None)

    body = p[4]
    p[0] = ('func', return_type, func_name, params, vars_ast, body)

    # Registrar tama?os de activaci?n
    func_info.locals_size = memory_manager.get_usage(SEG_LOCAL)
    func_info.temps_size = memory_manager.get_usage(SEG_TEMP)

    # Cuadruplo de fin de funcion
    emit_quad('ENDFUNC', None, None, None)

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
    if p[1] is not None and current_func is not None:
        for var_name, var_type in _extract_var_decls(p[1]):
            addr = alloc_local(var_type)
            current_func.var_table.add_variable(var_name, var_type, addr, is_param=False)


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
    'programa : PROGRAMA ID PUNTO_Y_COMA program_entry pro_vars pro_funcs INICIO program_main cuerpo FIN'
    prog_name = p[2]

    pro_vars_ast = p[5]
    pro_funcs_list = p[6]
    main_body = p[9]

    # AST del programa (como antes)
    p[0] = node('programa', prog_name, pro_vars_ast, pro_funcs_list, main_body)
    # Fin de programa
    emit_quad('END', None, None, None)



# Helper: emitir salto inicial al main
def p_program_entry(p):
    'program_entry : '
    global main_goto
    main_goto = emit_quad('GOTO', None, None, None)
    p[0] = None


# Helper: rellenar salto al main justo al entrar a INICIO
def p_program_main(p):
    'program_main : '
    global main_start
    main_start = ir.next_quad
    if main_goto is not None:
        fill_quad(main_goto, ir.next_quad)
    p[0] = None


def p_pro_vars(p):
    '''pro_vars : empty
                | vars'''
    p[0] = p[1]
    if p[1] is not None and current_func is None:
        for var_name, var_type in _extract_var_decls(p[1]):
            addr = alloc_global(var_type)
            global_var_table.add_variable(var_name, var_type, addr)


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
    _reset_semantic_structures()
    reset_ir()  # limpiar PilaO, PTypes, POper, PJumps, quads, temporales
    ast = parser.parse(code, lexer=_lexer)
    # Salvaguarda: si el salto a main quedó sin rellenar, rellenarlo aquí
    if main_goto is not None:
        # Calcular inicio probable de main:
        # - si main_start se seteo en program_main, úsalo
        # - si no, toma el quad siguiente al último ENDFUNC (o 1 si no hay funcs)
        start_guess = 1
        for idx, (op, _, _, _) in enumerate(quads):
            if op == 'ENDFUNC':
                start_guess = idx + 1
        target = main_start if main_start is not None else start_guess
        try:
            _, _, _, res = quads[main_goto]
            if res in (None, 0):
                fill_quad(main_goto, target)
        except Exception:
            fill_quad(main_goto, target)
    return ast


def get_function_directory() -> FunctionDirectory:
    return func_dir


def get_global_var_table() -> VariableTable:
    return global_var_table
