import os
import random
import time

import matplotlib
matplotlib.use("Agg")   # solo guarda las imágenes, no abre ventanas
import matplotlib.pyplot as plt

from Quadtreetree import Rect, Quadtree, brute_radius, brute_nearest, brute_k_nearest

# ======================================================================
# CONFIGURACIÓN
# ======================================================================
CARPETA = "graficas"
os.makedirs(CARPETA, exist_ok=True)

TAMANOS = [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
CONSULTAS = 200       # consultas aleatorias por tamaño (se promedia)
REPETICIONES = 3      # cada medición se repite y se toma la mejor (reduce el ruido)
RADIO = 500           # metros
CAPACIDAD = 4         # puntos por nodo antes de subdividir
LADO = 10000          # la ciudad mide LADO x LADO metros


# ======================================================================
# FUNCIONES AUXILIARES
# ======================================================================
def generar_puntos(n):
    return [(random.uniform(0, LADO), random.uniform(0, LADO)) for _ in range(n)]


def construir_arbol(puntos, capacidad=CAPACIDAD):
    arbol = Quadtree(Rect(LADO / 2, LADO / 2, LADO / 2, LADO / 2), capacidad)
    for p in puntos:
        arbol.insert(p)
    return arbol


def tiempo(funcion):
    """Ejecuta la función una vez y devuelve cuántos segundos tardó."""
    t0 = time.perf_counter()
    funcion()
    return time.perf_counter() - t0


def promedio_por_consulta(funcion, consultas):
    """Tiempo promedio (segundos) de una consulta, repitiéndola con todas las consultas."""
    total = tiempo(lambda: [funcion(qx, qy) for (qx, qy) in consultas])
    return total / len(consultas)


def mejor_de(funcion, repeticiones=REPETICIONES):
    """Repite una medición y se queda con la más rápida (la menos afectada por ruido)."""
    return min(funcion() for _ in range(repeticiones))


# ======================================================================
# MEDICIÓN
# ======================================================================
def medir(n, capacidad=CAPACIDAD):
    """Mide todos los tiempos para n puntos. Devuelve un diccionario (en segundos)."""
    random.seed(1)
    puntos = generar_puntos(n)
    consultas = [(random.uniform(0, LADO), random.uniform(0, LADO)) for _ in range(CONSULTAS)]

    arbol = construir_arbol(puntos, capacidad)

    return {
        "n": n,
        "construccion": mejor_de(lambda: tiempo(lambda: construir_arbol(puntos, capacidad))),
        "radio_bruta": mejor_de(lambda: promedio_por_consulta(
            lambda x, y: brute_radius(puntos, x, y, RADIO), consultas)),
        "radio_arbol": mejor_de(lambda: promedio_por_consulta(
            lambda x, y: arbol.query_radius(x, y, RADIO), consultas)),
        "vecino_bruta": mejor_de(lambda: promedio_por_consulta(
            lambda x, y: brute_nearest(puntos, x, y), consultas)),
        "vecino_arbol": mejor_de(lambda: promedio_por_consulta(
            lambda x, y: arbol.nearest(x, y), consultas)),
    }


# ======================================================================
# RESULTADOS
# ======================================================================
def imprimir_tabla(resultados):
    us = 1e6   # segundos -> microsegundos
    print("\nTiempos por consulta en microsegundos (µs); la construcción en milisegundos (ms)")
    print(f"{'N':>7} | {'Constr(ms)':>10} | {'Radio bruta':>11} | {'Radio árbol':>11} |"
          f" {'Vec. bruta':>10} | {'Vec. árbol':>10}")
    print("-" * 78)
    for r in resultados:
        print(f"{r['n']:>7} | {r['construccion'] * 1000:>10.2f} | {r['radio_bruta'] * us:>11.1f} |"
              f" {r['radio_arbol'] * us:>11.1f} | {r['vecino_bruta'] * us:>10.1f} |"
              f" {r['vecino_arbol'] * us:>10.1f}")


def primer_cruce(resultados, clave_bruta, clave_arbol):
    """Primer N donde el árbol es más rápido que la fuerza bruta (None si nunca)."""
    for r in resultados:
        if r[clave_arbol] < r[clave_bruta]:
            return r["n"]
    return None


def consultas_para_amortizar(r, clave_bruta, clave_arbol):
    """Cuántas consultas hacen falta para que construir el árbol valga la pena."""
    ahorro = r[clave_bruta] - r[clave_arbol]
    if ahorro <= 0:
        return None
    return r["construccion"] / ahorro


def graficar_comparacion(resultados, clave_bruta, clave_arbol, titulo, archivo):
    ns = [r["n"] for r in resultados]
    bruta = [r[clave_bruta] * 1e6 for r in resultados]
    arbol = [r[clave_arbol] * 1e6 for r in resultados]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(ns, bruta, marker="o", color="tab:red", label="Fuerza bruta")
    ax.plot(ns, arbol, marker="o", color="tab:blue", label="Quadtree")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Número de puntos (N)")
    ax.set_ylabel("Tiempo por consulta (µs)")
    ax.set_title(titulo)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)


