"""
Analizador sintáctico descendente recursivo (LL(1)) de U-Nota.

Cada no terminal de la gramática final de la Fase 2 (sin recursividad por la
izquierda y factorizada) es una función de esta clase. El comentario encima
de cada función es la regla BNF que implementa. Para decidir qué alternativa
aplicar se mira un solo token (el token actual) y se compara con los
conjuntos PRIMERO / SIGUIENTE calculados en el documento.
"""

import sys

from arbol import Nodo
from tokens import FIN, describir

sys.setrecursionlimit(10000)

# ---------------------------------------------------------------------------
# Conjuntos PRIMERO y SIGUIENTE (tabla de la Fase 2)
# ---------------------------------------------------------------------------
PRIMERO_CURSO = {"CURSO"}
PRIMERO_ELEMENTO = {"EVALUACION", "ESTUDIANTE", "MOSTRAR", "SI"}
PRIMERO_SENTENCIA = {"MOSTRAR", "SI"}
PRIMERO_NOTA = {"ID"}
PRIMERO_EXPR = {"PAR_IZQ", "NUM", "ID", "PROMEDIO"}
OPERADORES_RELACIONALES = {"MENOR", "MENOR_IGUAL", "MAYOR", "MAYOR_IGUAL", "IGUAL", "DIFERENTE"}

SIGUIENTE_LISTA_CURSOS_P = {FIN}
SIGUIENTE_CUERPO_P = {"LLAVE_DER"}
SIGUIENTE_NOTAS_P = {"LLAVE_DER"}
SIGUIENTE_SENTENCIAS_P = {"LLAVE_DER"}

# Tokens donde el parser puede retomar el análisis después de un error.
PUNTOS_DE_RECUPERACION = PRIMERO_ELEMENTO | {"CURSO", "LLAVE_DER", FIN}


