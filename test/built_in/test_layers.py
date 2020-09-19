from helpers import compute_volume

import pygmsh


def test(mesh_size=0.05):
    geom = pygmsh.built_in.Geometry()

    # Draw a cross with a circular hole
    circ = geom.add_circle(
        [0.0, 0.0, 0.0], 0.1, mesh_size=mesh_size, make_surface=False
    )
    poly = geom.add_polygon(
        [
            [+0.0, +0.5, 0.0],
            [-0.1, +0.1, 0.0],
            [-0.5, +0.0, 0.0],
            [-0.1, -0.1, 0.0],
            [+0.0, -0.5, 0.0],
            [+0.1, -0.1, 0.0],
            [+0.5, +0.0, 0.0],
            [+0.1, +0.1, 0.0],
        ],
        mesh_size=mesh_size,
        holes=[circ],
    )

    axis = [0, 0, 1.0]

    geom.extrude(poly.surface, translation_axis=axis, num_layers=1)

    ref = 0.16951514066385628
    mesh = pygmsh.generate_mesh(geom)
    assert abs(compute_volume(mesh) - ref) < 1.0e-2 * ref
    return mesh


if __name__ == "__main__":
    import meshio

    meshio.write("layers.vtu", test())
