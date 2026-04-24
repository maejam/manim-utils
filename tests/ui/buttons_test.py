import manim as m
import pytest

from manim_utils.ui.buttons import Button, PushButton


# ----------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------
class TstButton(Button):
    """A minimal concrete button for testing the base Button class."""

    STATE_A = {"color": m.RED}
    STATE_B = {"color": m.BLUE}

    def _build_state(self, state_name: str) -> tuple[m.VGroup, m.VDict]:
        color = self.states[state_name]["color"]
        body = self._get_template().set_fill(color=color)
        contents = self._get_contents_template().set_fill(color=color)
        return m.VGroup(body), contents


@pytest.fixture
def btn():
    shape = m.Circle()
    return TstButton(shape=shape)


# ----------------------------------------------------------------------
# Button
# ----------------------------------------------------------------------
def test_button_initialization(btn):
    """Test that a button initializes with the first state."""
    assert btn.state == "STATE_A"
    assert len(btn._state_keys) == 2
    assert btn._state_keys == ["STATE_A", "STATE_B"]
    assert btn._state_index == 0
    assert btn.states == {
        "STATE_A": {"color": m.RED},
        "STATE_B": {"color": m.BLUE},
    }


def test_button_transition_next_state(btn):
    """Test transitioning to the next state automatically."""
    assert btn.state == "STATE_A"
    assert btn._state_index == 0
    btn.transition()
    assert btn.state == "STATE_B"
    assert btn._state_index == 1


def test_button_transition_wraps_around(btn):
    """Test that transitioning cycles back to the first state."""
    btn.transition()
    assert btn.state == "STATE_B"
    assert btn._state_index == 1

    btn.transition()
    assert btn.state == "STATE_A"
    assert btn._state_index == 0


def test_button_transition_explicit_state(btn):
    """Test transitioning to a specific named state."""
    btn.transition("STATE_B")
    assert btn.state == "STATE_B"

    btn.transition("STATE_A")
    assert btn.state == "STATE_A"


def test_button_transition_explicit_same_state(btn):
    """Test transitioning to the same named state."""
    btn.transition("STATE_B")
    assert btn.state == "STATE_B"
    assert btn._state_index == 1

    btn.transition("STATE_B")
    assert btn.state == "STATE_B"
    assert btn._state_index == 1


def test_button_transition_invalid_state(btn):
    """Test that transitioning to an invalid state raises ValueError."""
    with pytest.raises(
        ValueError,
        match=r"State 'INVALID_STATE' is not valid for TstButton. "
        r"Avalaible states: \['STATE_A', 'STATE_B'\]",
    ):
        btn.transition("INVALID_STATE")


def test_button_callback_execution():
    """Test that the callback is called during transition."""
    shape = m.Circle()
    call_log = []

    def mock_callback(button, from_state, to_state):
        call_log.append((button, from_state, to_state))

    btn = TstButton(shape=shape, callback=mock_callback)

    btn.transition()  # STATE_A -> STATE_B
    btn.transition()  # STATE_B -> STATE_A
    btn.transition("STATE_A")  # STATE_A -> STATE_A

    assert len(call_log) == 3
    assert call_log[0] == (btn, "STATE_A", "STATE_B")
    assert call_log[1] == (btn, "STATE_B", "STATE_A")
    assert call_log[2] == (btn, "STATE_A", "STATE_A")


def test_button_return_self(btn):
    """Test that transition returns the button instance for chaining."""
    result = btn.transition()
    assert result is btn


def test_swap_content_updates_displayed_content():
    shape = m.Circle()
    btn = TstButton(
        shape=shape,
        contents={"STATE_A": m.Text("A"), "STATE_B": m.Text("B")},
    )
    assert btn.content.text == "A"

    btn.swap_content("STATE_B")
    assert btn.content.text == "B"

    btn.transition()
    btn.swap_content("STATE_A")
    assert btn.content.text == "A"


def test_swap_content_defaults_to_current_state():
    shape = m.Circle()
    btn = TstButton(
        shape=shape,
        contents={"STATE_A": m.Text("A"), "STATE_B": m.Text("B")},
    )
    btn.transition("STATE_B")
    btn.swap_content()
    assert btn.content.text == "B"


def test_swap_content_empty_state():
    """Test swapping content when a state has an empty Mobject."""
    shape = m.Circle()
    contents = {
        "STATE_A": m.Text("A"),
        "STATE_B": m.VMobject(),  # Empty state
    }

    btn = TstButton(shape=shape, contents=contents)

    btn.transition("STATE_B")
    btn.swap_content()
    assert isinstance(btn.content, m.VMobject)
    assert len(btn.content.submobjects) == 0


