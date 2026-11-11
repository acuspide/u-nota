"""
U-Nota: lenguaje de dominio específico para registrar notas y calcular promedios.

Uso:
    python unota.py <archivo.unota> [opciones]

Opciones:
    --tokens        muestra la tabla de tokens del analizador léxico
    --arbol         muestra el árbol de derivación sintáctica
    --derivacion    muestra la derivación más a la izquierda paso a paso
    --matriz        muestra la matriz de transiciones del AFD
    --salida ARCH   guarda el árbol de derivación en un archivo de texto
    --sin-ejecutar  solo analiza (léxico + sintáctico), no calcula notas

Sin opciones se muestran tokens, árbol y resultado de la ejecución.
"""

import argparse
import sys

import afd
import arbol
import evaluador
import lexer
import parser


def titulo(texto):
    print()
    print("=" * 60)
    print(texto)
    print("=" * 60)


def main(argumentos=None):
    ap = argparse.ArgumentParser(description="Analizador e intérprete del lenguaje U-Nota")
    ap.add_argument("archivo", help="archivo fuente .unota")
    ap.add_argument("--tokens", action="store_true")
    ap.add_argument("--arbol", action="store_true")
    ap.add_argument("--derivacion", action="store_true")
    ap.add_argument("--matriz", action="store_true")
    ap.add_argument("--salida")
    ap.add_argument("--sin-ejecutar", action="store_true")
    args = ap.parse_args(argumentos)

    todo = not (args.tokens or args.arbol or args.derivacion or args.matriz)

    try:
        with open(args.archivo, encoding="utf-8") as f:
            fuente = f.read()
    except OSError as e:
        print(f"No se pudo leer el archivo '{args.archivo}': {e.strerror}")
        return 2

    if args.matriz:
        titulo("MATRIZ DE TRANSICIONES DEL AFD")
        afd.imprimir_matriz()

    # 1. Análisis léxico
    tokens, errores_lexicos = lexer.analizar(fuente)
    if args.tokens or todo:
        titulo("1. ANÁLISIS LÉXICO: TOKENS")
        lexer.imprimir_tokens(tokens)

    # 2. Análisis sintáctico
    raiz, errores_sintacticos = parser.analizar(tokens)

    errores = [str(e) for e in errores_lexicos] + [str(e) for e in errores_sintacticos]
    if errores:
        titulo("LISTADO DE ERRORES")
        for e in errores:
            print("  - " + e)
        print(f"\nTotal: {len(errores_lexicos)} léxico(s), {len(errores_sintacticos)} sintáctico(s). "
              "No se genera el árbol de derivación.")
        return 1

    if args.arbol or todo:
        titulo("2. ÁRBOL DE DERIVACIÓN SINTÁCTICA")
        arbol.imprimir(raiz)

    if args.derivacion:
        titulo("DERIVACIÓN MÁS A LA IZQUIERDA")
        for i, paso in enumerate(arbol.derivacion_izquierda(raiz)):
            print(("    " if i == 0 else "  ⇒ ") + paso)

    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write("\n".join(arbol.a_texto(raiz)) + "\n")
        print(f"\nÁrbol guardado en {args.salida}")

    print("\nEl programa es sintácticamente correcto.")

    # 3. Ejecución (análisis semántico)
    if args.sin_ejecutar:
        return 0
    titulo("3. EJECUCIÓN")
    errores_semanticos, avisos = evaluador.ejecutar(raiz)
    for a in avisos:
        print(a)
    if errores_semanticos:
        print()
        for e in errores_semanticos:
            print("  - " + str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
