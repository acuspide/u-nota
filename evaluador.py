"""
Evaluador (fase semántica) de U-Nota.

Recorre el árbol de derivación que entrega el parser y ejecuta el programa:
registra evaluaciones con su peso, guarda las notas de cada estudiante,
calcula promedios ponderados y ejecuta 'mostrar' y 'si ... sino'.

Reglas semánticas:
  - Los pesos de las evaluaciones de un curso deben sumar 100 %.
  - Una nota solo puede asignarse a una evaluación declarada antes y debe
    estar entre 0.0 y 5.0 (escala colombiana).
  - Dentro de un estudiante, un ID en una expresión es una nota ya asignada
    a ese mismo estudiante.
  - promedio("Nombre") = Σ (nota_i × peso_i) / 100. Una evaluación sin nota
    cuenta como 0.0 y se avisa.
  - promedio() = promedio de los promedios de todos los estudiantes del curso.
"""

NOTA_MINIMA = 0.0
NOTA_MAXIMA = 5.0


class ErrorSemantico(Exception):
    def __init__(self, token, mensaje):
        self.token = token
        self.mensaje = mensaje
        super().__init__(str(self))

    def __str__(self):
        return f"Error semántico en línea {self.token.fila}, columna {self.token.columna}: {self.mensaje}"


class Curso:
    def __init__(self, nombre):
        self.nombre = nombre
        self.pesos = {}          # evaluación -> peso en %
        self.notas = {}          # estudiante -> {evaluación: nota}


def hijos_sin_epsilon(nodo):
    return [h for h in nodo.hijos if h.simbolo != "ε"]


def lexema_cadena(token):
    return token.lexema[1:-1]       # quitar las comillas


