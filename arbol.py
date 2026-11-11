"""
Árbol de derivación sintáctica.

Cada nodo interno es un no terminal de la gramática LL(1) de la Fase 2 y sus
hijos son, en orden, los símbolos del lado derecho de la regla aplicada.
Las hojas son tokens (terminales) o ε.
"""


class Nodo:
    def __init__(self, simbolo, token=None):
        self.simbolo = simbolo      # nombre del no terminal, categoría del token o "ε"
        self.token = token          # solo en las hojas terminales
        self.hijos = []

    def agregar(self, hijo):
        self.hijos.append(hijo)
        return hijo

    def es_terminal(self):
        return self.token is not None or self.simbolo == "ε"

    def etiqueta(self):
        if self.token is not None:
            return f"{self.simbolo} '{self.token.lexema}'"
        if self.simbolo == "ε":
            return "ε"
        return f"<{self.simbolo}>"

    def hojas(self):
        """Hojas leídas de izquierda a derecha: deben dar el programa original."""
        if self.es_terminal():
            return [] if self.simbolo == "ε" else [self.token.lexema]
        resultado = []
        for h in self.hijos:
            resultado.extend(h.hojas())
        return resultado


def a_texto(nodo, prefijo="", es_ultimo=True, es_raiz=True):
    lineas = []
    if es_raiz:
        lineas.append(nodo.etiqueta())
        nuevo_prefijo = ""
    else:
        lineas.append(prefijo + ("└── " if es_ultimo else "├── ") + nodo.etiqueta())
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
    for i, hijo in enumerate(nodo.hijos):
        lineas.extend(a_texto(hijo, nuevo_prefijo, i == len(nodo.hijos) - 1, False))
    return lineas


def imprimir(nodo):
    print("\n".join(a_texto(nodo)))


def derivacion_izquierda(raiz):
    """
    Reconstruye la derivación más a la izquierda que representa el árbol:
    en cada paso se reemplaza el no terminal más a la izquierda por el lado
    derecho de la regla aplicada en ese nodo.
    """
    def nombre(n):
        if n.token is not None:
            return n.token.lexema
        if n.simbolo == "ε":
            return ""
        return f"<{n.simbolo}>"

    forma = [raiz]
    pasos = [nombre(raiz)]
    while True:
        indice = next((i for i, n in enumerate(forma) if not n.es_terminal()), None)
        if indice is None:
            break
        nodo = forma[indice]
        forma = forma[:indice] + [h for h in nodo.hijos] + forma[indice + 1:]
        forma = [n for n in forma if n.simbolo != "ε"]
        pasos.append(" ".join(x for x in (nombre(n) for n in forma) if x))
    return pasos
