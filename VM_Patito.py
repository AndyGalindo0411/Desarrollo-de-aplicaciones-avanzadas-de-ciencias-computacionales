from typing import Any, Dict, List, Tuple

from intermediate import quads as ir_quads, const_table
from tabla_symbolos import FunctionDirectory


# Rangos de memoria según memory.py
GLOBAL_MIN = 10000
LOCAL_MIN = 20000
TEMP_MIN = 30000
CONST_MIN = 40000


class VirtualMachine:
    def __init__(
        self,
        quads: List[Tuple[Any, Any, Any, Any]],
        const_table_map: Dict[Tuple[str, Any], int],
        func_dir: FunctionDirectory,
    ):
        self.quads = quads
        self.ip = 0  # instruction pointer
        # Memoria global: direccion -> valor
        self.global_mem: Dict[int, Any] = {}
        # Pila de marcos (locals + temps)
        self.frames: List[Dict[int, Any]] = [{}]  # marco base
        # Constantes: addr -> valor
        self.const_by_addr: Dict[int, Any] = {addr: val for (typ, val), addr in const_table_map.items()}
        # Pila de llamadas: (return_ip, func_name)
        self.call_stack: List[Tuple[int, str]] = []
        # Valores de retorno por función
        self.return_values: Dict[str, Any] = {}
        # Parámetros pendientes (se escriben al hacer GOSUB)
        self.pending_params: List[Any] = []
        # Directorio de funciones (para direcciones de parámetros)
        self.func_dir = func_dir

    def _which_mem(self, addr: int) -> Dict[int, Any]:
        if addr >= CONST_MIN:
            return self.const_by_addr  # lectura únicamente
        if addr >= LOCAL_MIN:
            return self.frames[-1] if self.frames else {}
        return self.global_mem

    def _get_val(self, operand: Any) -> Any:
        if operand is None:
            return None
        if isinstance(operand, int):
            if operand in self.const_by_addr:
                return self.const_by_addr[operand]
            mem = self._which_mem(operand)
            return mem.get(operand, 0)
        if isinstance(operand, str):
            # Slot simbólico de retorno
            if operand in self.return_values:
                return self.return_values[operand]
            # Si se usa como "address" simbólico en frame o global
            if self.frames and operand in self.frames[-1]:
                return self.frames[-1].get(operand)
            if operand in self.global_mem:
                return self.global_mem.get(operand)
            return operand
        return operand

    def _write(self, addr: Any, value: Any) -> None:
        if addr is None:
            return
        if isinstance(addr, int):
            mem = self._which_mem(addr)
            mem[addr] = value
        elif isinstance(addr, str):
            # Slot simbólico (p.ej., nombre de función)
            if self.frames:
                self.frames[-1][addr] = value

    def _jump_to_endfunc(self) -> None:
        # Busca el siguiente ENDFUNC y salta ahí
        for i in range(self.ip + 1, len(self.quads)):
            if self.quads[i][0] == "ENDFUNC":
                self.ip = i
                return
        # Si no se encuentra, terminar
        self.ip = len(self.quads)

    def run(self):
        while 0 <= self.ip < len(self.quads):
            op, a1, a2, res = self.quads[self.ip]

            if op in ('+', '-', '*', '/', '>', '<', '!=', '=='):
                v1 = self._get_val(a1)
                v2 = self._get_val(a2)
                if op == '+':
                    out = v1 + v2
                elif op == '-':
                    out = v1 - v2
                elif op == '*':
                    out = v1 * v2
                elif op == '/':
                    out = v1 / v2
                elif op == '>':
                    out = v1 > v2
                elif op == '<':
                    out = v1 < v2
                elif op == '!=':
                    out = v1 != v2
                elif op == '==':
                    out = v1 == v2
                else:
                    out = None
                self._write(res, out)
                self.ip += 1

            elif op == 'UMINUS':
                v1 = self._get_val(a1)
                self._write(res, -v1)
                self.ip += 1

            elif op == '=':
                v1 = self._get_val(a1)
                self._write(res, v1)
                self.ip += 1

            elif op == 'PRINT':
                v = self._get_val(a1)
                print(v)
                self.ip += 1

            elif op == 'GOTOF':
                cond = self._get_val(a1)
                if not cond:
                    self.ip = int(res) if res is not None else self.ip + 1
                else:
                    self.ip += 1

            elif op == 'GOTO':
                self.ip = int(res) if res is not None else self.ip + 1

            elif op == 'ERA':
                # Preparar parámetros
                self.pending_params = []
                self.ip += 1

            elif op == 'PARAMETER':
                val = self._get_val(a1)
                self.pending_params.append(val)
                self.ip += 1

            elif op == 'GOSUB':
                func_name = a1 if isinstance(a1, str) else ''
                # Guardar retorno
                self.call_stack.append((self.ip + 1, func_name))
                # Crear nuevo frame
                self.frames.append({})
                # Escribir parámetros según direcciones de la firma
                finfo = self.func_dir.get_function(func_name)
                if finfo:
                    for idx, val in enumerate(self.pending_params):
                        if idx < len(finfo.parameters):
                            _pname, _ptype, paddr = finfo.parameters[idx]
                            self._write(paddr, val)
                self.pending_params = []
                # Saltar a inicio de función
                self.ip = int(res) if res is not None else self.ip + 1

            elif op == 'RETURN':
                ret_val = self._get_val(a1)
                func_name = self.call_stack[-1][1] if self.call_stack else ''
                if func_name:
                    self.return_values[func_name] = ret_val
                # Saltar al ENDFUNC siguiente
                self._jump_to_endfunc()

            elif op == 'RETVAL':
                func_name = a1 if isinstance(a1, str) else ''
                val = self.return_values.get(func_name)
                self._write(res, val)
                self.ip += 1

            elif op == 'ENDFUNC':
                if self.call_stack:
                    return_ip, _fname = self.call_stack.pop()
                    if len(self.frames) > 1:
                        self.frames.pop()
                    self.ip = return_ip
                else:
                    self.ip += 1

            elif op == 'END':
                break

            else:
                # Operador desconocido
                self.ip += 1

        return {
            "global": dict(self.global_mem),
            "top_frame": dict(self.frames[-1]) if self.frames else {},
        }
