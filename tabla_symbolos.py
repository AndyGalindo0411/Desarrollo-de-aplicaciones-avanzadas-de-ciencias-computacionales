# Estructuras de datos para el Directorio de Funciones y Tablas de Variables 

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

#  Excepciones semánticas
class SemanticError(Exception):
    pass


#  Información de variables

@dataclass
class VariableInfo:
    name: str
    var_type: str         # "entero", "flotante", "bool", "letrero", etc.
    address: int          # dirección virtual
    is_param: bool = False


class VariableTable:
    def __init__(self) -> None:
        self._vars: Dict[str, VariableInfo] = {}

    def add_variable(self, name: str, var_type: str, address: int, is_param: bool = False) -> None:
        if name in self._vars:
            raise SemanticError(f"Variable '{name}' declarada más de una vez en el mismo ámbito.")
        self._vars[name] = VariableInfo(name=name, var_type=var_type, address=address, is_param=is_param)

    def lookup(self, name: str) -> Optional[VariableInfo]:
        return self._vars.get(name)

    def all_variables(self) -> Dict[str, VariableInfo]:
        return dict(self._vars)

#  Información de funciones

@dataclass
class FunctionInfo:
    name: str
    return_type: str                    # "entero", "flotante", "nula"
    parameters: List[Tuple[str, str, int]] = field(default_factory=list)  # (nombre, tipo, dir)
    var_table: VariableTable = field(default_factory=VariableTable)
    start_quad: int | None = None
    locals_size: Dict[str, int] = field(default_factory=dict)
    temps_size: Dict[str, int] = field(default_factory=dict)

    def add_parameter(self, name: str, param_type: str, address: int) -> None:
        # Primero verificar que no haya otro parámetro/variable con el mismo nombre
        if self.var_table.lookup(name) is not None:
            raise SemanticError(f"Parámetro/variable '{name}' ya existe en la función '{self.name}'.")
        # Registrar en la lista de parámetros (orden importa)
        self.parameters.append((name, param_type, address))
        # Registrar en la tabla de variables del ámbito de la función
        self.var_table.add_variable(name, param_type, address, is_param=True)


class FunctionDirectory:
    def __init__(self) -> None:
        # Diccionario: {nombre_funcion: FunctionInfo}
        self._funcs: Dict[str, FunctionInfo] = {}

    def add_function(self, name: str, return_type: str) -> FunctionInfo:
        if name in self._funcs:
            raise SemanticError(f"Función '{name}' ya fue declarada previamente.")
        func_info = FunctionInfo(name=name, return_type=return_type)
        self._funcs[name] = func_info
        return func_info

    def get_function(self, name: str) -> Optional[FunctionInfo]:
        return self._funcs.get(name)

    def has_function(self, name: str) -> bool:
        return name in self._funcs

    def all_functions(self) -> Dict[str, FunctionInfo]:
        return dict(self._funcs)
