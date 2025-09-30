import collections

# =====================================================================
# 1. IMPLEMENTACIÓN DE LAS CLASES
# =====================================================================

# A. STACK (Pila) - LIFO
class Stack:
    """Implementación de STACK (LIFO) usando una lista de Python."""
    def __init__(self):
        self._items = []

    def push(self, item):
        """Agrega un elemento a la parte superior de la pila."""
        self._items.append(item)

    def pop(self):
        """Remueve y devuelve el elemento superior (LIFO)."""
        if not self.isEmpty():
            return self._items.pop()
        raise IndexError("ERROR: pop() en una pila vacía (Underflow).")

    def peek(self):
        """Devuelve el elemento superior sin removerlo."""
        if not self.isEmpty():
            return self._items[-1]
        raise IndexError("ERROR: peek() en una pila vacía.")

    def isEmpty(self):
        """Verifica si la pila está vacía."""
        return len(self._items) == 0

# B. QUEUE (Cola) - FIFO
class Queue:
    """Implementación de QUEUE (FIFO) usando collections.deque."""
    def __init__(self):
        # collections.deque ofrece inserciones/extracciones O(1) en ambos extremos, ideal para colas.
        self._items = collections.deque()

    def enqueue(self, item):
        """Agrega un elemento al final de la cola."""
        self._items.append(item)

    def dequeue(self):
        """Remueve y devuelve el elemento del frente (FIFO)."""
        if not self.isEmpty():
            return self._items.popleft() # Extracción del inicio de la cola
        raise IndexError("ERROR: dequeue() en una cola vacía (Underflow).")

    def peek(self):
        """Devuelve el elemento del frente sin removerlo."""
        if not self.isEmpty():
            return self._items[0]
        raise IndexError("ERROR: peek() en una cola vacía.")

    def isEmpty(self):
        """Verifica si la cola está vacía."""
        return len(self._items) == 0

# C. TABLE / HASH / DICTIONARY (Ordenada)
class Dictionary:
    """Implementación de DICTIONARY (acceso por clave, mantiene orden de inserción)."""
    def __init__(self):
        # El dict nativo de Python (desde 3.7+) mantiene el orden de inserción.
        self._data = {}

    def insert(self, key, value):
        """Agrega un par clave-valor. Si la clave existe, actualiza el valor."""
        self._data[key] = value

    def get(self, key):
        """Recupera el valor asociado a la clave."""
        if key in self._data:
            return self._data[key]
        raise KeyError(f"ERROR: Clave '{key}' no encontrada.")

    def remove(self, key):
        """Elimina la entrada asociada a la clave."""
        if key in self._data:
            del self._data[key]
        else:
            raise KeyError(f"ERROR: No se puede eliminar. Clave '{key}' no encontrada.")

    def containsKey(self, key):
        """Verifica si la clave existe."""
        return key in self._data
        
    def show_order(self):
        """Muestra las claves en su orden de inserción."""
        return list(self._data.keys())

# =====================================================================
# 2. PROGRAMA DE DEMOSTRACIÓN Y VALIDACIÓN (TEST-CASES)
# =====================================================================

def run_demonstration(title, func):
    """Función auxiliar para ejecutar y formatear la demostración."""
    print(f"\n{'='*5} {title} {'='*5}")
    try:
        func()
        print(f"Demostración de {title} completada con éxito.")
    except Exception as e:
        print(f"ERROR CRÍTICO durante la demostración de {title}: {e}")

# --- Demostración de STACK ---
def demo_stack():
    """Demuestra el principio LIFO y las operaciones clásicas de la Pila."""
    pila = Stack()
    print("[Test 1: isEmpty inicial] Pila vacía:", pila.isEmpty()) 

    # Test: Push y LIFO principle
    print("Push: 'A', 'B', 'C' (LIFO)")
    pila.push("A")
    pila.push("B")
    pila.push("C") # Último en entrar
    
    # Test: Peek
    print("[Test 2: Peek] Elemento superior:", pila.peek()) # Esperado: C

    # Test: Pop (LIFO)
    print(f"[Test 3: Pop LIFO 1] Extraído: {pila.pop()}") # Esperado: C
    print(f"[Test 4: Pop LIFO 2] Extraído: {pila.pop()}") # Esperado: B
    
    print("[Test 5: isEmpty final] Pila vacía:", pila.isEmpty())

