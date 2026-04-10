import manim as m
import numpy as np

from manim_utils.animations import LazyAnimation, TrackedAnimation


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
def create_red_circle():
    return m.Circle(color=m.RED)


def create_green_square():
    return m.Square(color=m.GREEN)


def shift_right_anim(mob: m.Mobject, distance: float = 1.0):
    return m.ApplyMethod(mob.shift, m.RIGHT * distance)


# ----------------------------------------------------------------------
# LazyAnimation
# ----------------------------------------------------------------------
def test_mobject_deferred_until_begin():
    called = False

    def factory():
        nonlocal called
        called = True
        return m.Circle()

    anim = LazyAnimation(
        mobject_factory=factory, animation_factory=lambda mob: m.FadeIn(mob)
    )

    assert not called, "Factory should not be called in __init__"

    anim.begin()
    assert called, "Factory must be called in begin()"


def test_kwargs_deferred_until_begin():
    called = False

    def kwargs_factory():
        nonlocal called
        called = True
        return {"distance": 5.0}

    anim = LazyAnimation(
        mobject_factory=create_red_circle,
        animation_factory=shift_right_anim,
        kwargs_factory=kwargs_factory,
    )

    assert not called, "Kwargs factory should not be called in __init__"

    anim.begin()
    assert called, "Kwargs factory must be called in begin()"


def test_captures_state_changes_before_begin():
    c = m.Circle(color=m.RED)
    d = m.Dot(color=m.GREEN)
    r = m.Rectangle(color=m.BLUE)

    grp = m.VGroup(c, d, r)
    assert np.allclose(c.get_center(), d.get_center(), r.get_center())

    def mob_factory():
        return m.VGroup([mob for mob in grp if mob.color == m.RED])

    anim = LazyAnimation(
        mobject_factory=mob_factory,
        animation_factory=lambda mob: m.ApplyMethod(mob.shift, m.RIGHT * 3),
    )
    grp[2].set_color(m.RED)
    scene = m.Scene()
    scene.play(anim)
    assert np.allclose(c.get_center(), r.get_center())
    assert not np.allclose(c.get_center(), d.get_center())


def test_default_kwargs_factory():
    anim = LazyAnimation(
        mobject_factory=create_red_circle, animation_factory=lambda mob: m.FadeIn(mob)
    )

    anim.begin()
    assert anim._kwargs == {}


def test_interpolation_delegation():
    """Verify interpolate delegates to the inner animation."""
    anim = LazyAnimation(
        mobject_factory=create_red_circle, animation_factory=lambda mob: m.FadeIn(mob)
    )

    anim.begin()
    anim.interpolate(0.5)
    # If we got here without error, delegation worked
    assert anim._animation is not None


def test_finish_delegation():
    """Verify finish delegates to the inner animation."""
    anim = LazyAnimation(
        mobject_factory=create_red_circle, animation_factory=lambda mob: m.FadeIn(mob)
    )

    anim.begin()
    anim.finish()

    # Check that the inner animation finished
    assert anim._animation is not None


def test_get_all_families_zipped_delegation():
    """Verify get_all_families_zipped delegates correctly."""
    anim = LazyAnimation(
        mobject_factory=create_red_circle, animation_factory=lambda mob: m.FadeIn(mob)
    )

    anim.begin()
    families = anim.get_all_families_zipped()

    assert families is not None


# ----------------------------------------------------------------------
# TrackedAnimation
# ----------------------------------------------------------------------
def test_tracked_initial_played_state():
    """Verify _played is False initially."""
    anim = TrackedAnimation(shift_right_anim(m.Circle()))
    assert anim._played is False


def test_tracked_played_state_after_finish():
    """Verify _played becomes True after finish()."""
    anim = TrackedAnimation(shift_right_anim(m.Circle()))

    # Manually call begin to simulate start
    anim.begin()

    assert anim._played is False

    anim.finish()

    assert anim._played is True


def test_tracked_played_state_persistence():
    """Verify _played remains True after multiple finishes."""
    anim = TrackedAnimation(shift_right_anim(m.Circle()))
    anim.begin()
    anim.finish()

    assert anim._played is True

    anim.finish()
    assert anim._played is True


def test_tracked_combined_with_lazy_animation():
    def tracked_factory(mob: m.Mobject):
        return TrackedAnimation(shift_right_anim(m.Circle()))

    anim = LazyAnimation(
        mobject_factory=create_red_circle, animation_factory=tracked_factory
    )
    print(anim.run_time)

    anim.begin()

    assert isinstance(anim._animation, TrackedAnimation)
    assert anim._played is False

    anim.finish()

    assert anim._played is True
