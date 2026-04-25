from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Mapping
from typing import (
    Any,
    Self,
    cast,
)

import manim as m


class Button(m.VGroup, ABC):
    """Define behaviour for all types of buttons.

    Concrete Buttons define their possible states and how to build them.
    This class defines how to transition from one state to another. It also provides a
    callback mechanism to execute code when a transition occurs as well as per-state
    content.

    The possible states MUST be defined as class level dictionaries with ALL-CAPS keys
    and must not start with an underscore.

    Parameters
    ----------
    shape
        A VMobject that defines the outer shape of the button. All its attributes will
        be kept: size, color, opacity...
    callback
        Optional callback function that will be called for each transition.
        Takes 3 inputs: the button instance, the state name it is transitioning from
        and the one it is transitioning to.
    contents
        The content displayed on the button for each state. Possible values:
        - `None` (default): the VMobjects for each state will default to empty
          VMobjects, effectively displaying nothing.
        - A mapping from state names to VMobjects associating each state to a different
          VMobject. Every state key must be defined.
        - A single VMobject that will be used for every state.
        In any case, it is the user responsibility to call `swap_content` to update the
        displayed content.
    kwargs
        Keyword arguments forwarded to the superclass VGroup.

    """

    # NOTE: the goal of `_template` and `_contents_template` is to record all
    # transformations on the button. States must be built from them using the helper
    # methods `_get_template` and `_get_contents_template`

    def __init__(
        self,
        shape: m.VMobject,
        callback: Callable[["Button", str, str], None] = (
            lambda button, from_state, to_state: None
        ),
        contents: Mapping[str, m.VMobject] | m.VMobject | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._shape = shape
        self._template = self._shape.copy().set_fill(opacity=0).set_stroke(opacity=0)
        self._callback = callback

        self.states = self._get_states()
        self._state_keys = list(self.states)
        self._state_index = 0
        first_state = next(iter(self.states))
        self.state = first_state

        self._contents = self._get_contents(contents)
        self._contents_template = (
            self._contents.copy().set_fill(opacity=0).set_stroke(opacity=0)
        )
        self.content = self._contents[self.state]

        self._deco_group, self._contents = self._build_state(first_state)
        self.add(
            self._template,
            self._contents_template,
            self._deco_group,
            self.content,
        )

    def _get_states(self) -> dict[str, dict[str, Any]]:
        """Build the state dictionary."""
        states = {}
        for cls in type(self).__mro__:
            for k, v in cls.__dict__.items():
                if isinstance(v, dict) and not k.startswith("_") and k.isupper():
                    states[k] = v
        return states

    def _get_contents(
        self, contents: Mapping[str, m.VMobject] | m.VMobject | None
    ) -> m.VDict:
        """Build the VDict of contents."""
        if contents is None:
            contents_vd = m.VDict(
                {cast(Hashable, k): m.VMobject() for k in self._state_keys}
            )
        elif isinstance(contents, m.VMobject):
            contents_vd = m.VDict(
                cast(
                    Mapping[Hashable, m.VMobject],
                    dict.fromkeys(self._state_keys, contents),
                )
            )
        else:
            contents_vd = m.VDict(cast(Mapping[Hashable, m.VMobject], contents))

        if len(contents_vd.submob_dict) != len(self._state_keys):
            raise ValueError(
                "You must provide exactly one content VMobject for each state. "
                "Provide an empty `VMobject()` if a given state should be content-free."
            )

        if set(self.states.keys()) != set(contents_vd.submob_dict.keys()):
            raise KeyError(
                "The keys in the content dictionary should match the button states: "
                f"{self._state_keys}"
            )

        return contents_vd

    @abstractmethod
    def _build_state(self, state_name: str) -> tuple[m.VGroup, m.VDict]:
        """Define how to build a state from the state dictionary."""

    def transition(self, state_name: str | None = None) -> Self:
        """Transition to another state.

        If `state_name` is not provided, the button will transition to its next state
        in the order they are defined, starting over from the first one when
        transitioning from the last one.

        """
        if state_name is None:
            self._state_index = (self._state_index + 1) % len(self._state_keys)
            state_name = self._state_keys[self._state_index]
        else:
            try:
                self._state_index = self._state_keys.index(state_name)
            except ValueError:
                raise ValueError(
                    f"State {state_name!r} is not valid for {type(self).__name__}. "
                    f"Avalaible states: {self._state_keys}"
                ) from None

        deco_group, self._contents = self._build_state(state_name)
        from_state = self.state
        self.state = state_name
        self._deco_group.become(deco_group)
        self._callback(self, from_state, self.state)
        return self

    def swap_content(self, to_state: str | None = None) -> Self:
        """Update the content to a given button state.

        Parameters
        ----------
        to_state
            The content associated with the given state will be displayed on the button.
            If `None` is given (default) the content displayed will be the current
            button state.

        """
        if to_state is None:
            to_state = self.state
        self.remove(self.content)
        self.content = self._contents[to_state]
        self.add(self.content)
        return self

    def _get_template(self) -> m.VMobject:
        return (
            self._template.copy()
            .set_fill(opacity=self._shape.fill_opacity)
            .set_stroke(opacity=self._shape.stroke_opacity)
        )

    def _get_contents_template(self) -> m.VDict:
        templates = self._contents_template.copy()
        for state, content in templates.submob_dict.items():
            content.set_fill(opacity=self._contents[state].fill_opacity).set_stroke(
                opacity=self._contents[state].stroke_opacity
            )
        return templates


class ButtonGroup(m.VGroup):
    """Group buttons together to apply group logic to transitions.

    ButtonGroup is a VGroup of Buttons with a group level callback function.

    Parameters
    ----------
    *buttons
        The buttons to initially add to the ButtonGroup.
    callback
        A group level callback that will wrap individual buttons callbacks.
    **kwargs
        Keyword arguments forwarded to the parent VGroup.

    Notes
    -----
    A button can belong to multiple Groups at the same time. The original button
    callback will be called first and only once. The group callbacks will be
    called in the same order the button was added to the groups.

    A button that is removed from a ButtonGroup will still have its callback wrapped
    in the group callback.

    """

    def __init__(
        self,
        *buttons: Button,
        callback: Callable[["ButtonGroup", Button, str, str], None] = (
            lambda group, button, from_state, to_state: None
        ),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._callback = callback
        self.add(*buttons)

    def add(self, *buttons: Button) -> Self:  # type: ignore[override]
        """Add new buttons to the ButtonGroup."""
        # Wrap the callback for each button to inject group logic
        for btn in buttons:
            if btn in self.submobjects:
                return self

            original_callback = btn._callback

            def make_wrapper(
                b: Button, orig_cb: Callable[[Button, str, str], None]
            ) -> Callable[[Button, str, str], None]:
                def wrapper(button: "Button", from_state: str, to_state: str) -> None:
                    # call the button original callback
                    orig_cb(button, from_state, to_state)

                    # call the group callback
                    self._callback(self, button, from_state, to_state)

                return wrapper

            btn._callback = make_wrapper(btn, original_callback)

        return super().add(*buttons)


class PushButton(Button):
    """A 2-state button: PUSHED/UNPUSHED with a bevel effect.

    Default values are optimized for rectangular buttons. If needed, tweak by modifying
    the state dictionaries after instantiating the button. Example:
    `button.states["UNPUSHED"][shadow_opacity] = 0.1`

    or subclass for a reusable solution.

    """

    UNPUSHED = {
        "color_interpolation_factor": 0.0,
        "scale_factor": 1.0,
        "shadow_opacity": 0.25,
        "shadow_offset": 0.08,
        "highlight_opacity": 0.15,
        "highlight_offset": 0.04,
        "inner_shadow_opacity": 0.0,
        "inner_shadow_offset": 0.0,
        "inner_highlight_opacity": 0.0,
        "inner_highlight_offset": 0.0,
    }
    PUSHED = {
        "color_interpolation_factor": 0.15,
        "scale_factor": 0.96,
        "shadow_opacity": 0.0,
        "shadow_offset": 0.0,
        "highlight_opacity": 0.0,
        "highlight_offset": 0.0,
        "inner_shadow_opacity": 0.30,
        "inner_shadow_offset": 0.06,
        "inner_highlight_opacity": 0.15,
        "inner_highlight_offset": 0.04,
    }

    def _build_state(self, state_name: str) -> tuple[m.VGroup, m.VDict]:
        state_dict = self.states[state_name]

        # shadow
        shadow = self._get_template().set_stroke(width=0)
        shadow.set_fill(m.BLACK, opacity=state_dict["shadow_opacity"])
        shadow.shift(m.DR * state_dict["shadow_offset"])

        # body
        color = m.interpolate_color(
            self._shape.fill_color,
            m.BLACK,
            state_dict["color_interpolation_factor"],
        )
        body = self._get_template()
        body.set_fill(color=color)

        # inner shadow
        inner_shadow = self._get_template().set_stroke(width=0)
        inner_shadow.set_fill(m.BLACK, opacity=state_dict["inner_shadow_opacity"])
        inner_shadow.shift(m.UL * state_dict["inner_shadow_offset"])

        # highlight
        highlight = self._get_template().set_stroke(width=0)
        highlight.set_fill(m.WHITE, opacity=state_dict["highlight_opacity"])
        highlight.shift(m.UL * state_dict["highlight_offset"])

        # inner highlight
        inner_highlight = self._get_template().set_stroke(width=0)
        inner_highlight.set_fill(m.WHITE, opacity=state_dict["inner_highlight_opacity"])
        inner_highlight.shift(m.UL * state_dict["inner_highlight_offset"])

        # contents
        contents = self._get_contents_template()

        # assemble and scale
        deco_group = m.VGroup(
            shadow, body, inner_shadow, highlight, inner_highlight, contents
        )
        deco_group.scale(state_dict["scale_factor"])
        # contents are scaled. Now remove them so that they do not morph with become
        deco_group.remove(contents)

        return deco_group, contents


class HighlightButton(Button):
    """A 2-state button: ACTIVE/INACTIVE.

    ACTIVE state displays a highlight (glow) effect on the button.
    INACTIVE state displays the button without the highlight and slightly greyed out.

    """

    INACTIVE = {
        "color_interpolation_factor": 0.25,
        "stroke_opacity": 0.0,
        "stroke_width": 0,
        "stroke_color": m.WHITE,
        "fill_opacity": 0.5,
    }

    ACTIVE = {
        "color_interpolation_factor": -0.2,
        "stroke_opacity": 1.0,
        "stroke_width": 3,
        "stroke_color": m.YELLOW,
        "fill_opacity": 1.0,
    }

    def _build_state(self, state_name: str) -> tuple[m.VGroup, m.VDict]:
        state_dict = self.states[state_name]

        color = m.interpolate_color(
            self._shape.fill_color,
            m.BLACK,
            state_dict["color_interpolation_factor"],
        )
        body = self._get_template()
        body.set_fill(color=color, opacity=state_dict["fill_opacity"])
        body.set_stroke(
            color=state_dict["stroke_color"],
            opacity=state_dict["stroke_opacity"],
            width=state_dict["stroke_width"],
        )

        # contents
        contents = self._get_contents_template()

        # assemble
        deco_group = m.VGroup(body)

        return deco_group, contents
