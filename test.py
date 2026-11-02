import os
import random
import math
import unittest

import matplotlib
matplotlib.use("Agg")   # solo guarda las imágenes, no abre ventanas
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from Quadtreetree import Rect, Quadtree, brute_radius, brute_nearest, brute_k_nearest

# Carpeta donde se guardan las gráficas (se crea una sola vez)
CARPETA = "graficas"
os.makedirs(CARPETA, exist_ok=True)


# ======================================================================
# PRUEBAS UNITARIAS
# ======================================================================
class TestQuadtree(unittest.TestCase):

    def setUp(self):
        # Se ejecuta antes de cada prueba: crea los datos y el árbol
        random.seed(42)
        self.puntos = [(random.uniform(0, 10000), random.uniform(0, 10000)) for _ in range(10000)]
        self.arbol = Quadtree(Rect(5000, 5000, 5000, 5000), capacity=4)
        for p in self.puntos:
            self.arbol.insert(p)

    def test_count(self):
        # El árbol debe tener exactamente los 10.000 puntos
        self.assertEqual(self.arbol.count(), 10000)

    def test_radio_centro(self):
        # Radio de 500 m en (5000, 5000): debe dar 69 puntos e igualar a fuerza bruta
        r_arbol = self.arbol.query_radius(5000, 5000, 500)
        r_bruta = brute_radius(self.puntos, 5000, 5000, 500)

        self.assertEqual(len(r_arbol), 69)
        self.assertEqual(set(r_arbol), set(r_bruta))

    def test_radio_aleatorio(self):
        # 100 consultas aleatorias: el árbol y la fuerza bruta deben dar el mismo conjunto
        for _ in range(100):
            qx = random.uniform(0, 10000)
            qy = random.uniform(0, 10000)
            qr = random.uniform(100, 1000)

            r_arbol = self.arbol.query_radius(qx, qy, qr)
            r_bruta = brute_radius(self.puntos, qx, qy, qr)

            self.assertEqual(set(r_arbol), set(r_bruta))

    def test_vecino_aleatorio(self):
        # 100 consultas aleatorias: el vecino más cercano debe coincidir con la fuerza bruta
        for _ in range(100):
            qx = random.uniform(0, 10000)
            qy = random.uniform(0, 10000)

            mejor_arbol = self.arbol.nearest(qx, qy)
            vecino_bruta, dist_bruta = brute_nearest(self.puntos, qx, qy)

            # El punto debe coincidir exactamente
            self.assertEqual(mejor_arbol[0], vecino_bruta)

    def test_radio_sin_resultados(self):
        # Un círculo diminuto (r=0.001) en la esquina debe devolver lista vacía
        r_arbol = self.arbol.query_radius(0, 0, 0.001)
        self.assertEqual(r_arbol, [])

    def test_k_vecinos_aleatorio(self):
        # 100 consultas aleatorias: los 5 más cercanos deben coincidir con la fuerza bruta
        for _ in range(100):
            qx = random.uniform(0, 10000)
            qy = random.uniform(0, 10000)

            r_arbol = self.arbol.k_nearest_points(qx, qy, 5)
            r_bruta = brute_k_nearest(self.puntos, qx, qy, 5)

            self.assertEqual([p for p, _ in r_arbol], [p for p, _ in r_bruta])

# ======================================================================
# VISUALIZACIONES
# ======================================================================
def graficar_radio(puntos, x, y, r, encontrados, archivo="radio.png"):
    fig, ax = plt.subplots(figsize=(8, 8))

    # 1. Todos los puntos en gris claro y pequeños
    x_todos = [p[0] for p in puntos]
    y_todos = [p[1] for p in puntos]
    ax.scatter(x_todos, y_todos, s=2, color="lightgray")

    # 2. Puntos dentro del radio, de otro color y más grandes
    if encontrados:
        x_enc = [p[0] for p in encontrados]
        y_enc = [p[1] for p in encontrados]
        ax.scatter(x_enc, y_enc, s=20, color="tab:blue")

    # 3. Círculo de búsqueda en rojo
    ax.add_patch(Circle((x, y), r, fill=False, color="red"))

    # 4. Centro de la búsqueda (estrella roja)
    ax.scatter([x], [y], marker="*", s=150, color="red")

    ax.set_aspect("equal")   # evita que el círculo se vea ovalado
    ax.set_title(f"Radio {r} m: {len(encontrados)} puntos encontrados")

    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)           # no la muestra, solo la guarda


