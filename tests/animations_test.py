import manim as m
import numpy as np
import pytest

from manim_utils import LazyAnimation, TrackedAnimationMixin


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
def circle_factory():
    return m.Circle()


def applymeth_factory(mob):
    return m.ApplyMethod(mob.shift, m.RIGHT)


@pytest.fixture
def tracked_transform():
    class TrackedTransform(TrackedAnimationMixin, m.Transform): ...

    return TrackedTransform(m.Circle(), m.Rectangle())


@pytest.fixture
def tracked_apply_meth():
    class TrackedAppplyMeth(TrackedAnimationMixin, m.ApplyMethod): ...

    return TrackedAppplyMeth(m.Circle().shift, m.RIGHT)


# ----------------------------------------------------------------------
# LazyAnimation
# ----------------------------------------------------------------------
def test_lazy_animation_instantiation():
    anim = LazyAnimation(
        mobject_factory=circle_factory,
        animation_factory=applymeth_factory,
    )

    assert anim is not None
    assert anim._mobject_factory is circle_factory
    assert anim._animation_factory is applymeth_factory


def test_mobject_assigned_after_begin():
    anim = LazyAnimation(
        mobject_factory=circle_factory,
        animation_factory=applymeth_factory,
    )

    assert isinstance(anim.mobject, m.Mobject)
    assert not isinstance(anim.mobject, m.Circle)
    anim.begin()
    assert isinstance(anim.mobject, m.Circle)


def test_delegation_to_inner_animation():
    anim = LazyAnimation(
        mobject_factory=circle_factory,
        animation_factory=applymeth_factory,
    )

    anim.begin()

    # These should not raise AttributeError
    anim.interpolate(0.5)
    anim.update_mobjects(0.016)
    families = anim.get_all_families_zipped()
    assert isinstance(families, zip)


def test_finish_delegates_to_inner_animation():
    anim = LazyAnimation(
        mobject_factory=circle_factory,
        animation_factory=applymeth_factory,
    )

    anim.begin()
    # Should not raise
    anim.finish()


def test_dynamic_mobject_changes_are_captured():
    """Test that mobject changes before play are captured."""
    c = m.Circle(color=m.RED)
    d = m.Dot(color=m.GREEN)
    grp = m.VGroup(c, d)

    def mob_factory():
        return m.VGroup([mob for mob in grp if mob.color == m.RED])

    anim = LazyAnimation(
        mobject_factory=mob_factory,
        animation_factory=applymeth_factory,
    )

    grp[1].set_color(m.RED)

    s = m.Scene()
    pos_c = c.get_center()
    pos_d = d.get_center()
    s.play(anim)

    assert len(anim.mobject) == 2
    assert not np.allclose(pos_c, c.get_center())
    assert not np.allclose(pos_d, d.get_center())


# ----------------------------------------------------------------------
# TrackedAnimationMixin
# ----------------------------------------------------------------------
def test_tracked_mixin_initial_status(tracked_transform, tracked_apply_meth):
    assert tracked_transform._status == "not played"
    assert tracked_apply_meth._status == "not played"


def test_tracked_mixin_status_after_begin(tracked_transform, tracked_apply_meth):
    tracked_transform.begin()
    assert tracked_transform._status == "playing"
    tracked_apply_meth.begin()
    assert tracked_apply_meth._status == "playing"


def test_tracked_mixin_status_after_finish(tracked_transform, tracked_apply_meth):
    tracked_transform.begin()
    tracked_transform.finish()
    assert tracked_transform._status == "played"
    tracked_apply_meth.begin()
    tracked_apply_meth.finish()
    assert tracked_apply_meth._status == "played"


def test_tracked_mixin_multiple_begin_finish_cycles(
    tracked_transform, tracked_apply_meth
):
    # First cycle
    assert tracked_transform._status == "not played"
    tracked_transform.begin()
    assert tracked_transform._status == "playing"
    tracked_transform.finish()
    assert tracked_transform._status == "played"

    # Second cycle
    tracked_transform.begin()
    assert tracked_transform._status == "playing"
    tracked_transform.finish()
    assert tracked_transform._status == "played"

    # First cycle
    assert tracked_apply_meth._status == "not played"
    tracked_apply_meth.begin()
    assert tracked_apply_meth._status == "playing"
    tracked_apply_meth.finish()
    assert tracked_apply_meth._status == "played"

    # Second cycle
    tracked_apply_meth.begin()
    assert tracked_apply_meth._status == "playing"
    tracked_apply_meth.finish()
    assert tracked_apply_meth._status == "played"
