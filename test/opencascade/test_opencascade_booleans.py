"""Test module for boolean operations."""
import meshio
import numpy as np
import pytest
from helpers import compute_volume

import pygmsh


def square_loop(geo_object):
    """Construct square using built in geometry."""
    points = [
        geo_object.add_point([-0.5, -0.5, 0], 0.05),
        geo_object.add_point([-0.5, 0.5, 0], 0.05),
        geo_object.add_point([0.5, 0.5, 0], 0.05),
        geo_object.add_point([0.5, -0.5, 0], 0.05),
    ]
    lines = [
        geo_object.add_line(points[0], points[1]),
        geo_object.add_line(points[1], points[2]),
        geo_object.add_line(points[2], points[3]),
        geo_object.add_line(points[3], points[0]),
    ]
    return geo_object.add_curve_loop(lines)


def circle_loop(geo_object):
    """construct circle using built_in geometry module."""
    points = [
        geo_object.add_point([+0.0, +0.0, 0.0], 0.05),
        geo_object.add_point([+0.0, +0.1, 0.0], 0.05),
        geo_object.add_point([-0.1, +0.0, 0.0], 0.05),
        geo_object.add_point([+0.0, -0.1, 0.0], 0.05),
        geo_object.add_point([+0.1, +0.0, 0.0], 0.05),
    ]
    quarter_circles = [
        geo_object.add_circle_arc(points[1], points[0], points[2]),
        geo_object.add_circle_arc(points[2], points[0], points[3]),
        geo_object.add_circle_arc(points[3], points[0], points[4]),
        geo_object.add_circle_arc(points[4], points[0], points[1]),
    ]
    return geo_object.add_curve_loop(quarter_circles)


def _square_hole_classical(geo_object):
    """Construct surface using builtin and boolean methods."""
    # construct surface with hole using standard built in
    geo_object.characteristic_length_min = 0.05
    geo_object.characteristic_length_max = 0.05
    square = square_loop(geo_object)
    circle = circle_loop(geo_object)
    geo_object.add_plane_surface(square, [circle])


def _square_hole_cad(geo_object):
    # construct surface using boolean
    geo_object.characteristic_length_min = 0.05
    geo_object.characteristic_length_max = 0.05
    square2 = square_loop(geo_object)
    curve_loop2 = circle_loop(geo_object)
    surf1 = geo_object.add_plane_surface(square2)
    surf2 = geo_object.add_plane_surface(curve_loop2)
    geo_object.boolean_difference(surf1, surf2)


@pytest.mark.parametrize("fun", [_square_hole_classical, _square_hole_cad])
def test_square_circle_hole(fun):
    """Test planar surface with holes.

    Construct it with boolean operations and verify that it is the same.
    """
    with pygmsh.opencascade.Geometry() as geo_object:
        fun(geo_object)
        mesh = pygmsh.generate_mesh(geo_object)
    surf = 1 - 0.1 ** 2 * np.pi
    assert np.abs((compute_volume(mesh) - surf) / surf) < 1e-3


@pytest.mark.skip()
def test_square_circle_slice():
    """Test planar suface square with circular hole.

    Also test for surface area of fragments.
    """
    with pygmsh.opencascade.Geometry() as geo_object:
        square = square_loop(geo_object)
        curve_loop = circle_loop(geo_object)
        surf1 = geo_object.add_plane_surface(square)
        surf2 = geo_object.add_plane_surface(curve_loop)
        geo_object.boolean_fragments(surf1, surf2)
        # Gmsh 4 default format MSH4 doesn't have geometrical entities.
        mesh = pygmsh.generate_mesh(geo_object)

    ref = 1.0
    val = compute_volume(mesh)
    assert np.abs(val - ref) < 1e-3 * ref

    outer_mask = np.where(mesh.cell_data["gmsh:geometrical"][2] == 13)[0]
    outer_cells = {}
    outer_cells["triangle"] = mesh.cells_dict["triangle"][outer_mask]

    inner_mask = np.where(mesh.cell_data["gmsh:geometrical"][2] == 12)[0]
    inner_cells = {}
    inner_cells["triangle"] = mesh.cells_dict["triangle"][inner_mask]

    ref = 1 - 0.1 ** 2 * np.pi
    value = compute_volume(meshio.Mesh(mesh.points, outer_cells))
    assert np.abs(value - ref) < 1e-2 * ref


@pytest.mark.skip("cell data no working yet")
def test_fragments_diff_union():
    """Test planar surface with holes.

    Construct it with boolean operations and verify that it is the same.
    """
    # construct surface using boolean
    with pygmsh.opencascade.Geometry() as geo_object:
        geo_object.characteristic_length_min = 0.04
        geo_object.characteristic_length_max = 0.04
        square = square_loop(geo_object)
        surf1 = geo_object.add_plane_surface(square)
        curve_loop = circle_loop(geo_object)
        surf2 = geo_object.add_plane_surface(curve_loop)

        geo_object.add_physical([surf1], label="1")
        geo_object.add_physical([surf2], label="2")
        geo_object.boolean_difference(surf1, surf2, delete_other=False)
        mesh = pygmsh.generate_mesh(geo_object)

    ref = 1.0
    assert np.abs(compute_volume(mesh) - ref) < 1e-3 * ref

    surf = 1 - 0.1 ** 2 * np.pi
    outer_mask = np.where(mesh.cell_data_dict["gmsh:geometrical"]["triangle"] == 1)[0]
    outer_cells = {}
    outer_cells["triangle"] = mesh.cells_dict["triangle"][outer_mask]

    inner_mask = np.where(mesh.cell_data_dict["gmsh:geometrical"]["triangle"] == 2)[0]
    inner_cells = {}
    inner_cells["triangle"] = mesh.cells_dict["triangle"][inner_mask]

    value = compute_volume(meshio.Mesh(mesh.points, outer_cells))
    assert np.abs(value - surf) < 1e-2 * surf


@pytest.mark.skip("cell data no working yet")
def test_diff_physical_assignment():
    """construct surface using boolean.

    Ensure that after a difference operation the initial volume physical label
    is kept for the operated geometry.
    """
    with pygmsh.opencascade.Geometry() as geo_object2:
        geo_object2.characteristic_length_min = 0.05
        geo_object2.characteristic_length_max = 0.05
        square2 = square_loop(geo_object2)
        curve_loop2 = circle_loop(geo_object2)
        surf1 = geo_object2.add_plane_surface(square2)
        surf2 = geo_object2.add_plane_surface(curve_loop2)
        geo_object2.add_physical(surf1, label="1")
        geo_object2.boolean_difference(surf1, surf2)
        mesh = pygmsh.generate_mesh(geo_object2)
    assert np.allclose(
        mesh.cell_data_dict["gmsh:geometrical"]["triangle"],
        np.ones(mesh.cells_dict["triangle"].shape[0]),
    )
    surf = 1 - 0.1 ** 2 * np.pi
    assert np.abs((compute_volume(mesh) - surf) / surf) < 1e-3


def test_polygon_diff():
    with pygmsh.opencascade.Geometry() as geom:
        poly = geom.add_polygon([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
        disk = geom.add_disk([0, 0, 0], 0.5)
        geom.boolean_difference(poly.surface, disk)


if __name__ == "__main__":
    test_square_circle_slice()