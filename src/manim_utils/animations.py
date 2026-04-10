from collections.abc import Callable, Iterable, Mapping
from typing import Any

import manim as m


class LazyAnimation(m.Animation):
    """An Animation that is built at play time.

    This is useful when the set of Mobjects to animate or the animation parameters
    change dynamically between the moment the Animation is constructed and the moment
    it is played. See a toy example below and a useful one in
    `Grid.insert_row <https://github.com/maejam/manim-grid/blob/main/src/manim_grid/grid.py#L720-L858>`_

    Parameters
    ----------
    mobject_factory
        A callable that returns the Mobject (or Group) to be animated.
    animation_factory
        A callable that takes the Mobject and kwargs, returning an Animation instance.
    kwargs_factory
        A callable that returns the kwargs dict for the animation.
    **kwargs
        Standard Animation keyword arguments (passed to parent Animation class).

    Examples
    --------
    >>> class LazyAnimationScene(m.Scene):
    >>>     def construct(self) -> None:
    >>>         grp = m.VGroup(
    >>>             Circle(color=m.RED), m.Dot(color=m.GREEN), m.Rectangle(color=m.BLUE)
    >>>         )
    >>>         self.add(grp.arrange(m.RIGHT))

    >>>         def mob_factory():
    >>>             return m.VGroup([mob for mob in grp if mob.color == m.RED])

    >>>         anim = LazyAnimation(
    >>>             mobject_factory=mob_factory,
    >>>             animation_factory=lambda mob: m.ApplyMethod(mob.shift, m.RIGHT * 3),
    >>>         )

    >>>         # even mobjects that are changed after the animation is built will be
    >>>         # included
    >>>         grp[2].set_color(m.RED)
    >>>         self.play(anim, run_time=2)

    """

    def __init__(
        self,
        mobject_factory: Callable[[], m.Mobject],
        animation_factory: Callable[..., m.Animation],
        kwargs_factory: Callable[[], Mapping[str, Any]] = lambda: {},
        **kwargs: Any,
    ) -> None:
        self._mobject_factory = mobject_factory
        self._animation_factory = animation_factory
        self._kwargs_factory = kwargs_factory
        super().__init__(None, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the inner animation.

        Useful for example when using in conjunction with :clss:`TrackedAnimation`:
        `anim._played` can be used instead of `anim._animation._played`.

        """
        animation = self.__dict__.get("_animation")
        if animation is not None:
            return getattr(animation, name)
        else:
            return super().__getattribute__(name)

    def begin(self) -> None:
        """Construct the mobject and the inner animation just before playing."""
        self._mobject = self._mobject_factory()
        # Set the mobject for the parent class
        self.mobject = self._mobject  # type: ignore[assignment]

        self._kwargs = self._kwargs_factory()
        self._animation = self._animation_factory(self._mobject, **self._kwargs)
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


class TrackedAnimation(m.Animation):
    """An Animation subclass that tracks if the animation has been played.

    Parameters
    ----------
    animation
        The animation to track.
    **kwargs
        Additional keyword arguments forwarded to the animation constructor.

    Examples
    --------
    >>> class TrackedAnimationScene(m.Scene):
    >>>     def construct(self) -> None:
    >>>         c = m.Circle()

    >>>         # .animate methods can be wrapped in ApplyMethod
    >>>         anim = TrackedAnimation(m.ApplyMethod(c.shift, m.RIGHT * 3), run_time=2)
    >>>         print(anim._played)
    'False'

    >>>         self.play(anim)
    >>>         print(anim._played)
    'True'

    >>>         # Animation classes can be used directly
    >>>         anim2 = TrackedAnimation(m.Transform(c, m.Rectangle()))
    >>>         print(anim2._played)
    'False'

    >>>         self.play(anim2)
    >>>         print(anim2._played)
    'True'


    """

    def __init__(self, animation: m.Animation, **kwargs: Any) -> None:
        if not isinstance(animation, m.Animation):
            raise TypeError(
                f"TrackedAnimation expects an Animation instance, got {type(animation)}"
            )
        super().__init__(animation.mobject, **kwargs)

        self._animation = animation
        self._played = False

    def begin(self) -> None:
        """Start the inner animation."""
        self._animation.begin()

    def finish(self) -> None:
        """Finish the inner animation and mark as played."""
        self._animation.finish()
        self._played = True

    def interpolate(self, alpha: float) -> None:
        """Delegate interpolation."""
        self._animation.interpolate(alpha)

    def update_mobjects(self, dt: float) -> None:
        """Delegate updates."""
        self._animation.update_mobjects(dt)

    def get_all_families_zipped(self) -> Iterable[tuple[m.Mobject, ...]]:
        """Delegate family zipping."""
        return self._animation.get_all_families_zipped()