def graficar_vecino(puntos, x, y, vecino, distancia, archivo="vecino.png", zoom=150):
    fig, ax = plt.subplots(figsize=(8, 8))

    # 1. Todos los puntos de entrega
    x_todos = [p[0] for p in puntos]
    y_todos = [p[1] for p in puntos]
    ax.scatter(x_todos, y_todos, s=25, color="gray", label="Puntos de entrega")

    # 2. Círculo con radio = distancia al vecino (no debe haber otro punto adentro)
    ax.add_patch(Circle((x, y), distancia, fill=False, linestyle="--", color="green"))

    # 3. Línea del punto de consulta al vecino
    ax.plot([x, vecino[0]], [y, vecino[1]], color="green")

    # 4. Vecino más cercano y punto de consulta
    ax.scatter([vecino[0]], [vecino[1]], s=80, color="tab:blue", label="Vecino más cercano")
    ax.scatter([x], [y], marker="*", s=250, color="red", label="Consulta")

    # 5. Zoom alrededor del punto (31 m en un mapa de 10.000 m no se verían)
    ax.set_xlim(x - zoom, x + zoom)
    ax.set_ylim(y - zoom, y + zoom)

    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(f"Vecino más cercano: a {distancia:.1f} m")
    ax.legend(loc="upper right")

    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)

def graficar_k_vecinos(puntos, x, y, vecinos, archivo="k_vecinos.png"):
    fig, ax = plt.subplots(figsize=(8, 8))

    x_todos = [p[0] for p in puntos]
    y_todos = [p[1] for p in puntos]
    ax.scatter(x_todos, y_todos, s=25, color="gray", label="Puntos de entrega")

    # Círculo hasta el k-ésimo vecino: adentro no hay ningún otro punto
    radio_k = vecinos[-1][1]
    ax.add_patch(Circle((x, y), radio_k, fill=False, linestyle="--", color="green"))

    # Los k vecinos, numerados del más cercano al más lejano
    for i, (p, d) in enumerate(vecinos, start=1):
        ax.plot([x, p[0]], [y, p[1]], color="green", alpha=0.5)
        ax.scatter([p[0]], [p[1]], s=80, color="tab:blue")
        ax.annotate(f"{i} ({d:.0f} m)", (p[0], p[1]), textcoords="offset points", xytext=(6, 6))

    ax.scatter([x], [y], marker="*", s=250, color="red", label="Consulta")

    zoom = radio_k * 1.5
    ax.set_xlim(x - zoom, x + zoom)
    ax.set_ylim(y - zoom, y + zoom)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(f"{len(vecinos)} vecinos más cercanos")
    ax.legend(loc="upper right")

    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)

def generar_graficas():
    # Mismos datos y árbol que en las pruebas
    random.seed(42)
    puntos = [(random.uniform(0, 10000), random.uniform(0, 10000)) for _ in range(10000)]
    arbol = Quadtree(Rect(5000, 5000, 5000, 5000), capacity=4)
    for p in puntos:
        arbol.insert(p)

    # Gráfica 1: búsqueda por radio
    cx, cy, radio = 5000, 5000, 500
    resultado_radio = arbol.query_radius(cx, cy, radio)
    graficar_radio(puntos, cx, cy, radio, resultado_radio, "resultado_radio.png")

    # Gráfica 2: vecino más cercano
    mejor = arbol.nearest(cx, cy)
    vecino_punto = mejor[0]
    distancia_m = math.sqrt(mejor[1])
    graficar_vecino(puntos, cx, cy, vecino_punto, distancia_m, "vecino.png")

    print(f"Gráficas guardadas en la carpeta '{CARPETA}/'")

    # Gráfica 3: los 5 vecinos más cercanos
    vecinos = arbol.k_nearest_points(cx, cy, 5)
    graficar_k_vecinos(puntos, cx, cy, vecinos, "k_vecinos.png")


# ======================================================================
# EJECUCIÓN
# ======================================================================
if __name__ == "__main__":
    generar_graficas()
    resultado = unittest.main(exit=False).result

    # Análisis de las pruebas realizadas
    print("\n--- ANÁLISIS DE LAS PRUEBAS ---")
    print(f"Pruebas ejecutadas: {resultado.testsRun}")
    print(f"Fallos: {len(resultado.failures)} | Errores: {len(resultado.errors)}")
    print("Se compararon el Quadtree y la fuerza bruta con 100 consultas aleatorias")
    print("de radio y 100 de vecino más cercano, además de una consulta de 500 m en el centro.")
    print("Si no hay fallos ni errores, el Quadtree devuelve los mismos resultados que la fuerza bruta.")