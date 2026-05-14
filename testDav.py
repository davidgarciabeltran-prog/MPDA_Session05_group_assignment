import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import ghpythonlib.components as gh  # ¡El catálogo completo de nodos de Grasshopper!

# ================================
# Inputs expected from Grasshopper
# ================================
width = globals().get('width', 10.0)
depth = globals().get('depth', 10.0)
n_points = globals().get('n_points', 20)
curve = globals().get('curve', None)
n_closest = globals().get('n_closest', 5)
domain_start = globals().get('domain_start', 0.2)
domain_end = globals().get('domain_end', 1.0)
offset_distance = globals().get('offset_distance', -0.1)
height = globals().get('height', 5.0)

# Helper function
def remap(value, source_domain, target_domain):
    src_min, src_max = source_domain
    dst_min, dst_max = target_domain
    if src_max == src_min: return dst_min
    t = (value - src_min) / float(src_max - src_min)
    return dst_min + t * (dst_max - dst_min)

# 1. Create rectangular boundary (Usando geometría pura rg)
plane = rg.Plane.WorldXY
rect_curve = rg.Rectangle3d(plane, width, depth).ToNurbsCurve()

# 2. Populate points (Usando Grasshopper internamente)
# Sintaxis: gh.PopulateGeometry(Region, Count, Seed)
points = gh.PopulateGeometry(rect_curve, n_points, 1)

# 3. Generate 2D Voronoi cells
# Sintaxis: gh.Voronoi(Points, Radius, Boundary, Plane)
# Devuelve una tupla (Cells, Boundary). Tomamos el índice [0] para las celdas.
voronoi_result = gh.Voronoi(points, None, rect_curve, plane)
voronoi_cells = voronoi_result[0] if voronoi_result else []

# 4. Calculate centroids using Grasshopper Area component
centroids = []
for cell in voronoi_cells:
    # gh.Area devuelve (Area, Centroid). Pedimos la propiedad .centroid
    centroid = gh.Area(cell).centroid 
    centroids.append(centroid)

# 5. Verify curve input
closest_data = []
if curve and centroids:
    # 6. Find N closest centroids to the curve
    for idx, pt in enumerate(centroids):
        # rg.Curve.ClosestPoint nos da el punto más cercano en la curva
        success, t = curve.ClosestPoint(pt)
        if success:
            closest_pt_on_curve = curve.PointAt(t)
            distance = pt.DistanceTo(closest_pt_on_curve)
            closest_data.append((distance, idx))
            
    # Ordenar por distancia (el primer elemento de la tupla)
    closest_data.sort(key=lambda item: item[0])

selected_indices = [item[1] for item in closest_data[:max(0, min(n_closest, len(closest_data)))]]

# 7. Cull pattern for selected Voronoi cells
cull_pattern = [idx in selected_indices for idx in range(len(voronoi_cells))]
selected_cells = [voronoi_cells[idx] for idx in selected_indices]
selected_centroids = [centroids[idx] for idx in selected_indices]
selected_distances = [closest_data[i][0] for i in range(len(selected_indices))] if closest_data else []

# 8. Remap distance values
remap_values = []
if selected_distances:
    source_domain = (min(selected_distances), max(selected_distances))
    target_domain = (domain_start, domain_end)
    remap_values = [remap(d, source_domain, target_domain) for d in selected_distances]

# 9. Scale and Offset selected cells
offset_surfaces = []
extrude_lines = []
extrusions = []

for cell, centroid, scale_val, dist in zip(selected_cells, selected_centroids, remap_values, selected_distances):
    # Escalar usando Grasshopper Node
    scaled_result = gh.Scale(cell, centroid, scale_val)
    scaled_cell = scaled_result.geometry
    
    # Offset usando Grasshopper Node
    offset_cell = gh.OffsetCurve(scaled_cell, offset_distance, plane, 1)[0]
    
    if offset_cell:
        # Crear Superficie
        surface = gh.BoundarySurfaces(offset_cell)
        offset_surfaces.append(surface)
        
        # Crear Vector y Extruir
        line_height = dist * height
        vector_up = rg.Vector3d(0, 0, line_height)
        
        extrusion = gh.Extrude(surface, vector_up)
        extrusions.append(extrusion)

# Outputs
a = voronoi_cells
b = centroids
c = selected_cells
d = offset_surfaces
e = extrusions
f = remap_values
