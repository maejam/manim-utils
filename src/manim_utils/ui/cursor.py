from collections.abc import Iterable
from pathlib import Path
from typing import Any, Self

import manim as m
import numpy as np


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
    click
        Path to a click sound file. Usage in scenes: `self.add_sound(Cursor.click)`.
    cursors
        Dictionary of available cursor shapes. Identifiers are the file names
        capitalized.
    idle_duration
        Time in seconds of inactivity before the fade-out process begins. Set to `None`
        to disable the automatic fade-out.

    Parameters
    ----------
    svg_paths
        Additional directories to scan for cursor SVG files. Defaults to empty tuple.
    idle_duration
        Seconds of inactivity before fading starts. If None, fading is disabled.
        Defaults to 4.0.
    fade_duration
        Duration of the fade-out effect in seconds. Defaults to 1.0.
    **kwargs
        Additional keyword arguments passed to the parent `VMobject`.

    """

    DEFAULT_PATH: Path = Path(__file__).parent / "assets/cursors/"
    click: str = str(Path(__file__).parent / "assets/click.wav")

    def __init__(
        self,
        svg_paths: Iterable[Path | str] = (),
        idle_duration: float | None = 4,
        fade_duration: float = 1,
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
        self._fade_duration = fade_duration
        self._idle_time = m.ValueTracker(0)
        self._last_pos = self.get_center()
        self.become(m.SVGMobject(self.cursors["LEFT_PTR"]))
        self.set_stroke(width=4)
        self._scale_factor = 1.0
        self.scale(0.2)

    @property
    def idle_duration(self) -> float:
        if self._idle_duration is None:
            raise ValueError("No idle duration set on this cursor.")
        return self._idle_duration

    @idle_duration.setter
    def idle_duration(self, duration: float | None) -> None:
        self.remove_updater(self._idle_fade)
        if duration is not None:
            self.add_updater(self._idle_fade)
        self._idle_duration = duration

    def _idle_fade(self, mob: m.Mobject, dt: float) -> None:
        if not np.allclose(self.get_center(), self._last_pos):
            self._idle_time.set_value(0)
            self._last_pos = self.get_center()

        self._idle_time.increment_value(dt)
        if self._idle_time.get_value() > self.idle_duration:
            new_opacity = max(
                0,
                1
                - (self._idle_time.get_value() - self.idle_duration)
                / self._fade_duration,
            )
            self.set_opacity(new_opacity)
        else:
            self.set_opacity(1)

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
        self._idle_time.set_value(0)
        return self

    def scale(self, scale_factor: float, **kwargs: Any) -> Self:  # type: ignore[override]
        self._scale_factor *= scale_factor
        return super().scale(scale_factor, **kwargs)
