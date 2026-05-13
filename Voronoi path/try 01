import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import random


def create_rectangle_domain(width, depth):
    """Crea la curva rectangular del dominio en el plano XY."""
    corners = [
        rg.Point3d(0.0, 0.0, 0.0),
        rg.Point3d(width, 0.0, 0.0),
        rg.Point3d(width, depth, 0.0),
        rg.Point3d(0.0, depth, 0.0),
        rg.Point3d(0.0, 0.0, 0.0),
    ]
    return rg.PolylineCurve(corners)


def random_points_in_rectangle(width, depth, count, seed=None):
    """Genera puntos aleatorios dentro del rectángulo base."""
    if seed is not None:
        random.seed(seed)
    return [rg.Point3d(random.random() * width, random.random() * depth, 0.0) for _ in range(count)]


def get_voronoi_cells(points, boundary_curve):
    """Calcula el diagrama de Voronoi recortado al dominio rectangular."""
    if not points:
        return []

    voronoi = rs.Voronoi(points, boundary_curve)
    if not voronoi:
        return []

    # rhinoscriptsyntax.Voronoi puede devolver listas anidadas.
    if isinstance(voronoi, (list, tuple)) and voronoi and isinstance(voronoi[0], (list, tuple)):
        flattened = []
        for item in voronoi:
            if isinstance(item, (list, tuple)):
                flattened.extend(item)
            else:
                flattened.append(item)
        voronoi = flattened

    valid_cells = []
    for cell in voronoi:
        if cell is None:
            continue
        if isinstance(cell, rg.Curve):
            if cell.IsClosed:
                valid_cells.append(cell)
            else:
                success, polyline = cell.TryGetPolyline()
                if success:
                    if not polyline.IsClosed:
                        polyline.Add(polyline[0])
                    valid_cells.append(rg.PolylineCurve(polyline))
                else:
                    valid_cells.append(cell)
        else:
            valid_cells.append(cell)

    return valid_cells


def centroid_from_points(points):
    """Calcula el centroide de un polígono planar definido por puntos cerrados."""
    n = len(points)
    if n < 3:
        return None

    area = 0.0
    cx = 0.0
    cy = 0.0

    for i in range(n):
        p0 = points[i]
        p1 = points[(i + 1) % n]
        cross = p0.X * p1.Y - p1.X * p0.Y
        area += cross
        cx += (p0.X + p1.X) * cross
        cy += (p0.Y + p1.Y) * cross

    if abs(area) < 1e-9:
        return None

    area *= 0.5
    return rg.Point3d(cx / (6.0 * area), cy / (6.0 * area), 0.0)


def centroid_from_curve(curve):
    """Obtiene el centroide de una curva cerrada mediante su polilínea equivalente."""
    if curve is None or not curve.IsClosed:
        return None

    success, polyline = curve.TryGetPolyline()
    if success:
        if not polyline.IsClosed:
            polyline.Add(polyline[0])
        return centroid_from_points(list(polyline))

    area_props = rg.AreaMassProperties.Compute(curve)
    if area_props:
        return rg.Point3d(area_props.Centroid.X, area_props.Centroid.Y, 0.0)
    return None


def distance_point_to_curve(point, curve):
    """Calcula la distancia mínima entre un punto y una curva."""
    if point is None or curve is None:
        return float('inf')

    t = curve.ClosestPoint(point)
    closest = curve.PointAt(t)
    return point.DistanceTo(closest)


def remap(value, domain_min, domain_max, target_min, target_max):
    """Remapea un valor de un dominio a otro."""
    if domain_max == domain_min:
        return target_min
    ratio = (value - domain_min) / (domain_max - domain_min)
    return target_min + ratio * (target_max - target_min)


def scale_curve_around_point(curve, center, factor):
    """Escala una curva respecto a un punto central."""
    if curve is None or center is None:
        return None
    duplicate = curve.DuplicateCurve()
    xform = rg.Transform.Scale(rg.Plane(center, rg.Vector3d.ZAxis), factor)
    duplicate.Transform(xform)
    return duplicate


