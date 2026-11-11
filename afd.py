"""
Autómata Finito Determinista del analizador léxico de U-Nota.

    M = (Q, Σ, δ, q0, F)

Esta es la misma matriz de transiciones de la Fase 1, escrita como tabla.
Si se modifica el autómata en el documento, se modifica aquí la fila o la
columna correspondiente y el analizador léxico cambia de comportamiento sin
tocar ninguna otra parte del código.
"""

# ---------------------------------------------------------------------------
# Σ agrupado en clases de símbolos (columnas de la matriz)
# ---------------------------------------------------------------------------
#   L   letras a..z, A..Z (sin tildes ni ñ)
#   D   dígitos 0..9
#   _   guion bajo
#   .   punto decimal
#   "   comillas dobles
#   #   inicio de comentario
#   <  >  =  !   operadores relacionales / asignación
#   S   símbolos simples  + - * / ( ) { } ; %
#   B   blancos: espacio, tabulador, retorno de carro
#   NL  salto de línea
#   X   cualquier otro carácter (tildes, ñ, @, $, ...). Solo es válido
#       dentro de una CADENA o de un COMENTARIO.

COLUMNAS = ["L", "D", "_", ".", '"', "#", "<", ">", "=", "!", "S", "B", "NL", "X"]

SIMBOLOS_S = set("+-*/(){};%")


def clase_de(c):
    """Devuelve la columna de la matriz a la que pertenece el carácter c."""
    if ("a" <= c <= "z") or ("A" <= c <= "Z"):
        return "L"
    if "0" <= c <= "9":
        return "D"
    if c in ("_", ".", '"', "#", "<", ">", "=", "!"):
        return c
    if c in SIMBOLOS_S:
        return "S"
    if c in (" ", "\t", "\r"):
        return "B"
    if c == "\n":
        return "NL"
    return "X"


# ---------------------------------------------------------------------------
# Q, q0, F y la función de transición δ
# ---------------------------------------------------------------------------
# qE es el estado de error (sumidero): una vez se llega a él no se sale.
# Llegar a qE significa "este carácter ya no forma parte del lexema actual".

ESTADO_INICIAL = "q0"
ESTADO_ERROR = "qE"

#            L     D     _     .     "     #     <     >     =     !     S     B     NL    X
DELTA = {
    "q0":  ["q1", "q2", "qE", "qE", "q5", "q7", "q8", "q10", "q12", "q14", "q16", "q17", "q17", "qE"],
    "q1":  ["q1", "q1", "q1", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q2":  ["qE", "q2", "qE", "q3", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q3":  ["qE", "q4", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q4":  ["qE", "q4", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q5":  ["q5", "q5", "q5", "q5", "q6", "q5", "q5", "q5", "q5", "q5", "q5", "q5", "qE", "q5"],
    "q6":  ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q7":  ["q7", "q7", "q7", "q7", "q7", "q7", "q7", "q7", "q7", "q7", "q7", "q7", "qE", "q7"],
    "q8":  ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "q9", "qE", "qE", "qE", "qE", "qE"],
    "q9":  ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q10": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "q11", "qE", "qE", "qE", "qE", "qE"],
    "q11": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q12": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "q13", "qE", "qE", "qE", "qE", "qE"],
    "q13": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q14": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "q15", "qE", "qE", "qE", "qE", "qE"],
    "q15": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q16": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
    "q17": ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "q17", "q17", "qE"],
    "qE":  ["qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE", "qE"],
}

# F: estados de aceptación y la categoría que reconoce cada uno.
# Las categorías "ID" y "SIMBOLO" se precisan después con las tablas de
# tokens.py (palabras reservadas y símbolos simples).
ACEPTACION = {
    "q1": "ID",
    "q2": "NUM",
    "q4": "NUM",
    "q6": "CADENA",
    "q7": "COMENTARIO",
    "q8": "OPERADOR",
    "q9": "OPERADOR",
    "q10": "OPERADOR",
    "q11": "OPERADOR",
    "q12": "OPERADOR",
    "q13": "OPERADOR",
    "q15": "OPERADOR",
    "q16": "SIMBOLO",
    "q17": "BLANCO",
}

# Estados de rechazo (no aceptación) y el error que significa quedarse en
# cada uno cuando el siguiente carácter lleva a qE.
MENSAJE_RECHAZO = {
    "q0": "el carácter no puede iniciar ningún token",
    "q3": "número real incompleto: después del punto debe venir al menos un dígito",
    "q5": "cadena sin cerrar: falta la comilla de cierre antes del fin de línea",
    "q14": "el símbolo '!' solo es válido en el operador '!='",
}


def transicion(estado, caracter):
    """δ(q, a): consulta la matriz."""
    columna = COLUMNAS.index(clase_de(caracter))
    return DELTA[estado][columna]


def es_aceptacion(estado):
    return estado in ACEPTACION


def acepta(cadena):
    """
    Algoritmo de procesamiento visto en clase:
        q <- q0;  para cada a_i: q <- δ(q, a_i);  aceptar si q ∈ F.
    Sirve para probar una cadena completa a mano contra el autómata.
    Devuelve (aceptada, recorrido de estados).
    """
    q = ESTADO_INICIAL
    recorrido = [q]
    for a in cadena:
        q = transicion(q, a)
        recorrido.append(q)
    return es_aceptacion(q), recorrido


def imprimir_matriz():
    ancho = 5
    print("δ".ljust(ancho) + "".join(c.ljust(ancho) for c in COLUMNAS))
    for estado, fila in DELTA.items():
        marca = "*" if es_aceptacion(estado) else " "
        print((marca + estado).ljust(ancho) + "".join(d.ljust(ancho) for d in fila))
    print("(* = estado de aceptación)")