def test_button_contents_initialized_with_None(btn):
    assert isinstance(btn._contents, m.VDict)
    assert list(btn._contents.submob_dict.keys()) == ["STATE_A", "STATE_B"]
    assert isinstance(btn._contents["STATE_A"], m.VMobject)
    assert isinstance(btn._contents["STATE_B"], m.VMobject)


def test_button_contents_initialized_with_dict():
    shape = m.Circle()
    d = m.Dot()
    r = m.Rectangle()
    btn = TstButton(shape=shape, contents={"STATE_A": d, "STATE_B": r})
    assert isinstance(btn._contents, m.VDict)
    assert list(btn._contents.submob_dict.keys()) == ["STATE_A", "STATE_B"]
    assert isinstance(btn._contents["STATE_A"], m.Dot)
    assert isinstance(btn._contents["STATE_B"], m.Rectangle)


def test_button_contents_initialized_with_single_vmob():
    shape = m.Circle()
    d = m.Dot()
    btn = TstButton(shape=shape, contents=d)
    assert isinstance(btn._contents, m.VDict)
    assert list(btn._contents.submob_dict.keys()) == ["STATE_A", "STATE_B"]
    assert isinstance(btn._contents["STATE_A"], m.Dot)
    assert isinstance(btn._contents["STATE_B"], m.Dot)
    assert btn._contents["STATE_A"] is btn._contents["STATE_B"]


def test_button_requires_all_states_in_contents():
    shape = m.Circle()
    # Missing STATE_B in contents should raise ValueError
    contents = {"STATE_A": m.VMobject()}

    with pytest.raises(ValueError, match="exactly one content VMobject for each state"):
        TstButton(shape=shape, contents=contents)


def test_button_contents_keys_must_match_states():
    shape = m.Circle()
    # Extra key not in states
    contents = {
        "STATE_A": m.VMobject(),
        "STATE_C": m.VMobject(),
    }

    with pytest.raises(KeyError, match="keys in the content dictionary should match"):
        TstButton(shape=shape, contents=contents)


def test_button_adds_all_components_in_init(btn):
    # Check that the button group contains the expected submobjects
    # Based on __init__: template, contents_template, deco_group, content
    assert len(btn.submobjects) == 4


# ----------------------------------------------------------------------
# PushButton
# ----------------------------------------------------------------------
def test_pushbutton_default_state():
    """Test that PushButton initializes to UNPUSHED."""
    shape = m.RoundedRectangle(corner_radius=0.3, width=3.0, height=1.2)
    contents = {"UNPUSHED": m.Text("Unpushed"), "PUSHED": m.Text("Pushed")}
    btn = PushButton(shape=shape, contents=contents)
    assert btn.state == "UNPUSHED"
    assert btn.content.text == "Unpushed"


def test_pushbutton_transition_changes_internal_properties():
    shape = m.Rectangle()
    pb = PushButton(shape=shape)

    assert pb.state == "UNPUSHED"
    pb.transition("PUSHED")
    assert pb.state == "PUSHED"

    pb.transition()
    assert pb.state == "UNPUSHED"


def test_pushbutton_build_state_returns_expected_structure():
    shape = m.Rectangle()
    pb = PushButton(shape=shape)

    deco_group, contents = pb._build_state("UNPUSHED")

    assert isinstance(deco_group, m.VGroup)
    assert isinstance(contents, m.VDict)

    # Check that deco_group has expected components (shadow, body, etc.)
    assert len(deco_group.submobjects) == 5


def test_pushbutton_callback_on_push():
    """Test callback execution specifically for PushButton transitions."""
    shape = m.RoundedRectangle(corner_radius=0.3, width=3.0, height=1.2)
    contents = {"UNPUSHED": m.Text("Unpushed"), "PUSHED": m.Text("Pushed")}
    transitions = []

    def track_transitions(btn, from_s, to_s):
        transitions.append((btn, from_s, to_s))

    btn = PushButton(shape=shape, contents=contents, callback=track_transitions)

    btn.transition()  # UNPUSHED -> PUSHED
    btn.transition()  # PUSHED -> UNPUSHED

    assert len(transitions) == 2
    assert transitions[0] == (btn, "UNPUSHED", "PUSHED")
    assert transitions[1] == (btn, "PUSHED", "UNPUSHED")
