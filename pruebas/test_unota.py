"""
Pruebas automáticas de U-Nota.
Ejecutar desde la carpeta del proyecto:  python -m unittest discover pruebas
"""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import afd          # noqa: E402
import evaluador    # noqa: E402
import lexer        # noqa: E402
import parser       # noqa: E402


def categorias(texto):
    tokens, errores = lexer.analizar(texto)
    return [t.categoria for t in tokens], errores


def ejecutar(texto):
    tokens, errores_lex = lexer.analizar(texto)
    raiz, errores_sin = parser.analizar(tokens)
    salida = []
    if errores_lex or errores_sin:
        return None, errores_lex, errores_sin, []
    errores_sem, _ = evaluador.ejecutar(raiz, salida.append)
    return salida, errores_lex, errores_sin, errores_sem


class PruebasAFD(unittest.TestCase):
    def test_cadenas_aceptadas(self):
        for cadena in ["parcial1", "nota_final", "30", "4.25", '"Ana Perez"', "<=", ">=", "==", "!=", "=", "%"]:
            aceptada, recorrido = afd.acepta(cadena)
            self.assertTrue(aceptada, f"{cadena}: {recorrido}")

    def test_cadenas_rechazadas(self):
        for cadena in ["4.", "!", '"sin cerrar', "_x", "1a", "@"]:
            aceptada, _ = afd.acepta(cadena)
            self.assertFalse(aceptada, cadena)

    def test_recorrido_real(self):
        _, recorrido = afd.acepta("4.25")
        self.assertEqual(recorrido, ["q0", "q2", "q3", "q4", "q4"])

    def test_matriz_completa(self):
        for estado, fila in afd.DELTA.items():
            self.assertEqual(len(fila), len(afd.COLUMNAS), estado)
            for destino in fila:
                self.assertIn(destino, afd.DELTA)


class PruebasLexico(unittest.TestCase):
    def test_palabras_reservadas_e_identificadores(self):
        cats, errores = categorias("curso cursos si sino entonces x1")
        self.assertEqual(cats, ["CURSO", "ID", "SI", "SINO", "ENTONCES", "ID", "FIN"])
        self.assertEqual(errores, [])

    def test_lexema_mas_largo(self):
        cats, _ = categorias("a<=b a<b a==b a=b a!=b")
        self.assertEqual(cats, ["ID", "MENOR_IGUAL", "ID", "ID", "MENOR", "ID", "ID", "IGUAL", "ID",
                                "ID", "ASIG", "ID", "ID", "DIFERENTE", "ID", "FIN"])

    def test_comentarios_y_tildes_en_cadena(self):
        cats, errores = categorias('# comentario con tildes: álgebra\nmostrar "Matemáticas";')
        self.assertEqual(cats, ["MOSTRAR", "CADENA", "PYC", "FIN"])
        self.assertEqual(errores, [])

    def test_errores_lexicos_con_posicion(self):
        _, errores = categorias("x = 4.;\ny @ 2")
        self.assertEqual([(e.fila, e.columna, e.estado) for e in errores], [(1, 5, "q3"), (2, 3, "q0")])


PROGRAMA = """
curso "Calculo" {
  evaluacion p1 peso 50%;
  evaluacion p2 peso 50%;
  estudiante "Ana" { p1 = 4.0; p2 = 3.0; }
  mostrar promedio("Ana");
  si promedio("Ana") >= 3.0 entonces { mostrar "aprobo"; } sino { mostrar "reprobo"; }
}
"""


class PruebasSintacticas(unittest.TestCase):
    def test_programa_valido(self):
        salida, el, es, esem = ejecutar(PROGRAMA)
        self.assertEqual((el, es, esem), ([], [], []))
        self.assertEqual(salida, ["== Curso: Calculo ==", "3.50", "aprobo"])

    def test_hojas_reconstruyen_el_programa(self):
        tokens, _ = lexer.analizar(PROGRAMA)
        raiz, _ = parser.analizar(tokens)
        self.assertEqual(raiz.hojas(), [t.lexema for t in tokens[:-1]])

    def test_precedencia_y_asociatividad(self):
        programa = ('curso "c" { evaluacion a peso 100%; estudiante "x" { a = 10 - 4 - 2 * 3 / 3 + 1; } '
                    'mostrar promedio("x"); }')
        salida, *_ = ejecutar(programa)
        self.assertEqual(salida[-1], "5.00")   # 10-4-2+1 = 5

    def test_si_anidado_sin_ambiguedad(self):
        programa = ('curso "c" { evaluacion a peso 100%; estudiante "x" { a = 2.0; } '
                    'si promedio("x") >= 3.0 entonces { si promedio("x") >= 4.0 entonces { mostrar "A"; } } '
                    'sino { mostrar "B"; } }')
        salida, *_ = ejecutar(programa)
        self.assertEqual(salida[-1], "B")

    def test_varios_errores_en_una_pasada(self):
        programa = ('curso "c" {\n evaluacion a peso 50%\n evaluacion b 50%;\n'
                    ' estudiante "x" { a 3; b = ; }\n mostrar ;\n}')
        _, _, errores, _ = ejecutar(programa)
        self.assertEqual([e.token.fila for e in errores], [3, 3, 4, 4, 5])

    def test_falta_llave_de_cierre(self):
        _, _, errores, _ = ejecutar('curso "c" { evaluacion a peso 100%;')
        self.assertEqual(len(errores), 1)
        self.assertIn("'}'", str(errores[0]))

    def test_archivo_vacio(self):
        _, _, errores, _ = ejecutar("")
        self.assertEqual(len(errores), 1)


class PruebasSemanticas(unittest.TestCase):
    def test_nota_fuera_de_rango_y_evaluacion_inexistente(self):
        programa = 'curso "c" { evaluacion a peso 100%; estudiante "x" { a = 6; b = 3; } }'
        _, _, _, errores = ejecutar(programa)
        self.assertEqual(len(errores), 2)

    def test_division_por_cero(self):
        programa = 'curso "c" { evaluacion a peso 100%; estudiante "x" { a = 3 / 0; } }'
        _, _, _, errores = ejecutar(programa)
        self.assertIn("división por cero", str(errores[0]))


if __name__ == "__main__":
    unittest.main()
