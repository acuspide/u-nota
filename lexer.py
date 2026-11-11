"""
Analizador léxico de U-Nota.

Recorre el texto carácter por carácter aplicando la matriz δ de afd.py.
Regla de corte (lexema más largo): se avanza mientras exista transición a un
estado distinto de qE. Cuando el siguiente carácter lleva a qE:
  - si el estado actual es de aceptación, se emite el token y se vuelve a q0
    sin consumir ese carácter (equivale a la transición "OTRO" con retroceso
    que se vio en clase);
  - si el estado actual es de rechazo, se reporta un error léxico con el
    mensaje asociado a ese estado y se continúa desde q0.
"""

import afd
from tokens import Token, PALABRAS_RESERVADAS, SIMBOLOS_SIMPLES, OPERADORES, FIN


class ErrorLexico:
    def __init__(self, fila, columna, lexema, mensaje, estado):
        self.fila = fila
        self.columna = columna
        self.lexema = lexema
        self.mensaje = mensaje
        self.estado = estado

    def __str__(self):
        return (f"Error léxico en línea {self.fila}, columna {self.columna}: "
                f"'{self.lexema}' -> {self.mensaje} (el AFD se detuvo en {self.estado})")


def categoria_final(estado, lexema):
    """Convierte la categoría del estado de aceptación en el token definitivo."""
    tipo = afd.ACEPTACION[estado]
    if tipo == "ID":
        return PALABRAS_RESERVADAS.get(lexema, "ID")
    if tipo == "SIMBOLO":
        return SIMBOLOS_SIMPLES[lexema]
    if tipo == "OPERADOR":
        return OPERADORES[lexema]
    return tipo


def analizar(texto):
    """Devuelve (lista de tokens, lista de errores léxicos)."""
    tokens = []
    errores = []

    i = 0
    n = len(texto)
    fila, columna = 1, 1              # posición del carácter texto[i]

    while i < n:
        estado = afd.ESTADO_INICIAL
        lexema = ""
        fila_ini, col_ini = fila, columna

        while True:
            c = texto[i] if i < n else None
            siguiente = afd.ESTADO_ERROR if c is None else afd.transicion(estado, c)

            if siguiente != afd.ESTADO_ERROR:
                # consumir el carácter
                estado = siguiente
                lexema += c
                i += 1
                if c == "\n":
                    fila += 1
                    columna = 1
                else:
                    columna += 1
                continue

            # El siguiente carácter ya no pertenece a este lexema.
            if afd.es_aceptacion(estado):
                categoria = categoria_final(estado, lexema)
                if categoria not in ("BLANCO", "COMENTARIO"):
                    tokens.append(Token(categoria, lexema, fila_ini, col_ini))
            elif estado == afd.ESTADO_INICIAL:
                # Ni siquiera se pudo empezar un token con c: se descarta c.
                if afd.clase_de(c) == "X":
                    mensaje = "el carácter no pertenece al alfabeto Σ de U-Nota"
                else:
                    mensaje = afd.MENSAJE_RECHAZO[estado]
                errores.append(ErrorLexico(fila, columna, c, mensaje, estado))
                i += 1
                columna += 1
            else:
                mensaje = afd.MENSAJE_RECHAZO.get(estado, "lexema inválido")
                errores.append(ErrorLexico(fila_ini, col_ini, lexema.rstrip("\n"), mensaje, estado))
            break

    tokens.append(Token(FIN, "$", fila, columna))
    return tokens, errores


def imprimir_tokens(tokens):
    print(f"{'Fila:Col':<10}{'Categoría':<14}Lexema")
    print("-" * 44)
    for t in tokens:
        print(f"{str(t.fila) + ':' + str(t.columna):<10}{t.categoria:<14}{t.lexema}")
