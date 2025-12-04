# intermediate.py
# Infraestructura para generación de código intermedio (cuádruplos)

from typing import Any, Dict, List, Tuple
from memory import (
    SEG_CONST,
    SEG_GLOBAL,
    SEG_LOCAL,
    SEG_TEMP,
    memory_manager,
)

# ==========================
#  Pilas principales
# ==========================

# Pila de operandos (PilaO): IDs, constantes, temporales, etc.
PilaO: List[Any] = []

# Pila de tipos de cada operando (PTypes): "entero", "flotante", "bool", "letrero"
PTypes: List[str] = []

# Pila de operadores (POper): '+', '-', '*', '/', '==', '<', '>' , '=' , etc.
POper: List[str] = []

# Pila de saltos (para if/while; la usaremos después)
PJumps: List[int] = []

# ==========================
#  Fila de cuádruplos
# ==========================

# Cada cuadruplo es una tupla: (op, arg1, arg2, result)
Quadruple = Tuple[str, Any, Any, Any]

quads: List[Quadruple] = []

# Apuntador al siguiente cuadruplo (índice)
next_quad: int = 0

# ==========================
#  Tabla de constantes
# ==========================
# Map (tipo, valor) -> dirección virtual
const_table: Dict[Tuple[str, Any], int] = {}

# ==========================
#  Manejo de temporales
# ==========================

_temp_counter: int = 0  # para generar nombres t1, t2, t3, ...


def new_temp(tipo: str) -> int:
    """
    Devuelve la dirección de un nuevo temporal para el tipo dado.
    """
    global _temp_counter
    _temp_counter += 1
    return memory_manager.allocate(SEG_TEMP, tipo)


def release_temp(tipo: str, address: int) -> None:
    """
    Libera un temporal (lo regresa a la free-list). Llamar sólo
    cuando estés seguro de que ya no se usará.
    """
    memory_manager.free_temp(tipo, address)


def alloc_global(tipo: str) -> int:
    return memory_manager.allocate(SEG_GLOBAL, tipo)


def alloc_local(tipo: str) -> int:
    return memory_manager.allocate(SEG_LOCAL, tipo)


def intern_const(value: Any, tipo: str) -> int:
    """
    Registra una constante y devuelve su dirección. Reutiliza la
    dirección si el valor ya se había internado.
    """
    key = (tipo, value)
    if key in const_table:
        return const_table[key]
    addr = memory_manager.allocate(SEG_CONST, tipo)
    const_table[key] = addr
    return addr


# ==========================
#  Operaciones sobre IR
# ==========================

def emit_quad(op: str, arg1: Any, arg2: Any, result: Any) -> int:
    """
    Agrega un cuadruplo a la fila de cuádruplos y regresa su índice.
    """
    global next_quad
    quad = (op, arg1, arg2, result)
    quads.append(quad)
    idx = next_quad
    next_quad += 1
    return idx


def fill_quad(index: int, result: Any) -> None:
    """
    Rellena el campo 'result' de un cuadruplo existente.
    Útil para GOTOF / GOTO.
    """
    op, arg1, arg2, _ = quads[index]
    quads[index] = (op, arg1, arg2, result)


def reset_ir() -> None:
    """
    Limpia TODAS las pilas y la lista de cuádruplos.
    Llamar al inicio de cada parse(code).
    """
    global next_quad, _temp_counter, const_table
    PilaO.clear()
    PTypes.clear()
    POper.clear()
    PJumps.clear()
    quads.clear()
    next_quad = 0
    _temp_counter = 0
    const_table.clear()
    memory_manager.reset_all()


def dump_quads() -> None:
    """
    Imprime todos los cuádruplos en consola con su índice.
    """
    print("=== CUADRUPLOS GENERADOS ===")
    for i, (op, arg1, arg2, res) in enumerate(quads):
        print(f"{i:3}: ({op}, {arg1}, {arg2}, {res})")



def reset_function_memory() -> None:
    """
    Reinicia contadores de locales y temporales (p.ej. al comenzar una nueva funci?n).
    No toca memoria global ni constantes.
    """
    memory_manager.reset_locals()
    memory_manager.reset_temps()