class ErrorSintactico(Exception):
    def __init__(self, token, esperado, regla):
        self.token = token
        self.esperado = esperado
        self.regla = regla
        super().__init__(str(self))

    def __str__(self):
        encontrado = "el fin del archivo" if self.token.categoria == FIN else f"'{self.token.lexema}'"
        return (f"Error sintáctico en línea {self.token.fila}, columna {self.token.columna}: "
                f"se esperaba {self.esperado} y se encontró {encontrado}. "
                f"[regla {self.regla}]")


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errores = []

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @property
    def actual(self):
        return self.tokens[self.pos]

    def consumir(self):
        token = self.actual
        if token.categoria != FIN:
            self.pos += 1
        return token

    def esperar(self, categoria, padre, regla):
        """Si el token actual es 'categoria' lo agrega como hoja; si no, error."""
        if self.actual.categoria == categoria:
            return padre.agregar(Nodo(categoria, self.consumir()))
        raise ErrorSintactico(self.actual, describir(categoria), regla)

    def lista_esperados(self, categorias):
        return ", ".join(sorted(describir(c) for c in categorias))

    def sincronizar(self):
        """
        Recuperación en modo pánico: se descartan tokens hasta un ';'
        (que también se descarta) o hasta un token donde puede empezar o
        terminar una construcción (evaluacion, estudiante, mostrar, si,
        curso, '}' o fin de archivo).
        Si en lo descartado se abre un bloque '{', se descarta completo hasta
        su '}' para no confundir esa llave con la que cierra el curso.
        """
        while self.actual.categoria not in PUNTOS_DE_RECUPERACION:
            token = self.consumir()
            if token.categoria == "PYC":
                return
            if token.categoria == "LLAVE_IZQ":
                profundidad = 1
                while profundidad > 0 and self.actual.categoria != FIN:
                    c = self.consumir().categoria
                    if c == "LLAVE_IZQ":
                        profundidad += 1
                    elif c == "LLAVE_DER":
                        profundidad -= 1
                return

    def protegido(self, funcion):
        """Analiza un elemento de una lista; si falla, registra el error y sincroniza."""
        try:
            return funcion()
        except ErrorSintactico as error:
            self.errores.append(error)
            self.sincronizar()
            return Nodo("error")

    def contenido_de_bloque(self, funcion, padre):
        """
        Analiza lo que va entre '{' y '}' (cuerpo, notas o sentencias).
        Si el bloque está vacío o empieza mal, se reporta el error y se
        sincroniza dentro del bloque, para que la llave '}' siga cerrando
        el bloque correcto.
        """
        try:
            padre.agregar(funcion())
        except ErrorSintactico as error:
            self.errores.append(error)
            if self.actual.categoria != "LLAVE_DER":
                self.sincronizar()

    def token_inesperado(self, esperados, regla):
        """Un token que no puede empezar ni cerrar la lista actual: se reporta y se salta."""
        self.errores.append(ErrorSintactico(self.actual, esperados, regla))
        inicio = self.pos
        self.sincronizar()
        if self.pos == inicio:
            self.consumir()

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------
    def analizar(self):
        raiz = self.programa()
        if self.actual.categoria != FIN:
            self.errores.append(ErrorSintactico(self.actual, "el fin del archivo", "1"))
        return raiz

    # (1) <programa> ::= <lista_cursos>
    def programa(self):
        nodo = Nodo("programa")
        nodo.agregar(self.lista_cursos())
        return nodo

    # (2) <lista_cursos> ::= <curso> <lista_cursos'>
    def lista_cursos(self):
        nodo = Nodo("lista_cursos")
        nodo.agregar(self.curso())
        nodo.agregar(self.lista_cursos_p())
        return nodo

    # Nota sobre las funciones <X'> de listas: el "while True" no es parte de
    # la gramática; solo vuelve a intentar la misma regla después de saltar
    # un token inesperado (recuperación de errores). Sin errores se ejecuta
    # una sola vez y la repetición la hace la llamada recursiva, igual que
    # en la regla BNF.

    # (3) <lista_cursos'> ::= <curso> <lista_cursos'> | ε
    def lista_cursos_p(self):
        nodo = Nodo("lista_cursos'")
        while True:
            if self.actual.categoria in PRIMERO_CURSO:
                nodo.agregar(self.curso())
                nodo.agregar(self.lista_cursos_p())
                return nodo
            if self.actual.categoria in SIGUIENTE_LISTA_CURSOS_P:
                nodo.agregar(Nodo("ε"))
                return nodo
            self.token_inesperado("'curso' o el fin del archivo", "3")

    # (4) <curso> ::= curso CADENA { <cuerpo> }
    def curso(self):
        nodo = Nodo("curso")
        try:
            self.esperar("CURSO", nodo, "4")
            self.esperar("CADENA", nodo, "4")
            self.esperar("LLAVE_IZQ", nodo, "4")
        except ErrorSintactico as error:
            # Encabezado mal escrito: se reporta y se intenta seguir con el cuerpo.
            self.errores.append(error)
            while self.actual.categoria not in PRIMERO_ELEMENTO | {"LLAVE_IZQ", FIN}:
                self.consumir()
            if self.actual.categoria == "LLAVE_IZQ":
                self.consumir()
            elif self.actual.categoria == FIN:
                return nodo
        self.contenido_de_bloque(self.cuerpo, nodo)
        try:
            self.esperar("LLAVE_DER", nodo, "4")
        except ErrorSintactico as error:
            self.errores.append(error)
        return nodo

    # (5) <cuerpo> ::= <elemento> <cuerpo'>
    def cuerpo(self):
        nodo = Nodo("cuerpo")
        if self.actual.categoria not in PRIMERO_ELEMENTO:
            raise ErrorSintactico(self.actual, self.lista_esperados(PRIMERO_ELEMENTO), "5")
        nodo.agregar(self.protegido(self.elemento))
        nodo.agregar(self.cuerpo_p())
        return nodo

    # (6) <cuerpo'> ::= <elemento> <cuerpo'> | ε
    def cuerpo_p(self):
        nodo = Nodo("cuerpo'")
        while True:
            if self.actual.categoria in PRIMERO_ELEMENTO:
                nodo.agregar(self.protegido(self.elemento))
                nodo.agregar(self.cuerpo_p())
                return nodo
            if self.actual.categoria in SIGUIENTE_CUERPO_P or self.actual.categoria in {"CURSO", FIN}:
                nodo.agregar(Nodo("ε"))
                return nodo
            self.token_inesperado(self.lista_esperados(PRIMERO_ELEMENTO | {"LLAVE_DER"}), "6")

    # (7) <elemento> ::= <evaluacion> | <estudiante> | <sentencia>
    def elemento(self):
        nodo = Nodo("elemento")
        c = self.actual.categoria
        if c == "EVALUACION":
            nodo.agregar(self.evaluacion())
        elif c == "ESTUDIANTE":
            nodo.agregar(self.estudiante())
        elif c in PRIMERO_SENTENCIA:
            nodo.agregar(self.sentencia())
        else:
            raise ErrorSintactico(self.actual, self.lista_esperados(PRIMERO_ELEMENTO), "7")
        return nodo

    # (8) <evaluacion> ::= evaluacion ID peso NUM % ;
    def evaluacion(self):
        nodo = Nodo("evaluacion")
        for categoria in ("EVALUACION", "ID", "PESO", "NUM", "PORCENTAJE", "PYC"):
            self.esperar(categoria, nodo, "8")
        return nodo

    # (9) <estudiante> ::= estudiante CADENA { <notas> }
    def estudiante(self):
        nodo = Nodo("estudiante")
        self.esperar("ESTUDIANTE", nodo, "9")
        self.esperar("CADENA", nodo, "9")
        self.esperar("LLAVE_IZQ", nodo, "9")
        self.contenido_de_bloque(self.notas, nodo)
        self.esperar("LLAVE_DER", nodo, "9")
        return nodo

    # (10) <notas> ::= <nota> <notas'>
    def notas(self):
        nodo = Nodo("notas")
        if self.actual.categoria not in PRIMERO_NOTA:
            raise ErrorSintactico(self.actual, "un identificador de evaluación", "10")
        nodo.agregar(self.protegido(self.nota))
        nodo.agregar(self.notas_p())
        return nodo

    # (11) <notas'> ::= <nota> <notas'> | ε
    def notas_p(self):
        nodo = Nodo("notas'")
        while True:
            if self.actual.categoria in PRIMERO_NOTA:
                nodo.agregar(self.protegido(self.nota))
                nodo.agregar(self.notas_p())
                return nodo
            if self.actual.categoria in SIGUIENTE_NOTAS_P or self.actual.categoria in PUNTOS_DE_RECUPERACION:
                # Si no es '}', la regla (9) reportará que falta cerrar el estudiante.
                nodo.agregar(Nodo("ε"))
                return nodo
            self.token_inesperado("un identificador de evaluación o '}'", "11")

    # (12) <nota> ::= ID = <expr> ;
    def nota(self):
        nodo = Nodo("nota")
        self.esperar("ID", nodo, "12")
        self.esperar("ASIG", nodo, "12")
        nodo.agregar(self.expr())
        self.esperar("PYC", nodo, "12")
        return nodo

    # (13) <sentencia> ::= <mostrar> | <condicional>
    def sentencia(self):
        nodo = Nodo("sentencia")
        if self.actual.categoria == "MOSTRAR":
            nodo.agregar(self.mostrar())
        elif self.actual.categoria == "SI":
            nodo.agregar(self.condicional())
        else:
            raise ErrorSintactico(self.actual, "'mostrar' o 'si'", "13")
        return nodo

    # (14) <mostrar> ::= mostrar <valor> ;
    def mostrar(self):
        nodo = Nodo("mostrar")
        self.esperar("MOSTRAR", nodo, "14")
        nodo.agregar(self.valor())
        self.esperar("PYC", nodo, "14")
        return nodo

    # (15) <valor> ::= <expr> | CADENA
    def valor(self):
        nodo = Nodo("valor")
        if self.actual.categoria in PRIMERO_EXPR:
            nodo.agregar(self.expr())
        elif self.actual.categoria == "CADENA":
            self.esperar("CADENA", nodo, "15")
        else:
            raise ErrorSintactico(self.actual, "una expresión o una cadena", "15")
        return nodo

    # (16) <condicional> ::= si <cond> entonces <bloque> <resto_si>
    def condicional(self):
        nodo = Nodo("condicional")
        self.esperar("SI", nodo, "16")
        nodo.agregar(self.cond())
        self.esperar("ENTONCES", nodo, "16")
        nodo.agregar(self.bloque())
        nodo.agregar(self.resto_si())
        return nodo

    # (17) <resto_si> ::= sino <bloque> | ε
    def resto_si(self):
        nodo = Nodo("resto_si")
        if self.actual.categoria == "SINO":
            self.esperar("SINO", nodo, "17")
            nodo.agregar(self.bloque())
        else:
            nodo.agregar(Nodo("ε"))
        return nodo

    # (18) <bloque> ::= { <sentencias> }
    def bloque(self):
        nodo = Nodo("bloque")
        self.esperar("LLAVE_IZQ", nodo, "18")
        self.contenido_de_bloque(self.sentencias, nodo)
        self.esperar("LLAVE_DER", nodo, "18")
        return nodo

    # (19) <sentencias> ::= <sentencia> <sentencias'>
    def sentencias(self):
        nodo = Nodo("sentencias")
        if self.actual.categoria not in PRIMERO_SENTENCIA:
            raise ErrorSintactico(self.actual, "'mostrar' o 'si'", "19")
        nodo.agregar(self.protegido(self.sentencia))
        nodo.agregar(self.sentencias_p())
        return nodo

    # (20) <sentencias'> ::= <sentencia> <sentencias'> | ε
    def sentencias_p(self):
        nodo = Nodo("sentencias'")
        while True:
            if self.actual.categoria in PRIMERO_SENTENCIA:
                nodo.agregar(self.protegido(self.sentencia))
                nodo.agregar(self.sentencias_p())
                return nodo
            if self.actual.categoria in SIGUIENTE_SENTENCIAS_P or self.actual.categoria in PUNTOS_DE_RECUPERACION:
                nodo.agregar(Nodo("ε"))
                return nodo
            self.token_inesperado("'mostrar', 'si' o '}'", "20")

    # (21) <cond> ::= <expr> <oprel> <expr>
    def cond(self):
        nodo = Nodo("cond")
        nodo.agregar(self.expr())
        nodo.agregar(self.oprel())
        nodo.agregar(self.expr())
        return nodo

    # (22) <oprel> ::= < | <= | > | >= | == | !=
    def oprel(self):
        nodo = Nodo("oprel")
        if self.actual.categoria in OPERADORES_RELACIONALES:
            nodo.agregar(Nodo(self.actual.categoria, self.consumir()))
            return nodo
        raise ErrorSintactico(self.actual, "un operador relacional (<, <=, >, >=, ==, !=)", "22")

    # (23) <expr> ::= <termino> <expr'>
    def expr(self):
        nodo = Nodo("expr")
        nodo.agregar(self.termino())
        nodo.agregar(self.expr_p())
        return nodo

    # (24) <expr'> ::= + <termino> <expr'> | - <termino> <expr'> | ε
    def expr_p(self):
        nodo = Nodo("expr'")
        if self.actual.categoria in ("MAS", "MENOS"):
            nodo.agregar(Nodo(self.actual.categoria, self.consumir()))
            nodo.agregar(self.termino())
            nodo.agregar(self.expr_p())
        else:
            nodo.agregar(Nodo("ε"))
        return nodo

    # (25) <termino> ::= <factor> <termino'>
    def termino(self):
        nodo = Nodo("termino")
        nodo.agregar(self.factor())
        nodo.agregar(self.termino_p())
        return nodo

    # (26) <termino'> ::= * <factor> <termino'> | / <factor> <termino'> | ε
    def termino_p(self):
        nodo = Nodo("termino'")
        if self.actual.categoria in ("POR", "DIV"):
            nodo.agregar(Nodo(self.actual.categoria, self.consumir()))
            nodo.agregar(self.factor())
            nodo.agregar(self.termino_p())
        else:
            nodo.agregar(Nodo("ε"))
        return nodo

    # (27) <factor> ::= ( <expr> ) | NUM | ID | promedio ( <arg> )
    def factor(self):
        nodo = Nodo("factor")
        c = self.actual.categoria
        if c == "PAR_IZQ":
            self.esperar("PAR_IZQ", nodo, "27")
            nodo.agregar(self.expr())
            self.esperar("PAR_DER", nodo, "27")
        elif c == "NUM":
            self.esperar("NUM", nodo, "27")
        elif c == "ID":
            self.esperar("ID", nodo, "27")
        elif c == "PROMEDIO":
            self.esperar("PROMEDIO", nodo, "27")
            self.esperar("PAR_IZQ", nodo, "27")
            nodo.agregar(self.arg())
            self.esperar("PAR_DER", nodo, "27")
        else:
            raise ErrorSintactico(self.actual, "un número, un identificador, 'promedio' o '('", "27")
        return nodo

    # (28) <arg> ::= CADENA | ε
    def arg(self):
        nodo = Nodo("arg")
        if self.actual.categoria == "CADENA":
            self.esperar("CADENA", nodo, "28")
        else:
            nodo.agregar(Nodo("ε"))
        return nodo


def analizar(tokens):
    """Devuelve (árbol de derivación, lista de errores sintácticos)."""
    parser = Parser(tokens)
    raiz = parser.analizar()
    return raiz, parser.errores
