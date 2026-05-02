from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Self

import manim as m
import numpy as np
from manim.mobject.mobject import _AnimationBuilder
from manim.typing import Point3DLike
from manim.utils.rate_functions import RateFunction

from manim_utils.animations import CallbackAnimation


class Cursor(m.VMobject):
    """A VMobject representing a mouse cursor with idle-fading capabilities.

    This class loads cursor SVGs from specified directories, manages state transitions
    (e.g., switching cursor types), and automatically fades the cursor when it remains
    stationary for a configured duration.

    Attributes
    ----------
    DEFAULT_PATH
        Default directory path to scan for cursor SVG files. The library comes with
        40+ cursor shapes in this default path.
    click_sound
        Path to a click sound file. Usage in scenes:
        `self.add_sound(Cursor.click_sound)` or through the :meth:`click` method.
    cursors
        Dictionary of available cursor shapes. Identifiers are the file names
        capitalized.

    Parameters
    ----------
    svg_paths
        Additional directories to scan for cursor SVG files. Defaults to empty tuple.
    idle_duration
        Seconds of inactivity before fading starts. If negative, fading is disabled.
        Defaults to 4.0.
    fade_duration
        Duration of the fade-out effect in seconds. Defaults to 1.0.
    speed
        The speed of the cursor in munits per second. Defaults to 2.0.
        Only applied in internal methods such as :meth:`click`.
    rate_func
        The rate function to apply to the cursor movements in internal methods.
    **kwargs
        Additional keyword arguments passed to the parent `VMobject`.

    Note
    ----
    Moving the cursor with the `.animate` syntax or through the :meth:`click` method
    will set its opacity to 1 and reset the idle timer. Moving it any other way (e.g.
    through an animation such as `MoveToTarget`, or a simple unnanimated `move_to`) will
    keep its opacity as it was and will not reset the timer. This was initially done to
    circumvent a difficulty with the way interpolation works, but can actually be
    considered a feature.

    """

    DEFAULT_PATH: Path = Path(__file__).parent / "assets/cursors/"
    click_sound: str = str(Path(__file__).parent / "assets/click.wav")

    def __init__(
        self,
        svg_paths: Iterable[Path | str] = (),
        idle_duration: float = 4.0,
        fade_duration: float = 1.0,
        speed: float = 2.0,
        rate_func: RateFunction = m.smooth,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.cursors: dict[str, Path] = {}
        paths_to_scan: list[Path] = [self.DEFAULT_PATH]
        paths_to_scan.extend(Path(path) for path in svg_paths)
        for path in paths_to_scan:
            if not path.exists():
                m.logger.warning("The path %s does not exist. Skipping.", repr(path))
                continue

            for svg_file in path.rglob("*.svg"):
                key = svg_file.stem.upper()

                if key in self.cursors:
                    m.logger.warning(
                        "Warning: Duplicate cursor %s found. Overwriting %s with %s",
                        repr(key),
                        repr(self.cursors[key]),
                        repr(svg_file),
                    )
                self.cursors[key] = svg_file

        self.idle_duration = idle_duration
        self.fade_duration = fade_duration
        self._idle_time = 0.0
        self._last_pos = self.get_center()
        self.speed = speed
        self.rate_func = rate_func
        self.become(m.SVGMobject(self.cursors["LEFT_PTR"]))
        self.set_stroke(width=2)
        self._scale_factor = 1.0
        self.scale(0.1)

    @property
    def animate(self) -> _AnimationBuilder | Self:
        # NOTE: we override .animate because otherwise opacity would be interpolated
        # with movement, making the cursor reappear progressively. Opacity needs to be
        # set to 1 BEFORE the animation even starts
        self.set_opacity(1)
        if self.idle_duration > 0:
            self._idle_time = 0.0
            self.add_updater(self._idle_fade)
        return super().animate

    def _idle_fade(self, mob: m.Mobject, dt: float) -> None:
        self._idle_time += dt

        # keep opacity 1 while cursor is moving and reset timer
        if not np.array_equal(self.get_center(), self._last_pos):
            self._last_pos = self.get_center()
            self._idle_time = 0.0
            self.set_opacity(1)
            return

        # progressively fadeout if timer is above threshold
        if self._idle_time > self.idle_duration:
            new_opacity = max(
                0,
                1 - (self._idle_time - self.idle_duration) / self.fade_duration,
            )
            self.set_opacity(new_opacity)

        # remove updater as soon as cursor opacity is 0
        if self.fill_opacity == 0:
            self.remove_updater(self._idle_fade)

    def set_cursor(self, target: str) -> Self:
        """Switch the cursor to a different shape.

        Replaces the current visual representation with the specified cursor type and
        resets the idle timer.

        Parameters
        ----------
        target
            The uppercase identifier of the target cursor (e.g., "HAND2").

        Returns
        -------
        Self
            The Cursor instance for method chaining.

        Raises
        ------
        ValueError
            If the `target` identifier is not found in the loaded cursors.

        """
        if target not in self.cursors:
            raise ValueError(f"Unknown cursor: {target}.")
        self.match_points(m.SVGMobject(self.cursors[target]).move_to(self))
        super().scale(self._scale_factor)
        self._idle_time = 0.0
        return self

    def scale(self, scale_factor: float, **kwargs: Any) -> Self:  # type: ignore[override]
        self._scale_factor *= scale_factor
        return super().scale(scale_factor, **kwargs)

    def click(
        self,
        target: Point3DLike | m.Mobject,
        callback: Callable[..., Any] | None = None,
        animation: Any = None,
        **kwargs: Any,
    ) -> m.Succession:
        """Click a target.

        Moves the cursor to a given mobject or point, run a callback function and play
        an animation that is the result of the click.

        Parameters
        ----------
        target
            The Mobject or point to move the cursor to.
        callback
            A callback function that will be played after the cursor has moved to the
            target, but before the animation triggered by the click.
            A typical use-case is to play a click sound.
        animation
            The animation that will be played as a result of the click. Leave the `None`
            default to play no animation.
        **kwargs
            Keyword arguments passed to the generated Succession object.

        Returns
        -------
        Succession
            The Succession containing the animations ready to be played.

        """
        if isinstance(target, m.Mobject):
            target = target.get_center()

        self.set_opacity(1)
        if self.idle_duration > 0:
            self._idle_time = 0.0
            self.add_updater(self._idle_fade)

        # compute run_time based on distance to move for
        run_time = np.linalg.norm(self.get_center() - target) / self.speed
        self.generate_target()
        self.target.move_to(target)  # pyright: ignore[reportOptionalMemberAccess]
        move_anim = m.MoveToTarget(self, run_time=run_time, rate_func=self.rate_func)
        animations: list[m.Animation] = [move_anim]

        if callback is not None:
            animations.append(
                CallbackAnimation(callback=callback, delay=0.0, run_time=0.01)
            )

        if animation is not None:
            animations.append(animation)

        return m.Succession(*animations, **kwargs)
