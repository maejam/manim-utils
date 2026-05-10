import manim as m
import numpy as np

from manim_utils.geometry import get_bounds, is_inside_bounds


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
def create_test_objects():
    """Helper to create a consistent set of test objects."""
    # A square from (-1, -1) to (1, 1)
    square = m.Square(side_length=2)
    square.move_to(m.ORIGIN)

    # A circle with radius 0.5 at (2, 0, 0)
    circle = m.Circle(radius=0.5)
    circle.move_to(np.array([2, 0, 0]))

    # A line from (0, 2, 0) to (0, 3, 0)
    line = m.Line(np.array([0, 2, 0]), np.array([0, 3, 0]))

    # objects for is_inside_bounds
    small_square = m.Square(side_length=1).move_to(m.ORIGIN)

    return square, circle, line, small_square


# ----------------------------------------------------------------------
# get_bounds
# ----------------------------------------------------------------------
def test_get_bounds_default_no_stroke():
    """Test default behavior (include_stroke=None) returns path bounds."""
    square, circle, line, *_ = create_test_objects()

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
    square, circle, line, *_ = create_test_objects()

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
    square, circle, line, *_ = create_test_objects()

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
    square, circle, line, *_ = create_test_objects()

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
    square, circle, line, *_ = create_test_objects()

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
    cube = m.Cube(side_length=2).set_stroke(width=20)

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
    line = m.Line(np.array([0, 0, 0]), np.array([2, 0, 2]))
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


# ----------------------------------------------------------------------
# is_inside_bounds
# ----------------------------------------------------------------------
def test_small_inside_large_strict():
    """Small square should be inside large square with strict=True"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(small_square, square, strict=True) is True


def test_small_inside_large_non_strict():
    """Small square should overlap with large square with strict=False"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(small_square, square, strict=False) is True


def test_large_outside_small_strict():
    """Large square should NOT be inside small square with strict=True"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(square, small_square, strict=True) is False


def test_large_overlaps_small_non_strict():
    """Large square should overlap with small square with strict=False"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(square, small_square, strict=False) is True


def test_exactly_on_boundary_strict():
    """Object exactly on boundary should pass with strict=True"""
    square, circle, line, small_square = create_test_objects()
    # Create a container that exactly matches the small square
    container = m.Square(side_length=1).move_to(m.ORIGIN)
    assert is_inside_bounds(small_square, container, strict=True) is True


def test_slightly_outside_boundary_strict():
    """Object slightly outside boundary should fail with strict=True"""
    square, circle, line, small_square = create_test_objects()
    # Move small square slightly outside a container of same size
    moved_square = m.Square(side_length=1).move_to((0.1, 0, 0))
    container = m.Square(side_length=1).move_to((0, 0, 0))
    assert is_inside_bounds(moved_square, container, strict=True) is False


def test_slightly_overlapping_non_strict():
    """Object slightly overlapping should pass with strict=False"""
    moved_square = m.Square(side_length=1).move_to((0.1, 0, 0))
    container = m.Square(side_length=1).move_to((0, 0, 0))
    assert is_inside_bounds(moved_square, container, strict=False) is True


def test_inside_multiple_containers():
    """Should be inside the combined bounds of multiple containers"""
    square, circle, line, small_square = create_test_objects()
    container1 = m.Square(side_length=1).move_to((-1, 0, 0))
    container2 = m.Square(side_length=1).move_to((1, 0, 0))

    # Small square at origin should be inside the combined bounds
    assert is_inside_bounds(small_square, container1, container2, strict=True) is True


def test_floating_point_tolerance():
    """Test that floating point errors are handled with tolerance"""
    square, circle, line, small_square = create_test_objects()
    mob = m.Square(side_length=1).move_to((0, 0, -1e-17))
    assert is_inside_bounds(mob, small_square, strict=True) is True
    assert is_inside_bounds(mob, small_square, strict=False) is True


def test_square_not_inside_circle():
    """Square corners might not fit inside circle"""
    square, circle, line, small_square = create_test_objects()
    # A unit square's corners extend beyond a unit circle
    assert is_inside_bounds(small_square, circle, strict=True) is False


def test_offset_object_outside_bounds():
    """Offset object should be outside bounds of non-offset container"""
    square, circle, line, small_square = create_test_objects()
    assert (
        is_inside_bounds(square.shift(m.RIGHT * 2), small_square, strict=True) is False
    )


