import Rhino.Geometry as rg
import ghpythonlib.components as gh
import random  # Importamos la librería nativa de Python para generar aleatoriedad

# 1. El Terreno Base (Dominio)
plano = rg.Plane.WorldXY
rectangulo = gh.Rectangle(plano, width, depth, 0)[0] 

# 2. Poblar con puntos 
puntos = gh.Populate2D(rectangulo, n_cells, seed)

# 3. Generar las celdas de Voronoi
celdas = gh.Voronoi(puntos, boundary=rectangulo)

# Listas vacías (Como pedir camiones vacíos para ir guardando el material de obra)
superficies_base = []
volumenes = []

# Configuramos la "semilla" del generador aleatorio para que los cambios no salten sin control
random.seed(seed)

# 4 al 7. Bucle de construcción (Parcela por parcela)
for celda in celdas:
    
    # 4. Retranqueo (Offset). 
    curvas_offset = gh.OffsetCurve(celda, -offset_dist, plano, 1)
    
    # Verificamos que el offset no haya fallado (que no esté vacío)
    if curvas_offset:
        
        # PREVENCIÓN DE ERRORES: Comprobamos si el resultado es una lista o un elemento suelto
        if isinstance(curvas_offset, list):
            # Si es una lista (una caja de curvas), sacamos la primera
            curva_interior = curvas_offset[0]
        else:
            # Si NO es una lista, es la curva suelta directamente
            curva_interior = curvas_offset
            
        # 5. Losa de cimentación (Superficie)
        # Nota importante: BoundarySurfaces SIEMPRE exige que le entregues los planos 
        # dentro de una lista, por eso aquí sí envolvemos la curva en corchetes [ ]
        superficie = gh.BoundarySurfaces([curva_interior])
        superficies_base.append(superficie)
        
        # 6. Altura Aleatoria
        altura_azar = random.uniform(h_min, h_max)
        
        # 7. Extrusión
        centro = gh.Area(curva_interior)[1]
        linea_eje = gh.LineSDL(centro, rg.Vector3d.ZAxis, altura_azar)
        
        extrusion = gh.Extrude(superficie, linea_eje)
        volumenes.append(extrusion)

# Salidas (Outputs)
a = volumenes
b = superficies_base