class Evaluador:
    def __init__(self, salida=print):
        self.salida = salida
        self.errores = []
        self.avisos = []
        self.curso = None
        self.estudiante = None      # nombre del estudiante que se está leyendo

    # --------------------------------------------------------------
    def ejecutar(self, raiz):
        self.recorrer_lista(raiz.hijos[0], "lista_cursos'", self.curso_nodo)

    def recorrer_lista(self, nodo, nombre_prima, accion):
        """Recorre <X> ::= <item> <X'> y <X'> ::= <item> <X'> | ε."""
        while nodo is not None:
            hijos = hijos_sin_epsilon(nodo)
            if not hijos:
                return
            item = hijos[0]
            if item.simbolo != "error":
                try:
                    accion(item)
                except ErrorSemantico as e:
                    self.errores.append(e)
            nodo = hijos[1] if len(hijos) > 1 and hijos[1].simbolo == nombre_prima else None

    # --------------------------------------------------------------
    def curso_nodo(self, nodo):
        # curso CADENA { <cuerpo> }
        token_nombre = nodo.hijos[1].token
        self.curso = Curso(lexema_cadena(token_nombre))
        self.salida(f"== Curso: {self.curso.nombre} ==")
        cuerpo = next(h for h in nodo.hijos if h.simbolo == "cuerpo")
        self.recorrer_lista(cuerpo, "cuerpo'", self.elemento)
        self.validar_pesos(token_nombre)

    def validar_pesos(self, token):
        total = sum(self.curso.pesos.values())
        if abs(total - 100) > 1e-9:
            self.avisos.append(
                f"Aviso (línea {token.fila}): en el curso '{self.curso.nombre}' los pesos suman {total:g}% y deberían sumar 100%.")

    def elemento(self, nodo):
        hijo = nodo.hijos[0]
        if hijo.simbolo == "evaluacion":
            self.evaluacion(hijo)
        elif hijo.simbolo == "estudiante":
            self.estudiante_nodo(hijo)
        else:
            self.sentencia(hijo)

    def evaluacion(self, nodo):
        # evaluacion ID peso NUM % ;
        token_id = nodo.hijos[1].token
        token_peso = nodo.hijos[3].token
        if token_id.lexema in self.curso.pesos:
            raise ErrorSemantico(token_id, f"la evaluación '{token_id.lexema}' ya fue declarada")
        peso = float(token_peso.lexema)
        if peso <= 0 or peso > 100:
            raise ErrorSemantico(token_peso, "el peso debe estar entre 0% y 100%")
        self.curso.pesos[token_id.lexema] = peso

    def estudiante_nodo(self, nodo):
        # estudiante CADENA { <notas> }
        token_nombre = nodo.hijos[1].token
        nombre = lexema_cadena(token_nombre)
        if nombre in self.curso.notas:
            raise ErrorSemantico(token_nombre, f"el estudiante '{nombre}' ya fue registrado en este curso")
        self.curso.notas[nombre] = {}
        self.estudiante = nombre
        try:
            notas = next(h for h in nodo.hijos if h.simbolo == "notas")
            self.recorrer_lista(notas, "notas'", self.nota)
        finally:
            self.estudiante = None

    def nota(self, nodo):
        # ID = <expr> ;
        token_id = nodo.hijos[0].token
        evaluacion = token_id.lexema
        if evaluacion not in self.curso.pesos:
            raise ErrorSemantico(token_id, f"'{evaluacion}' no es una evaluación declarada en el curso")
        valor = self.expr(nodo.hijos[2])
        if not (NOTA_MINIMA <= valor <= NOTA_MAXIMA):
            raise ErrorSemantico(token_id, f"la nota de '{evaluacion}' da {valor:.2f} y debe estar entre 0.0 y 5.0")
        self.curso.notas[self.estudiante][evaluacion] = valor

    # --------------------------------------------------------------
    def sentencia(self, nodo):
        hijo = nodo.hijos[0]
        if hijo.simbolo == "mostrar":
            self.mostrar(hijo)
        else:
            self.condicional(hijo)

    def mostrar(self, nodo):
        # mostrar <valor> ;
        valor = nodo.hijos[1].hijos[0]
        if valor.token is not None:              # CADENA
            self.salida(lexema_cadena(valor.token))
        else:
            self.salida(f"{self.expr(valor):.2f}")

    def condicional(self, nodo):
        # si <cond> entonces <bloque> <resto_si>
        if self.cond(nodo.hijos[1]):
            self.bloque(nodo.hijos[3])
        else:
            resto = nodo.hijos[4]
            if resto.hijos[0].simbolo == "SINO":
                self.bloque(resto.hijos[1])

    def bloque(self, nodo):
        # { <sentencias> }
        self.recorrer_lista(nodo.hijos[1], "sentencias'", self.sentencia)

    def cond(self, nodo):
        izq = self.expr(nodo.hijos[0])
        op = nodo.hijos[1].hijos[0].simbolo
        der = self.expr(nodo.hijos[2])
        return {
            "MENOR": izq < der,
            "MENOR_IGUAL": izq <= der,
            "MAYOR": izq > der,
            "MAYOR_IGUAL": izq >= der,
            "IGUAL": abs(izq - der) < 1e-9,
            "DIFERENTE": abs(izq - der) >= 1e-9,
        }[op]

    # --------------------------------------------------------------
    # Expresiones: <expr> ::= <termino> <expr'>, etc.
    # El árbol LL(1) se recorre acumulando de izquierda a derecha, lo que
    # respeta la asociatividad por la izquierda de + - * /.
    # --------------------------------------------------------------
    def expr(self, nodo):
        acumulado = self.termino(nodo.hijos[0])
        prima = nodo.hijos[1]
        while prima.hijos[0].simbolo != "ε":
            operador, termino, prima = prima.hijos
            valor = self.termino(termino)
            acumulado = acumulado + valor if operador.simbolo == "MAS" else acumulado - valor
        return acumulado

    def termino(self, nodo):
        acumulado = self.factor(nodo.hijos[0])
        prima = nodo.hijos[1]
        while prima.hijos[0].simbolo != "ε":
            operador, factor, prima = prima.hijos
            valor = self.factor(factor)
            if operador.simbolo == "POR":
                acumulado *= valor
            else:
                if valor == 0:
                    raise ErrorSemantico(operador.token, "división por cero")
                acumulado /= valor
        return acumulado

    def factor(self, nodo):
        primero = nodo.hijos[0]
        if primero.simbolo == "PAR_IZQ":
            return self.expr(nodo.hijos[1])
        if primero.simbolo == "NUM":
            return float(primero.token.lexema)
        if primero.simbolo == "ID":
            return self.valor_id(primero.token)
        # promedio ( <arg> )
        arg = nodo.hijos[2]
        if arg.hijos[0].simbolo == "ε":
            return self.promedio_curso(primero.token)
        return self.promedio_estudiante(arg.hijos[0].token)

    def valor_id(self, token):
        if self.estudiante is None:
            raise ErrorSemantico(token, f"'{token.lexema}' solo puede usarse dentro del bloque de un estudiante")
        notas = self.curso.notas[self.estudiante]
        if token.lexema not in notas:
            raise ErrorSemantico(token, f"'{token.lexema}' todavía no tiene nota para {self.estudiante}")
        return notas[token.lexema]

    def promedio_estudiante(self, token):
        nombre = lexema_cadena(token)
        if nombre not in self.curso.notas:
            raise ErrorSemantico(token, f"el estudiante '{nombre}' no está registrado (antes de esta línea) en el curso")
        return self.calcular_promedio(nombre, token)

    def calcular_promedio(self, nombre, token):
        notas = self.curso.notas[nombre]
        faltantes = [e for e in self.curso.pesos if e not in notas]
        if faltantes:
            aviso = (f"Aviso (línea {token.fila}): a '{nombre}' le falta nota en "
                     f"{', '.join(faltantes)}; se cuenta como 0.0.")
            if aviso not in self.avisos:
                self.avisos.append(aviso)
        return sum(notas.get(e, 0.0) * peso for e, peso in self.curso.pesos.items()) / 100

    def promedio_curso(self, token):
        if not self.curso.notas:
            raise ErrorSemantico(token, "promedio() necesita al menos un estudiante registrado")
        promedios = [self.calcular_promedio(n, token) for n in self.curso.notas]
        return sum(promedios) / len(promedios)


def ejecutar(raiz, salida=print):
    ev = Evaluador(salida)
    ev.ejecutar(raiz)
    return ev.errores, ev.avisos