def offset_curve(curve, distance):
    """Offsetea una curva plana en el plano XY."""
    if curve is None:
        return None

    offsets = curve.Offset(rg.Plane.WorldXY, distance, 0.001, rg.CurveOffsetCornerStyle.Sharp)
    if offsets:
        return offsets[0]
    return None


def extrude_curve_vertical(curve, height):
    """Extruye una curva cerrada verticalmente según la altura dada."""
    if curve is None or height is None:
        return None
    return rg.Extrusion.Create(curve, height, True)


def create_voronoi_attractor(
    width,
    depth,
    point_count,
    attractor_curve,
    nearest_count=5,
    offset_dist=0.1,
    height_scale=10.0,
    seed=None,
    scale_min=0.7,
    scale_max=1.2,
):
    """Genera Voronoi, centroides, escala, offset y extrusiones según una curva attractor."""
    if width <= 0 or depth <= 0 or point_count < 1 or attractor_curve is None:
        return {
            'domain_curve': None,
            'points': [],
            'voronoi_cells': [],
            'centroids': [],
            'distances': [],
            'closest_indices': [],
            'closest_cells': [],
            'scaled_cells': [],
            'offset_cells': [],
            'extrusions': [],
        }

    domain_curve = create_rectangle_domain(width, depth)
    points = random_points_in_rectangle(width, depth, point_count, seed)
    voronoi_cells = get_voronoi_cells(points, domain_curve)

    cell_data = []
    for cell in voronoi_cells:
        centroid = centroid_from_curve(cell)
        if centroid is None:
            continue
        distance = distance_point_to_curve(centroid, attractor_curve)
        cell_data.append({
            'curve': cell,
            'centroid': centroid,
            'distance': distance,
        })

    if not cell_data:
        return {
            'domain_curve': domain_curve,
            'points': points,
            'voronoi_cells': [],
            'centroids': [],
            'distances': [],
            'closest_indices': [],
            'closest_cells': [],
            'scaled_cells': [],
            'offset_cells': [],
            'extrusions': [],
        }

    cell_data.sort(key=lambda item: item['distance'])
    distances = [item['distance'] for item in cell_data]
    min_dist = min(distances)
    max_dist = max(distances)

    nearest_count = max(0, min(nearest_count, len(cell_data)))
    closest_indices = list(range(nearest_count))
    closest_cells = [cell_data[i]['curve'] for i in closest_indices]

    scaled_cells = []
    offset_cells = []
    extrusions = []
    cull_pattern = [i < nearest_count for i in range(len(cell_data))]

    for item in cell_data:
        item['scale'] = remap(item['distance'], min_dist, max_dist, scale_max, scale_min)
        item['height'] = remap(item['distance'], min_dist, max_dist, height_scale, 0.0)

        scaled_curve = scale_curve_around_point(item['curve'], item['centroid'], item['scale'])
        scaled_cells.append(scaled_curve if scaled_curve else item['curve'])

        offset_curve_obj = offset_curve(item['curve'], -offset_dist)
        if offset_curve_obj:
            offset_cells.append(offset_curve_obj)
            extrusion_obj = extrude_curve_vertical(offset_curve_obj, item['height'])
            if extrusion_obj:
                extrusions.append(extrusion_obj)

    return {
        'domain_curve': domain_curve,
        'points': points,
        'voronoi_cells': [item['curve'] for item in cell_data],
        'centroids': [item['centroid'] for item in cell_data],
        'distances': distances,
        'closest_indices': closest_indices,
        'closest_cells': closest_cells,
        'cull_pattern': cull_pattern,
        'scaled_cells': scaled_cells,
        'offset_cells': offset_cells,
        'extrusions': extrusions,
    }


if __name__ == '__main__':
    # Ejemplo de prueba local (no es ejecutable fuera de Rhino/GhPython).
    print('Este módulo está pensado para usarse dentro de GhPython.')
