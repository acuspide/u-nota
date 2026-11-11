"""
Prueba de robustez: toma los programas de ejemplo correctos, les aplica
mutaciones aleatorias (borrar, insertar o cambiar caracteres) y verifica que
el analizador nunca se caiga ni se quede en un ciclo infinito: siempre debe
terminar con un árbol o con una lista de errores.

Uso (desde la carpeta del proyecto):  python pruebas/prueba_robustez.py [cantidad]
"""

import os
import random
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import evaluador  # noqa: E402
import lexer      # noqa: E402
import parser     # noqa: E402

PIEZAS = list('{}();=%+-*/<>!".#@ \n') + ["si", "sino", "curso", "mostrar", "entonces",
                                           "estudiante", "evaluacion", "x", "3.5", "promedio"]


def main():
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    base = ""
    for nombre in ("curso_correcto.unota", "dos_cursos.unota"):
        with open(os.path.join(RAIZ, "ejemplos", nombre), encoding="utf-8") as f:
            base += f.read()

    random.seed(1)
    for n in range(cantidad):
        texto = list(base)
        for _ in range(random.randint(1, 6)):
            i = random.randrange(len(texto))
            r = random.random()
            if r < 0.4:
                del texto[i]
            elif r < 0.8:
                texto.insert(i, random.choice(PIEZAS))
            else:
                texto[i] = random.choice(PIEZAS)
        texto = "".join(texto)

        inicio = time.time()
        tokens, errores_lex = lexer.analizar(texto)
        raiz, errores_sin = parser.analizar(tokens)
        if not errores_lex and not errores_sin:
            evaluador.ejecutar(raiz, lambda *a: None)
        if time.time() - inicio > 2:
            print(f"Mutación {n}: tardó demasiado")
            return 1
    print(f"{cantidad} programas mutados analizados sin fallos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
