
import math

def brute_radius(puntos,x,y,r):
    resultado = []
    for p in puntos:                                    #recorro cada punto de la lista
        dist2 = (p[0]-x)**2 + (p[1]-y)**2                  #calculo la distacia al cuadrado entre el punto y el centro del circulo
        if dist2 <= r**2:                                 #si la distancia al cuadrado es menor o igual al radio al cuadrado
            resultado.append(p)                            #agrego el punto a la lista de resultados
    return resultado

def brute_nearest(puntos, x, y):
    mejor = None                    # el punto más cercano que he visto hasta ahora
    mejor_dist2 = float('inf')      # su distancia (al cuadrado); empieza en "infinito"

    for p in puntos:
        dist2 = (p[0]-x)**2 + (p[1]-y)**2                # distancia al cuadrado de p a (x, y) igual que alnterior metodo
        if dist2 < mejor_dist2:     # p está más cerca que el mejor que llevo?
            mejor = p        # entonces p pasa a ser el mejor (y guardo su distancia)
            mejor_dist2 = dist2
    return mejor, math.sqrt(mejor_dist2)

def brute_k_nearest(puntos, x, y, k):
    lista = []
    for p in puntos:
        dist2 = (p[0] - x)**2 + (p[1] - y)**2
        lista.append((dist2, p))
    lista.sort()                                  # ordena por distancia al cuadrado

    resultado = []
    for dist2, p in lista[:k]:                    # solo los primeros k
        resultado.append((p, math.sqrt(dist2)))
    return resultado

class Rect: 
    def __init__(self, dx, dy, w, h):
        self.dx = dx
        self.dy = dy   
        self.w = w     #horizontal
        self.h = h     #vertical

    def contains(self, p):                                                        #lo que se hace es que devuelve true si el punto esta dentro del rectangulo y false si no lo esta
        return (self.dx -self.w <= p[0] <= self.dx + self.w and self.dy - self.h <= p[1] <= self.dy + self.h)            #X entre el borde de izquierda a derecha y Y entre el borde de arriba a abajo

    def min_dist2(self, x, y):
        # Punto del rectángulo más cercano a (x, y)
        nx = max(self.dx - self.w, min(x, self.dx + self.w))
        ny = max(self.dy - self.h, min(y, self.dy + self.h))
        
        # Distancia al cuadrado hasta ese punto más cercano
        return (x - nx)**2 + (y - ny)**2
    
    def intersects_circle(self, x, y, r):
            # 1. Se encuentra el punto (nx, ny) del rectángulo más cercano a (x, y)
            nx = max(self.dx - self.w, min(x, self.dx + self.w))
            ny = max(self.dy - self.h, min(y, self.dy + self.h))
    
            # 2. Calcular la distancia al cuadrado entre (x, y) y (nx, ny)
            dx = x - nx
            dy = y - ny
            dist2 = dx**2 + dy**2
    
            # 3. Comparar con r**2
            return dist2 <= r**2
                