def graficar_construccion(resultados, archivo="analisis_construccion.png"):
    ns = [r["n"] for r in resultados]
    tiempos = [r["construccion"] * 1000 for r in resultados]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(ns, tiempos, marker="o", color="tab:green")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Número de puntos (N)")
    ax.set_ylabel("Tiempo de construcción (ms)")
    ax.set_title("Costo de construir el Quadtree")
    ax.grid(True, which="both", alpha=0.3)
    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)


# ======================================================================
# EXPERIMENTO EXTRA: capacidad del nodo
# ======================================================================
def experimento_capacidad(n=10000, capacidades=(2, 4, 8, 16, 32)):
    print(f"\nEfecto de la capacidad del nodo (N = {n})")
    print(f"{'Capacidad':>9} | {'Constr(ms)':>10} | {'Radio árbol(µs)':>15} | {'Vec. árbol(µs)':>14}")
    print("-" * 58)
    filas = []
    for c in capacidades:
        r = medir(n, capacidad=c)
        filas.append((c, r))
        print(f"{c:>9} | {r['construccion'] * 1000:>10.2f} | {r['radio_arbol'] * 1e6:>15.1f} |"
              f" {r['vecino_arbol'] * 1e6:>14.1f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([c for c, _ in filas], [r["radio_arbol"] * 1e6 for _, r in filas],
            marker="o", label="Radio")
    ax.plot([c for c, _ in filas], [r["vecino_arbol"] * 1e6 for _, r in filas],
            marker="o", label="Vecino más cercano")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Capacidad del nodo")
    ax.set_ylabel("Tiempo por consulta (µs)")
    ax.set_title(f"Capacidad del nodo vs. tiempo de consulta (N = {n})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.savefig(os.path.join(CARPETA, "analisis_capacidad.png"), dpi=150)
    plt.close(fig)

# ======================================================================
# EXPERIMENTO: k VECINOS MÁS CERCANOS
# ======================================================================
K = 5   # cantidad de vecinos para la comparación por tamaño


def medir_k(n, k):
    """Tiempo promedio por consulta (en segundos) de k vecinos: (fuerza bruta, árbol)."""
    random.seed(1)
    puntos = generar_puntos(n)
    consultas = [(random.uniform(0, LADO), random.uniform(0, LADO)) for _ in range(CONSULTAS)]
    arbol = construir_arbol(puntos)

    t_bruta = mejor_de(lambda: promedio_por_consulta(
        lambda x, y: brute_k_nearest(puntos, x, y, k), consultas))
    t_arbol = mejor_de(lambda: promedio_por_consulta(
        lambda x, y: arbol.k_nearest_points(x, y, k), consultas))
    return t_bruta, t_arbol


def experimento_k():
    # --- Parte 1: tiempo contra N, con k fijo ---
    print(f"\nk = {K} vecinos más cercanos: tiempo por consulta (µs)")
    print(f"{'N':>7} | {'Fuerza bruta':>12} | {'Quadtree':>10}")
    print("-" * 36)
    ns, brutas, arboles = [], [], []
    for n in TAMANOS:
        t_b, t_a = medir_k(n, K)
        ns.append(n)
        brutas.append(t_b * 1e6)
        arboles.append(t_a * 1e6)
        print(f"{n:>7} | {t_b * 1e6:>12.1f} | {t_a * 1e6:>10.1f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(ns, brutas, marker="o", color="tab:red", label="Fuerza bruta")
    ax.plot(ns, arboles, marker="o", color="tab:blue", label="Quadtree")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Número de puntos (N)")
    ax.set_ylabel("Tiempo por consulta (µs)")
    ax.set_title(f"{K} vecinos más cercanos: fuerza bruta vs. Quadtree")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.savefig(os.path.join(CARPETA, "analisis_k_vecinos.png"), dpi=150)
    plt.close(fig)

    # --- Parte 2: tiempo contra k, con N fijo ---
    n = 10000
    ks = [1, 5, 10, 25, 50, 100]
    print(f"\nEfecto de k (N = {n}): tiempo por consulta (µs)")
    print(f"{'k':>5} | {'Fuerza bruta':>12} | {'Quadtree':>10}")
    print("-" * 34)
    brutas_k, arboles_k = [], []
    for k in ks:
        t_b, t_a = medir_k(n, k)
        brutas_k.append(t_b * 1e6)
        arboles_k.append(t_a * 1e6)
        print(f"{k:>5} | {t_b * 1e6:>12.1f} | {t_a * 1e6:>10.1f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(ks, brutas_k, marker="o", color="tab:red", label="Fuerza bruta")
    ax.plot(ks, arboles_k, marker="o", color="tab:blue", label="Quadtree")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("k (cantidad de vecinos)")
    ax.set_ylabel("Tiempo por consulta (µs)")
    ax.set_title(f"Efecto de k en el tiempo de consulta (N = {n})")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.savefig(os.path.join(CARPETA, "analisis_k_valor.png"), dpi=150)
    plt.close(fig)

# ======================================================================
# PROGRAMA PRINCIPAL
# ======================================================================
def main():
    resultados = []
    for n in TAMANOS:
        print(f"Midiendo N = {n} ...")
        resultados.append(medir(n))

    imprimir_tabla(resultados)

    graficar_comparacion(resultados, "radio_bruta", "radio_arbol",
                         f"Búsqueda por radio ({RADIO} m): fuerza bruta vs. Quadtree",
                         "analisis_radio.png")
    graficar_comparacion(resultados, "vecino_bruta", "vecino_arbol",
                         "Vecino más cercano: fuerza bruta vs. Quadtree",
                         "analisis_vecino.png")
    graficar_construccion(resultados)

    print("\n--- PUNTO DE CRUCE ---")
    for nombre, kb, ka in [("Radio", "radio_bruta", "radio_arbol"),
                           ("Vecino más cercano", "vecino_bruta", "vecino_arbol")]:
        n_cruce = primer_cruce(resultados, kb, ka)
        if n_cruce is None:
            print(f"{nombre}: el árbol no fue más rápido en ningún tamaño probado")
        else:
            print(f"{nombre}: el árbol empieza a ganar desde N = {n_cruce}")

    print("\n--- ¿CUÁNTAS CONSULTAS PARA AMORTIZAR LA CONSTRUCCIÓN? (N = 10000) ---")
    r10k = next(r for r in resultados if r["n"] == 10000)
    for nombre, kb, ka in [("Radio", "radio_bruta", "radio_arbol"),
                           ("Vecino más cercano", "vecino_bruta", "vecino_arbol")]:
        k = consultas_para_amortizar(r10k, kb, ka)
        if k is None:
            print(f"{nombre}: el árbol no ahorra tiempo por consulta")
        else:
            print(f"{nombre}: hacen falta unas {k:.0f} consultas")

    experimento_capacidad()
    experimento_k()
    print(f"\nGráficas guardadas en la carpeta '{CARPETA}/'")


if __name__ == "__main__":
    main()