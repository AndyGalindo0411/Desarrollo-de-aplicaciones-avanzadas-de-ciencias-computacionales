# intermediate.py
# Infraestructura para generación de código intermedio (cuádruplos)

from typing import Any, List, Tuple

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
#  Manejo de temporales
# ==========================

_temp_counter: int = 0  # para generar nombres t1, t2, t3, ...


def new_temp() -> str:
    """
    Devuelve el nombre de un nuevo temporal (t1, t2, t3, ...).
    """
    global _temp_counter
    _temp_counter += 1
    return f"t{_temp_counter}"


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
    global PilaO, PTypes, POper, PJumps, quads, next_quad, _temp_counter
    PilaO = []
    PTypes = []
    POper = []
    PJumps = []
    quads = []
    next_quad = 0
    _temp_counter = 0


def dump_quads() -> None:
    """
    Imprime todos los cuádruplos en consola con su índice.
    """
    print("=== CUADRUPLOS GENERADOS ===")
    for i, (op, arg1, arg2, res) in enumerate(quads):
        print(f"{i:3}: ({op}, {arg1}, {arg2}, {res})")