def test_single_point_inside():
    """Single point mobject should be inside any containing bounds"""
    square, circle, line, small_square = create_test_objects()
    point_mobject = m.Mobject()
    point_mobject.points = np.array([[0, 0, 0]])
    assert is_inside_bounds(point_mobject, small_square, strict=True) is True
    assert is_inside_bounds(point_mobject, small_square, strict=False) is True


def test_single_point_outside():
    """Single point outside bounds should fail"""
    square, circle, line, small_square = create_test_objects()
    point_mobject = m.Mobject()
    point_mobject.points = np.array([[10, 10, 0]])
    assert is_inside_bounds(point_mobject, small_square, strict=True) is False
    assert is_inside_bounds(point_mobject, small_square, strict=False) is False


def test_strict_false_allows_partial_overlap():
    """Non-strict mode should allow partial overlaps"""
    # Create two squares that partially overlap
    square1 = m.Square(side_length=2).move_to((0, 0, 0))
    square2 = m.Square(side_length=2).move_to((1, 0, 0))  # Partially overlapping

    # In strict mode, square2 should NOT be inside square1
    assert is_inside_bounds(square2, square1, strict=True) is False

    # In non-strict mode, square2 SHOULD overlap with square1
    assert is_inside_bounds(square2, square1, strict=False) is True


def test_identical_objects_strict():
    """Identical objects should pass in strict mode"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(square, square, strict=True) is True


def test_identical_objects_non_strict():
    """Identical objects should pass in non-strict mode"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(square, square, strict=False) is True


def test_include_stroke():
    square = m.Square(side_length=4, stroke_width=100)
    # square inside stroke: -1.5, 1.5
    # square path: -2, 2
    # square outside stroke: -2.5, 2.5
    circle1 = m.Circle(radius=1)
    circle2 = m.Circle(radius=1.7)
    circle3 = m.Circle(radius=2.2)
    circle4 = m.Circle(radius=2.7)
    # c1 < inner_stroke < c2 < path < c3 < outer_stroke < c4
    assert is_inside_bounds(circle1, square, include_stroke=False) is True
    assert is_inside_bounds(circle1, square, include_stroke=None) is True
    assert is_inside_bounds(circle1, square, include_stroke=True) is True

    assert is_inside_bounds(circle2, square, include_stroke=False) is False
    assert is_inside_bounds(circle2, square, include_stroke=None) is True
    assert is_inside_bounds(circle2, square, include_stroke=True) is True

    assert is_inside_bounds(circle3, square, include_stroke=False) is False
    assert is_inside_bounds(circle3, square, include_stroke=None) is False
    assert is_inside_bounds(circle3, square, include_stroke=True) is True

    assert is_inside_bounds(circle4, square, include_stroke=False) is False
    assert is_inside_bounds(circle4, square, include_stroke=None) is False
    assert is_inside_bounds(circle4, square, include_stroke=True) is False


def test_3d_object_in_3d_bounds():
    """Test with objects that have z-coordinates"""
    cube1 = m.Cube(side_length=2).move_to(m.ORIGIN)
    cube2 = m.Cube(side_length=1).move_to(m.ORIGIN)
    # Both should be in same plane, cube2 inside cube1
    assert is_inside_bounds(cube2, cube1, strict=True) is True
    assert is_inside_bounds(cube2, cube1, strict=False) is True
    cube2.shift((0, 0, 1))
    assert is_inside_bounds(cube2, cube1, strict=True) is False
    assert is_inside_bounds(cube2, cube1, strict=False) is True


def test_negative_coordinates():
    """Test with objects in negative coordinate space"""
    neg_square = m.Square(side_length=1).move_to((-2, -2, 0))
    container = m.Square(side_length=4).move_to((-2, -2, 0))
    assert is_inside_bounds(neg_square, container, strict=True) is True


def test_rotated_object():
    """Test rotated objects - bounding box should account for rotation"""
    rotated_square = m.Square(side_length=1).rotate(np.pi / 4).move_to(m.ORIGIN)
    container = m.Square(side_length=2).move_to(m.ORIGIN)
    assert is_inside_bounds(rotated_square, container, strict=True) is True


def test_empty_vmobjects_list():
    """Should handle empty vmobjects list gracefully"""
    square, circle, line, small_square = create_test_objects()
    assert is_inside_bounds(small_square) is False
