# U-Nota

Lenguaje de dominio específico para que los profesores registren notas y calculen promedios ponderados.
Proyecto de Teoría de Lenguajes Formales: AFD (Fase 1), gramática LL(1) en BNF (Fase 2) y analizador en Python (Fase 3).

## Requisitos

Python 3.8 o superior. No usa librerías externas.

## Uso

```
python unota.py ejemplos/curso_correcto.unota
python unota.py ejemplos/curso_correcto.unota --tokens
python unota.py ejemplos/minimo.unota --arbol --derivacion
python unota.py ejemplos/errores_sintacticos.unota
python unota.py ejemplos/minimo.unota --matriz
python unota.py ejemplos/curso_correcto.unota --arbol --salida arbol.txt
```

Sin opciones muestra la tabla de tokens, el árbol de derivación y el resultado de la ejecución.
Si hay errores léxicos o sintácticos muestra el listado de errores (con línea y columna) y no genera el árbol.

## Archivos

| Archivo | Contenido |
|---|---|
| `afd.py` | Alfabeto por clases, matriz de transiciones δ, estados de aceptación y de rechazo (Fase 1) |
| `tokens.py` | Categorías léxicas, palabras reservadas y símbolos (terminales de la gramática) |
| `lexer.py` | Analizador léxico: aplica la matriz δ carácter por carácter |
| `parser.py` | Analizador sintáctico descendente recursivo: una función por cada regla BNF (Fase 2) |
| `arbol.py` | Árbol de derivación y derivación más a la izquierda |
| `evaluador.py` | Fase semántica: pesos, notas, promedios, `mostrar` y `si ... sino` |
| `unota.py` | Programa principal |
| `ejemplos/` | Programas correctos y con errores léxicos, sintácticos y semánticos |
| `pruebas/` | Pruebas automáticas: `python -m unittest discover pruebas` |

## Ejemplo de programa

```
curso "Calculo I" {
  evaluacion parcial1 peso 30%;
  evaluacion parcial2 peso 30%;
  evaluacion final    peso 40%;

  estudiante "Ana Perez" {
    parcial1 = 4.2;
    parcial2 = 3.5;
    final    = (4.0 + 3.8) / 2;
  }

  mostrar promedio("Ana Perez");
  si promedio("Ana Perez") >= 3.0 entonces {
    mostrar "Aprobo";
  } sino {
    mostrar "Reprobo";
  }
}
```
