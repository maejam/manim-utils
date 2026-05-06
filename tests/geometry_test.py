import numpy as np
from manim import ORIGIN, Circle, Cube, Line, Square

from manim_utils.geometry import get_bounds


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
def create_test_objects():
    """Helper to create a consistent set of test objects."""
    # A square from (-1, -1) to (1, 1)
    square = Square(side_length=2)
    square.move_to(ORIGIN)

    # A circle with radius 0.5 at (2, 0, 0)
    circle = Circle(radius=0.5)
    circle.move_to(np.array([2, 0, 0]))

    # A line from (0, 2, 0) to (0, 3, 0)
    line = Line(np.array([0, 2, 0]), np.array([0, 3, 0]))

    return square, circle, line


# ----------------------------------------------------------------------
# get_bounds
# ----------------------------------------------------------------------
def test_get_bounds_default_no_stroke():
    """Test default behavior (include_stroke=None) returns path bounds."""
    square, circle, line = create_test_objects()

    # Default: include_stroke=None, as_len=False
    # Square: [-1, -1, 0] to [1, 1, 0]
    # Circle: [1.5, -0.5, 0] to [2.5, 0.5, 0]
    # Line: [0, 2, 0] to [0, 3, 0]
    # Global Min: [-1, -1, 0]
    # Global Max: [2.5, 3, 0]

    v_min, center, v_max = get_bounds(square, circle, line)

    expected_min = np.array([-1.0, -1.0, 0.0])
    expected_max = np.array([2.5, 3, 0.0])
    expected_center = (expected_min + expected_max) / 2

    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)
    np.testing.assert_array_almost_equal(center, expected_center)


def test_get_bounds_include_stroke_true():
    """Test include_stroke=True expands bounds by half the max stroke width."""
    square, circle, line = create_test_objects()

    # Set a uniform stroke width of 20 (0.2 Munits)
    # Half width = 0.1
    stroke_width = 20
    square.set_stroke(width=stroke_width)
    circle.set_stroke(width=stroke_width)
    line.set_stroke(width=stroke_width)

    # With include_stroke=True, bounds should expand by 0.1 on all sides
    v_min, center, v_max = get_bounds(square, circle, line, include_stroke=True)

    # Original min was [-1, -1, 0], now should be [-1.1, -1.1, -0.1] (z is 0)
    # Actually z is 0 for all, so z_min = 0 - 0.1 = -0.1
    expected_min = np.array([-1.1, -1.1, 0.0])
    expected_max = np.array([2.6, 3.1, 0.0])

    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)


def test_get_bounds_include_stroke_false():
    """Test include_stroke=False shrinks bounds by half the stroke width."""
    square, circle, line = create_test_objects()

    # Set stroke width
    stroke_width = 20  # 0.2 units
    square.set_stroke(width=stroke_width)
    circle.set_stroke(width=stroke_width)
    line.set_stroke(width=stroke_width)

    # With include_stroke=False, bounds should shrink by 0.1
    v_min, center, v_max = get_bounds(square, circle, line, include_stroke=False)

    # Original min was [-1, -1, 0], now should be [-0.9, -0.9, 0.0]
    expected_min = np.array([-0.9, -0.9, 0.0])
    expected_max = np.array([2.4, 2.9, 0.0])

    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)


def test_get_bounds_mixed_stroke_widths():
    """Test that include_stroke=True uses the MAX stroke width of the group."""
    square, circle, line = create_test_objects()

    # Square has thick stroke (0.4), others have thin (0.0)
    square.set_stroke(width=40)  # 0.4 units -> expansion 0.2
    circle.set_stroke(width=0)
    line.set_stroke(width=0)

    v_min, _, v_max = get_bounds(square, circle, line, include_stroke=True)

    # initial
    # Square: [-1, -1, 0] to [1, 1, 0]
    # Circle: [1.5, -0.5, 0] to [2.5, 0.5, 0]
    # Line: [0, 2, 0] to [0, 3, 0]
    # Global Min: [-1, -1, 0]
    # Global Max: [2.5, 3, 0]

    # adjusted
    # Global Min: [-1.2, -1.2, 0]
    # Global Max: [2.5, 3, 0]
    expected_min = np.array([-1.2, -1.2, -0.0])
    expected_max = np.array([2.5, 3, 0])

    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)