class Quadtree:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary    # el Rectangulo que cubre este nodo
        self.capacity = capacity    # máximo de puntos antes de partirse
        self.points = []            # puntos guardados en este nodo
        self.children = None        # None = no se ha partido todavía (nodo hoja)

    def subdivide(self):
        dx = self.boundary.dx
        dy = self.boundary.dy
        w = self.boundary.w 
        h = self.boundary.h 

        #nuevos anchos y altos
        nw = w/2
        nh = h/2

        #creo los 4 rectangulos hijos
        rect_no = Rect(dx - nw, dy + nh, nw, nh)  # NorOeste
        rect_ne = Rect(dx + nw, dy + nh, nw, nh)  # NorEste
        rect_so = Rect(dx - nw, dy - nh, nw, nh)  # SurOeste
        rect_se = Rect(dx + nw, dy - nh, nw, nh)  # SurEste

        #Ahora se guardan en la lista de hijos
        self.children = [Quadtree(rect_no, self.capacity),
                         Quadtree(rect_ne, self.capacity),
                         Quadtree(rect_so, self.capacity),
                         Quadtree(rect_se, self.capacity)]

        #Reparto los puntos que ya tenía este nodo entre los nuevos hijos
        for p in self.points:
            for child in self.children:
                if child.insert(p):  # Intenta insertar; si devuelve True, se guardó
                    break            # Pasa al siguiente punto inmediatamente

        # Se Vacia los puntos del nodo actual (ahora viven en sus hijos)
        self.points = []


    def insert(self, p):
        # Paso 1: Si el punto no pertenece a este rectángulo, ignorar
        if not self.boundary.contains(p):
            return False

        # Paso 2: Si hay espacio y aún no se ha dividido, guardarlo aquí
        if len(self.points) < self.capacity and self.children is None:
            self.points.append(p)
            return True

        # Paso 3: Si superó la capacidad y aún no está dividido, subdividir
        if self.children is None:
            self.subdivide()

        # Paso 4: Si ya está dividido, delegar la inserción a los hijos
        for child in self.children:
            if child.insert(p):
                return True

        return False

    def count(self):
        if self.children is None: #Si el nodo no tiene hijos, devuelve sus propios puntos
            return len(self.points)

        total = 0
        for child in self.children: #si tiene hijos, recorre cada hijo y suma sus puntos
            total += child.count()
        return total


    def query_radius(self, x, y, r, found=None):
        if found is None:
            found = []

        # 1. Si el círculo no toca este rectángulo, ignorar todo el nodo y sus hijos
        if not self.boundary.intersects_circle(x, y, r):
            return found

        # 2. Si lo toca, revisar los puntos directos de este nodo
        r2 = r**2
        for p in self.points:   
            dist2 = (p[0] - x)**2 + (p[1] - y)**2
            if dist2 <= r2:
                found.append(p)

        # 3. Si tiene hijos, bajar recursivamente pasando la misma lista 'found'
        if self.children is not None:
            for child in self.children:
                child.query_radius(x, y, r, found)

        return found

    def nearest(self, x, y, best=None):
        # 1. Si la distancia mínima al rectángulo actual es mayor o igual a la mejor distancia ya encontrada, descartamos este nodo completo
        if best is not None and self.boundary.min_dist2(x, y) >= best[1]:
            return best

        # 2. Revisamos los puntos propios de este nodo
        for p in self.points:
            dist2 = (p[0] - x)**2 + (p[1] - y)**2
            if best is None or dist2 < best[1]:
                best = [p, dist2]

        # 3. Bajo a los hijos, primero los más cercanos
        if self.children is not None:
            lista = []
            for i in range(4):
                hijo = self.children[i]
                d = hijo.boundary.min_dist2(x, y)     # qué tan cerca está su rectángulo
                lista.append((d, i, hijo))
            lista.sort()                              # ordena de menor a mayor distancia
            for d, i, hijo in lista:
                best = hijo.nearest(x, y, best)

        return best

    def nearest_point(self, x, y):
        best = self.nearest(x, y)
        return best[0], math.sqrt(best[1])

    def k_nearest(self, x, y, k, best=None):
        # best = lista ordenada de (dist2, punto), con a lo sumo k elementos
        if best is None:
            best = []

        # 1. Si ya tengo k candidatos y este nodo no puede mejorar al peor, lo descarto
        if len(best) == k and self.boundary.min_dist2(x, y) >= best[-1][0]:
            return best

        # 2. Reviso los puntos de este nodo
        for p in self.points:
            dist2 = (p[0] - x)**2 + (p[1] - y)**2
            if len(best) < k or dist2 < best[-1][0]:
                best.append((dist2, p))
                best.sort()            # ordena por distancia
                if len(best) > k:
                    best.pop()         # saco al peor

        # 3. Bajo a los hijos, primero los más cercanos
        if self.children is not None:
            lista = []
            for i in range(4):
                hijo = self.children[i]
                d = hijo.boundary.min_dist2(x, y)
                lista.append((d, i, hijo))
            lista.sort()
            for d, i, hijo in lista:
                hijo.k_nearest(x, y, k, best)


        return best
    def k_nearest_points(self, x, y, k):
        # Devuelve [(punto, distancia en metros), ...] ordenado de más cerca a más lejos
        return [(p, math.sqrt(d2)) for d2, p in self.k_nearest(x, y, k)]

