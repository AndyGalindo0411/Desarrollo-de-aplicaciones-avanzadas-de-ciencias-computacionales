# memory.py
# Gestor de direcciones virtuales para Patito.
# Asigna espacios para variables globales, locales, temporales y constantes.

from typing import Dict

# Segmentos de memoria
SEG_GLOBAL = "global"
SEG_LOCAL = "local"
SEG_TEMP = "temp"
SEG_CONST = "const"

# Rangos base por segmento y tipo
RANGE_SIZE = 1000
BASES = {
    SEG_GLOBAL: {
        "entero": 10000,
        "flotante": 11000,
        "bool": 12000,
        "letrero": 13000,
    },
    SEG_LOCAL: {
        "entero": 20000,
        "flotante": 21000,
        "bool": 22000,
        "letrero": 23000,
    },
    SEG_TEMP: {
        "entero": 30000,
        "flotante": 31000,
        "bool": 32000,
        "letrero": 33000,
    },
    SEG_CONST: {
        "entero": 40000,
        "flotante": 41000,
        "bool": 42000,
        "letrero": 43000,
    },
}


class MemoryOverflowError(MemoryError):
    """Se intentó asignar una dirección fuera del rango disponible."""


class MemoryManager:
    """
    Administra direcciones virtuales para cada segmento y tipo.
    Incluye una free-list para temporales, de modo que puedan reciclarse.
    """

    def __init__(self) -> None:
        self._base_map: Dict[str, Dict[str, int]] = BASES
        self._counters: Dict[str, Dict[str, int]] = {}
        self._free_temps: Dict[str, list[int]] = {}
        self.reset_all()

    def reset_all(self) -> None:
        """Reinicia todos los contadores y libera temporales."""
        self._counters = {seg: bases.copy() for seg, bases in self._base_map.items()}
        self._free_temps = {tipo: [] for tipo in self._base_map[SEG_TEMP].keys()}

    def reset_locals(self) -> None:
        """Reinicia sólo el segmento de variables locales."""
        self._counters[SEG_LOCAL] = self._base_map[SEG_LOCAL].copy()

    def reset_temps(self) -> None:
        """Reinicia contadores y free-list de temporales."""
        self._counters[SEG_TEMP] = self._base_map[SEG_TEMP].copy()
        self._free_temps = {tipo: [] for tipo in self._base_map[SEG_TEMP].keys()}

    def allocate(self, segment: str, tipo: str) -> int:
        """Entrega una nueva dirección para el segmento/tipo indicado."""
        if segment == SEG_TEMP:
            free_list = self._free_temps.get(tipo, [])
            if free_list:
                return free_list.pop()

        base = self._base_map[segment][tipo]
        next_addr = self._counters[segment][tipo]
        if next_addr >= base + RANGE_SIZE:
            raise MemoryOverflowError(f"Sin espacio para {segment} {tipo}")
        self._counters[segment][tipo] += 1
        return next_addr

    def free_temp(self, tipo: str, address: int) -> None:
        """
        Regresa un temporal a la free-list. No valida si el temporal
        sigue en uso; debe llamarse con criterio.
        """
        self._free_temps.setdefault(tipo, []).append(address)

    def get_usage(self, segment: str) -> Dict[str, int]:
        """Devuelve un dict tipo->cu?ntas direcciones se han usado en el segmento."""
        usage: Dict[str, int] = {}
        for tipo, base in self._base_map[segment].items():
            usage[tipo] = self._counters[segment][tipo] - base
        return usage

        def segment_of(self, address: int) -> str | None:
        """Devuelve el segmento al que pertenece una dirección, o None si no encaja."""
        for seg, bases in self._base_map.items():
            for tipo, base in bases.items():
                if base <= address < base + RANGE_SIZE:
                    return seg
        return None


# Instancia global para usar en parser/intermediate
memory_manager = MemoryManager()