def test_get_bounds_as_len_true():
    """Test as_len=True returns (width, height, depth, center)."""
    square, circle, line = create_test_objects()

    w, h, d, center = get_bounds(square, circle, line, as_len=True)

    # Width: 2.5 - (-1) = 3.5
    # Height: 3 - (-1) = 4
    # Depth: 0
    assert np.isclose(w, 3.5)
    assert np.isclose(h, 4.0)
    assert np.isclose(d, 0.0)

    # Center check
    expected_center = np.array([0.75, 1, 0.0])
    np.testing.assert_array_almost_equal(center, expected_center)


def test_get_bounds_empty_objects():
    """Test behavior with no objects."""
    zero = np.array([0.0, 0.0, 0.0])

    # Test default return
    v_min, center, v_max = get_bounds()
    np.testing.assert_array_equal(v_min, zero)
    np.testing.assert_array_equal(center, zero)
    np.testing.assert_array_equal(v_max, zero)

    # Test as_len return
    w, h, d, center = get_bounds(as_len=True)
    assert w == 0.0
    assert h == 0.0
    assert d == 0.0
    np.testing.assert_array_equal(center, zero)


def test_get_bounds_3d_cube_with_stroke():
    """Test that a 3D Cube expands in all dimensions.

    Including Z when include_stroke=True.
    """
    # Create a cube from (-1, -1, -1) to (1, 1, 1)
    cube = Cube(side_length=2).set_stroke(width=20)

    # Default (Path only)
    v_min, _, v_max = get_bounds(cube, include_stroke=None)
    np.testing.assert_array_almost_equal(v_min, np.array([-1.0, -1.0, -1.0]))
    np.testing.assert_array_almost_equal(v_max, np.array([1.0, 1.0, 1.0]))

    # Include Stroke (Should expand in X, Y, AND Z)
    v_min, _, v_max = get_bounds(cube, include_stroke=True)
    # Expansion is 0.1 on all sides
    expected_min = np.array([-1.1, -1.1, -1.1])
    expected_max = np.array([1.1, 1.1, 1.1])
    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)

    # Exclude Stroke (Should shrink in X, Y, AND Z)
    v_min, _, v_max = get_bounds(cube, include_stroke=False)
    expected_min = np.array([-0.9, -0.9, -0.9])
    expected_max = np.array([0.9, 0.9, 0.9])
    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)


def test_get_bounds_3d_line_in_xz_plane():
    """Test a line in the XZ plane (Y=0) expands in Y due to stroke.

    But Z only if it has Z extent.
    """
    # Line from (0, 0, 0) to (2, 0, 2)
    line = Line(np.array([0, 0, 0]), np.array([2, 0, 2]))
    line.set_stroke(width=20)  # 0.2 units

    # Default
    v_min, _, v_max = get_bounds(line, include_stroke=None)
    np.testing.assert_array_almost_equal(v_min, np.array([0.0, 0.0, 0.0]))
    np.testing.assert_array_almost_equal(v_max, np.array([2.0, 0.0, 2.0]))

    # Include Stroke
    # X: Has extent -> Expand
    # Y: No extent -> Expand (due to include_stroke=True) -> Creates tube thickness
    # Z: Has extent -> Expand
    v_min, _, v_max = get_bounds(line, include_stroke=True)
    expected_min = np.array([-0.1, -0.1, -0.1])
    expected_max = np.array([2.1, 0.1, 2.1])
    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)

    # Exclude Stroke
    # X: Has extent -> Shrink
    # Y: No extent -> Skip (no phantom shrinking)
    # Z: Has extent -> Shrink
    v_min, _, v_max = get_bounds(line, include_stroke=False)
    expected_min = np.array([0.1, 0.0, 0.1])
    expected_max = np.array([1.9, 0.0, 1.9])
    np.testing.assert_array_almost_equal(v_min, expected_min)
    np.testing.assert_array_almost_equal(v_max, expected_max)
