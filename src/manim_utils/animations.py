from collections.abc import Callable, Iterable
from typing import Any

import manim as m


class LazyAnimation(m.Animation):
    """An Animation that is built at play time.

    This is useful when the set of Mobjects to animate or the animation parameters
    change dynamically between the moment the Animation is declared and the moment
    it is played.

    Parameters
    ----------
    mobject_factory
        A callable that returns the Mobject (or Group) to be animated.
    animation_factory
        A callable that takes the Mobject and any additional parameter,
        returning an Animation instance.
    **kwargs
        Standard Animation keyword arguments (passed to parent Animation class).

    Examples
    --------
    >>> from manim import *
    >>> from manim_utils import LazyAnimation


    >>> class LazyAnimationScene(Scene):
    >>>     def construct(self) -> None:
    >>>         grp = VGroup(Circle(color=RED), Dot(color=GREEN), Rectangle(color=BLUE))
    >>>         self.add(grp.arrange(RIGHT))

    >>>         def mob_factory():
    >>>             return VGroup([mob for mob in grp if mob.color == RED])

    >>>         def animation_factory(mob):
    >>>             # args can be made dynamic too
    >>>             vec = RIGHT * len([mob for mob in grp if mob.color == GREEN])
    >>>             return ApplyMethod(mob.shift, vec)

    >>>         anim = LazyAnimation(
    >>>             mobject_factory=mob_factory,
    >>>             animation_factory=animation_factory,
    >>>         )

    >>>         # even mobjects that are changed after the animation is built will be
    >>>         # included
    >>>         grp[2].set_color(RED)
    >>>         grp.add(Dot(color=GREEN) for _ in range(4))
    >>>         self.play(anim, run_time=2)

    """

    def __init__(
        self,
        mobject_factory: Callable[..., m.Mobject],
        animation_factory: Callable[..., m.Animation],
        **kwargs: Any,
    ) -> None:
        self._mobject_factory = mobject_factory
        self._animation_factory = animation_factory
        super().__init__(None, **kwargs)

    def begin(self) -> None:
        """Construct the mobject and the inner animation just before playing."""
        self._mobject = self._mobject_factory()
        # Set the mobject for the parent class
        self.mobject = self._mobject  # type: ignore[assignment]

        self._animation = self._animation_factory(self._mobject)
        self._animation.begin()

    def finish(self) -> None:
        """Delegate finish to the inner animation."""
        self._animation.finish()

    def interpolate(self, alpha: float) -> None:
        """Delegate interpolation to the inner animation."""
        self._animation.interpolate(alpha)

    def update_mobjects(self, dt: float) -> None:
        """Delegate updater calls."""
        self._animation.update_mobjects(dt)

    def get_all_families_zipped(self) -> Iterable[tuple[m.Mobject, ...]]:
        """Ensure families are zipped based on the deferred mobject."""
        return self._animation.get_all_families_zipped()


class TrackedAnimationMixin:
    """A Mixin that adds tracking abilities to animations.

    Make sure the Mixin is first in the inheritance chain.

    Examples
    --------
    >>> from manim import *
    >>> from manim_utils import TrackedAnimationMixin


    >>> class TrackedAnimationScene(Scene):
    >>>     def construct(self) -> None:
    >>>         c = Circle()

    >>>         # Animation classes can be used directly
    >>>         class TrackedTransform(TrackedAnimationMixin, Transform): ...

    >>>         anim = TrackedTransform(c, Rectangle(), run_time=2)
    >>>         status_text = Text("").to_edge(DOWN)
    >>>         self.add(status_text)

    >>>         def update_status(mob, dt):
    >>>             if hasattr(anim, "_status"):
    >>>                 mob.become(Text(anim._status).to_edge(DOWN))

    >>>         status_text.add_updater(update_status)

    >>>         self.wait()
    >>>         self.play(anim)

    >>>         # .animate methods can be wrapped in ApplyMethod
    >>>         class TrackedApplyMethod(TrackedAnimationMixin, ApplyMethod): ...

    >>>         anim2 = TrackedApplyMethod(c.shift, RIGHT * 3)
    >>>         print(anim2._status)

    >>>         self.play(anim2)
    >>>         print(anim2._status)

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._status = "not played"

    def begin(self) -> None:
        self._status = "playing"
        super().begin()  # type: ignore[misc]

    def finish(self) -> None:
        super().finish()  # type: ignore[misc]
        self._status = "played"
