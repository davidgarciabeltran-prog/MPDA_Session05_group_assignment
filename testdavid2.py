import Rhino.Geometry as rg
import rhinoscriptsyntax as rs

# ================================
# Inputs expected from Grasshopper
# ================================
# width: float
# depth: float
# n_points: int
# curve: geometry
# n_closest: int
# domain_start: float
# domain_end: float
# offset_distance: float
# height: float

# Fallback defaults for script testing
width = globals().get('width', 10.0)
depth = globals().get('depth', 10.0)
n_points = globals().get('n_points', 20)
curve = globals().get('curve', None)
n_closest = globals().get('n_closest', 5)
domain_start = globals().get('domain_start', 0.2)
domain_end = globals().get('domain_end', 1.0)
offset_distance = globals().get('offset_distance', -0.1)
height = globals().get('height', 5.0)

# Helper functions

def remap(value, source_domain, target_domain):
    src_min, src_max = source_domain
    dst_min, dst_max = target_domain
    if src_max == src_min:
        return dst_min
    t = (value - src_min) / float(src_max - src_min)
    return dst_min + t * (dst_max - dst_min)


def get_centroid(curve_id):
    area_data = rs.CurveAreaCentroid(curve_id)
    if area_data:
        return area_data[0]
    return None


def safe_list_item(source_list, index):
    return source_list[index] if 0 <= index < len(source_list) else None

# 1. Create rectangular surface domain
rect_curve = rs.AddRectangle(rs.WorldXYPlane(), width, depth)
domain_surface = None
if rect_curve:
    domain_surface = rs.AddPlanarSrf(rect_curve)

# 2. Populate points in the rectangle
points = []
if rect_curve:
    points = rs.PopulateGeometry(rect_curve, n_points)

# 3. Generate 2D Voronoi cells
voronoi_cells = []
if points:
    voronoi_cells = rs.Voronoi(points, None, rect_curve)
    if not voronoi_cells:
        voronoi_cells = []

# 4. Calculate centroids for each Voronoi cell
centroids = []
for cell in voronoi_cells:
    centroid = get_centroid(cell)
    if centroid:
        centroids.append(centroid)

# 5. Verify curve input
if curve is None:
    curve = None

# 6. Find N closest centroids to the curve
closest_data = []
if curve and centroids:
    for idx, pt in enumerate(centroids):
        distance = rs.Distance(pt, curve)
        if distance is not None:
            closest_data.append((distance, idx))
    closest_data.sort(key=lambda item: item[0])

selected_indices = [item[1] for item in closest_data[:max(0, min(n_closest, len(closest_data)))]]

# 7. Cull pattern for selected Voronoi cells
cull_pattern = [idx in selected_indices for idx in range(len(voronoi_cells))]
selected_cells = [voronoi_cells[idx] for idx in selected_indices]
selected_centroids = [centroids[idx] for idx in selected_indices]
selected_distances = [closest_data[i][0] for i in range(len(selected_indices))] if closest_data else []

# 8. Remap distance values to the target domain
remap_values = []
if selected_distances:
    source_min = min(selected_distances)
    source_max = max(selected_distances)
    source_domain = (source_min, source_max)
    target_domain = (domain_start, domain_end)
    remap_values = [remap(d, source_domain, target_domain) for d in selected_distances]

# 9. Scale selected Voronoi geometry about each centroid
scaled_cells = []
for cell, centroid, scale_value in zip(selected_cells, selected_centroids, remap_values):
    scaled = rs.CopyObject(cell)
    if scaled:
        scaled = rs.ScaleObject(scaled, centroid, (scale_value, scale_value, scale_value))
        if scaled:
            scaled_cells.append(scaled)

# 10. Offset each scaled Voronoi cell
offset_curves = []
for scaled_cell in scaled_cells:
    if scaled_cell:
        offset_result = rs.OffsetCurve(scaled_cell, rs.CurveAreaCentroid(scaled_cell)[0], offset_distance)
        if offset_result:
            if isinstance(offset_result, list):
                offset_result = offset_result[0]
            offset_curves.append(offset_result)

# 11. Create planar surfaces from offset curves
offset_surfaces = []
for offset_curve in offset_curves:
    if offset_curve:
        surface = rs.AddPlanarSrf(offset_curve)
        if surface:
            if isinstance(surface, list):
                offset_surfaces.extend(surface)
            else:
                offset_surfaces.append(surface)

# 12. Create lines from centroids using distance * height
extrude_lines = []
for centroid, distance in zip(selected_centroids, selected_distances):
    line_height = distance * height
    start = centroid
    end = rg.Point3d(centroid.X, centroid.Y, centroid.Z + line_height)
    line_id = rs.AddLine(start, end)
    if line_id:
        extrude_lines.append(line_id)

# 13. Extrude surfaces with the lines
extrusions = []
for surface_id, line_id in zip(offset_surfaces, extrude_lines):
    extrusion = rs.ExtrudeSurface(surface_id, line_id)
    if extrusion:
        extrusions.append(extrusion)

# Outputs
voronoi_cells = voronoi_cells
centroids = centroids
closest_centroids = selected_centroids
closest_cells = selected_cells
scaled_cells = scaled_cells
offset_surfaces = offset_surfaces
extrusions = extrusions
remap_values = remap_values
cull_pattern = cull_pattern

# Optional Grasshopper outputs
a = voronoi_cells
b = centroids
c = closest_cells
d = scaled_cells
e = offset_surfaces
f = extrusions
g = remap_values
h = cull_pattern