# --- Demostración de QUEUE ---
def demo_queue():
    """Demuestra el principio FIFO y las operaciones clásicas de la Cola."""
    cola = Queue()
    print("[Test 1: isEmpty inicial] Cola vacía:", cola.isEmpty())

    # Test: Enqueue y FIFO principle
    print("Enqueue: 10, 20, 30 (FIFO)")
    cola.enqueue(10) # Primero en entrar
    cola.enqueue(20)
    cola.enqueue(30)

    # Test: Peek
    print("[Test 2: Peek] Elemento frontal:", cola.peek()) # Esperado: 10

    # Test: Dequeue (FIFO)
    print(f"[Test 3: Dequeue FIFO 1] Extraído: {cola.dequeue()}") # Esperado: 10
    print(f"[Test 4: Dequeue FIFO 2] Extraído: {cola.dequeue()}") # Esperado: 20
    
    print("[Test 5: isEmpty final] Cola vacía:", cola.isEmpty())

# --- Demostración de DICTIONARY ---
def demo_dictionary():
    """Demuestra el acceso por clave, la actualización y la persistencia de orden."""
    dicc = Dictionary()
    
    # Test: Insert y Order (la clave 'materia' se inserta primero)
    print("Insert: 'materia': 'Compiladores', 'clave': 304, 'carrera': 'Sistemas'")
    dicc.insert("materia", "Compiladores")
    dicc.insert("clave", 304)
    dicc.insert("carrera", "Sistemas")

    # Test: Get
    print("[Test 1: Get] Clave de materia:", dicc.get("materia")) # Esperado: Compiladores

    # Test: containsKey
    print("[Test 2: containsKey 'clave']:", dicc.containsKey("clave")) # Esperado: True
    
    # Test: Update (el valor de 'clave' se actualiza)
    print("[Test 3: Update] Insertando 'clave': 305")
    dicc.insert("clave", 305) 
    print("Nuevo valor de 'clave':", dicc.get("clave")) # Esperado: 305
    
    # Test: Remove
    print("[Test 4: Remove 'carrera']")
    dicc.remove("carrera")
    print("Contiene 'carrera':", dicc.containsKey("carrera")) # Esperado: False
    
    # Test: Order (Validación de persistencia de orden de inserción en las claves restantes)
    print("[Test 5: Order] Claves restantes en orden de inserción:", dicc.show_order())
    # Esperado: ['materia', 'clave']

# --- Demostración de Casos Límite (Excepciones) ---
def demo_exceptions():
    """Demuestra el manejo de errores de Underflow y Key Errors."""
    print("\n--- Manejo de Excepciones y Casos Límite ---")
    
    # STACK Underflow
    try:
        print("\nSTACK: Intentando pop() en pila vacía...")
        Stack().pop()
    except IndexError as e:
        print(f"STACK Test OK: Se capturó la excepción de Underflow. Mensaje: {e}")

    # QUEUE Underflow
    try:
        print("\nQUEUE: Intentando dequeue() en cola vacía...")
        Queue().dequeue()
    except IndexError as e:
        print(f"QUEUE Test OK: Se capturó la excepción de Underflow. Mensaje: {e}")

    # DICTIONARY Key Error (Get)
    try:
        print("\nDICTIONARY: Intentando get() de clave inexistente...")
        Dictionary().get("inexistente")
    except KeyError as e:
        print(f"DICTIONARY Test OK: Se capturó la excepción de clave faltante. Mensaje: {e}")


if __name__ == "__main__":
    # Ejecución de todas las demostraciones
    run_demonstration("STACK (LIFO)", demo_stack)
    run_demonstration("QUEUE (FIFO)", demo_queue)
    run_demonstration("DICTIONARY (TABLE/HASH)", demo_dictionary)
    demo_exceptions()