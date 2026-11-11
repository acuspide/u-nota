"""
Categorías léxicas (tokens) del lenguaje U-Nota.

Un token es la tupla (categoría, lexema, fila, columna), tal como se definió
en la Fase 1. Las categorías de este archivo son exactamente los símbolos
terminales de la gramática (Fase 2).
"""

from dataclasses import dataclass


@dataclass
class Token:
    categoria: str
    lexema: str
    fila: int
    columna: int

    def __str__(self):
        return f"({self.categoria}, '{self.lexema}', {self.fila}:{self.columna})"


# Palabras reservadas: el AFD las reconoce con el mismo camino de un ID
# (estado q1) y luego se buscan en esta tabla.
PALABRAS_RESERVADAS = {
    "curso": "CURSO",
    "evaluacion": "EVALUACION",
    "peso": "PESO",
    "estudiante": "ESTUDIANTE",
    "mostrar": "MOSTRAR",
    "promedio": "PROMEDIO",
    "si": "SI",
    "entonces": "ENTONCES",
    "sino": "SINO",
}

# Símbolos de un solo carácter (estado q16 del AFD).
SIMBOLOS_SIMPLES = {
    "+": "MAS",
    "-": "MENOS",
    "*": "POR",
    "/": "DIV",
    "(": "PAR_IZQ",
    ")": "PAR_DER",
    "{": "LLAVE_IZQ",
    "}": "LLAVE_DER",
    ";": "PYC",
    "%": "PORCENTAJE",
}

# Operadores relacionales y de asignación (estados q8 a q15).
OPERADORES = {
    "<": "MENOR",
    "<=": "MENOR_IGUAL",
    ">": "MAYOR",
    ">=": "MAYOR_IGUAL",
    "=": "ASIG",
    "==": "IGUAL",
    "!=": "DIFERENTE",
}

# Fin de archivo: el símbolo $ de las tablas LL(1).
FIN = "FIN"

# Nombre legible de cada categoría, para los mensajes de error.
DESCRIPCION = {
    "ID": "un identificador",
    "NUM": "un número",
    "CADENA": "una cadena entre comillas",
    FIN: "el fin del archivo",
}
for lexema, cat in {**PALABRAS_RESERVADAS, **SIMBOLOS_SIMPLES, **OPERADORES}.items():
    DESCRIPCION[cat] = f"'{lexema}'"


def describir(categoria):
    return DESCRIPCION.get(categoria, categoria)
