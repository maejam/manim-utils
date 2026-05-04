# Manim Utils – A collection of lightweight manim utilities.

## Table of Contents

- [Installation](#installation)
- [Utilities](#utilities)
  - [Stencil](#stencil)
  - [code](#code)
  - [animations](#animations)
  - [ui](#ui)
    - [Buttons](#Buttons)
    - [Cursor](#Cursor)
  - [groups](#groups)

---

## Installation

For now there is no Pypi package. Install by adding to your `manim` project:  
- create the project if necessary:  
```bash
uv init myproject
cd myproject
```
- add the plugin to your newly created or existing project:  
```bash
uv add git+https://github.com/maejam/manim-utils.git
```
Requires `Python >= 3.10, < 3.14` and `manim >= 0.19`  

---

## Utilities

### Stencil

Build a new `VMobject` by applying a Boolean operation (Difference, Exclusion, Intersection, Union, or a custom callable) to a *shape* and a *clip* object. It also supports an optional *wrapped* object to automatically update the stencil outer geometry to the wrapped Mobject shape and position.

#### Example
```python

from manim import *

from manim_utils import Stencil


class StencilDemo(Scene):
    def construct(self):
        dots = VGroup(
            *[
                Dot(point=(x, y, 0.0), radius=0.07, color=BLUE)
                for x in np.arange(-6.0, 6.5, 0.5)
                for y in np.arange(-4.0, 4.5, 0.5)
            ]
        )

        stencil = Stencil(
            # shape=Circle(), # The outer stencil shape. Rectangle by default.
            wrapped=dots,  # The optional wrapped content. The stencil will adapt to its shape and position.
            clip=Star(),  # The clip path.
            bool_op=Difference,  # Type of boolean operation to apply to the shape and the clip.
            fill_opacity=0.8,  # 1 by default.
            fill_color=RED,  # config.background_color by default.
            stroke_width=1,  # Any other kwargs will be applied to the computed stencil.
        )
        self.add(dots, stencil)

        # Animating the shape or the clip will update the stencil.
        # If wrapped is not None, animating it (here the dots) will also update the
        # stencil to fully cover the wrapped content.
        self.play(
            stencil.clip.animate.become(Circle()).shift(RIGHT * 3 + UP * 1).scale(1.5),
            run_time=4,
            rate_func=there_and_back,
        )
        self.wait(1)
```  

See the docstrings in `manim_utils.stencil` for more details.  


### Code  

A set of utilities to manipulate code in your manim scenes. This is designed to be more flexible and lightweight than the manim `Code` Mobject. Can be used with [Paragraph](https://docs.manim.community/en/stable/reference/manim.mobject.text.text_mobject.Paragraph.html), [Table](https://docs.manim.community/en/stable/reference/manim.mobject.table.Table.html) or [manim-grid](https://github.com/maejam/manim-grid) for instance.

It provides 2 functions:
* `highlight_code`: returns an object with 2 attributes, the highlighted lines of code and the background color.
* `get_styles_list`: returns the list of available `pygments` styles.  

See the docstrings in `manim_utils.code` for more details.  


### Animations  

Utilities related to animations.  

* `LazyAnimation`: an Animation wrapper that builds the animation only when it is played. Useful when the set of mobjects to animate or the animation parameters may change dynamically between the moment the animation is built and the moment it is played.

```python

from manim import *
from manim_utils import LazyAnimation


class LazyAnimationDemo(Scene):
    def construct(self) -> None:
        grp = VGroup(Circle(color=RED), Dot(color=GREEN), Rectangle(color=BLUE))
        self.add(grp.arrange(RIGHT))

        def mob_factory():
            return VGroup([mob for mob in grp if mob.color == RED])

        anim = LazyAnimation(
            mobject_factory=mob_factory,
            animation_factory=lambda mob: ApplyMethod(mob.shift, RIGHT * 3),
        )

        # even mobjects that are changed after the animation is built will be
        # included
        grp[2].set_color(RED)
        self.play(anim, run_time=2)

```  

* `TrackedAnimationMixin`: an Mixin class for `Animation` that tracks the status of the animation: "not played", "playing" and "played".
Make sure the Mixin comes before the Animation class in the inheritance tree.


```python

from manim import *
from manim_utils import TrackedAnimationMixin


class TrackedAnimationDemo(Scene):
    def construct(self) -> None:
        c = Circle()

        # Animation classes can be used directly
        class TrackedTransform(TrackedAnimationMixin, Transform): ...

        anim = TrackedTransform(c, Rectangle(), run_time=2)

        status_text = Text("").to_edge(DOWN)
        self.add(status_text)

        def update_status(mob, dt):
            if hasattr(anim, "_status"):
                mob.become(Text(anim._status).to_edge(DOWN))

        status_text.add_updater(update_status)

        self.wait()
        self.play(anim)

        # .animate methods can be wrapped in ApplyMethod
        class TrackedApplyMethod(TrackedAnimationMixin, ApplyMethod): ...

        anim2 = TrackedApplyMethod(c.shift, RIGHT * 3)
        print(anim2._status)

        self.play(anim2)
        print(anim2._status)

```  

* `CallBackAnimation`: a wrapper allowing a function call to be performed during an animation.
Shamelessly stolen for @nikolaj on manim's discord server!


### UI  

Pre-made UI elements that can be added to scenes and customized.  

#### Buttons  

All buttons have a `transition` method that changes the state of the button to the next one in the order they are defined. It is also possible to pass a string name to transition to a specific state: `transition("PUSHED")`.
It is also possible to pass a callback parameter to a Button that will be called when a transition occurs. This callback takes 3 inputs: the button instance/the state name before the transition/the state name after the transition.

* `PushButton`: a 2-states button ("PUSHED"/"UNPUSHED") with a bevel effect

```python

from manim import *
from manim.utils.rate_functions import ease_in_back, ease_out_back

from manim_utils.ui.buttons import PushButton


class PushButtonDemo(Scene):
    def construct(self):
        d = Dot(color=GREEN)
        self.add(d)

        # the shape for the button
        base_shape = RoundedRectangle(
            corner_radius=0.3,
            width=3.0,
            height=1.5,
            fill_color=TEAL_E,
            fill_opacity=1,
            stroke_width=0,
        )

        def callback(button, state_from, state_to):
            if state_to == "PUSHED":
                d.set_color(RED)
            else:
                d.set_color(GREEN)

        button = PushButton(
            shape=base_shape,
            callback=callback,
            contents={
                "UNPUSHED": Text("Push Me"),
                "PUSHED": Text("Pushed!", fill_opacity=0.2),
            },
        )
        # customize any state value - will be updated after a transition
        button.states["UNPUSHED"]["shadow_opacity"] = 1.0
        r = BackgroundRectangle(button, fill_color=RED, buff=0.4)
        Group(r, button).to_edge(DOWN)

        self.add(r, button)
        self.wait()
        for _ in range(3):
            rate_func = ease_in_back if button.state == "UNPUSHED" else ease_out_back
            self.play(
                button.animate(rate_func=rate_func).transition(),
                run_time=0.5,
            )
            button.swap_content()
            self.wait()

```

* `HighlightButton`: a 2-states flat button ("INACTIVE"/"ACTIVE") with an highlighting effect.

* `ButtonGroup`: a VGroup of Buttons with a group level callback function. This allows to have buttons react to transition on other buttons in the same group.

```python

from manim import *
from manim.utils.rate_functions import ease_in_back, ease_out_back

from manim_utils.ui.buttons import ButtonGroup, HighlightButton, PushButton


class ButtonGroupDemo(Scene):
    def construct(self):
        # the shape for the button
        base_shape = RoundedRectangle(
            corner_radius=0.3,
            width=3.0,
            height=1.5,
            fill_color=TEAL_E,
            fill_opacity=1,
            stroke_width=0,
        )

        def callback(group, button, from_state, to_state):
            if to_state == "ACTIVE":
                for btn in group:
                    if btn is not button:
                        btn.transition("INACTIVE")

        tab1 = HighlightButton(shape=base_shape, contents=Text("Tab1"))
        tab2 = HighlightButton(shape=base_shape, contents=Text("Tab2"))
        tab3 = HighlightButton(shape=base_shape, contents=Text("Tab3"))
        tabs = ButtonGroup(tab1, tab2, tab3, callback=callback, direction=RIGHT, buff=0.4)
        self.add(tabs.shift(LEFT * 3))

        self.wait()
        tab1.transition("ACTIVE")
        self.wait()
        tab2.transition("ACTIVE")
        self.wait()
        tab3.transition("ACTIVE")
        self.wait()
        tab2.transition()
        self.wait()

```

* `ButtonDict`: a VGroup of Buttons with a group level callback function and string labels access.  


#### Cursor  

A mouse cursor with assets management and auto-fadeout functionality.

```python

from manim import *
from manim.utils.rate_functions import ease_in_out_quad

from manim_utils.ui import Cursor


class CursorDemo(Scene):
    def construct(self) -> None:
        cursor = (
            Cursor(
                idle_duration=1, fade_duration=1, rate_func=ease_in_out_quad, speed=2
            )
            .set_fill(BLACK)
            .set_stroke(WHITE)
        )
        button1 = Rectangle().to_corner(UL)
        button2 = Rectangle().to_corner(UR)

        self.add(button1, button2, cursor)
        self.wait()
        self.play(
            cursor.click(
                button1,  # target
                lambda: self.add_sound(cursor.click_sound),  # optional callback
                button1.animate.scale(0.5),  # optional animation triggered by the click
            )
        )
        # cursor does not move for more than `idle_duration` => Fades out in
        # `fade_duration` seconds
        self.wait(2)
        cursor.set_shape(
            "HAND2",
            reset_timer=False,  # True by default
        )
        self.play(cursor.click(button2))  # only target
        self.wait()
```  


### Groups  

Simple (V)Groups-related utilities.

* `GroupDict`: similar to `VDict` for Mobjects. Does not handle displaying keys.

* `IconText`: A simple Group combining an icon and a text. Handles svg and raster files to overcome the limitations of manim about svg files. Also, it resizes the raster images using Pillow directly because downsampling with manim `scale` method does not always give good results.

```python

from manim import *
from manim_utils import IconText


class IconTextDemo(Scene):
    def construct(self):
        icon_text = IconText(Circle(fill_color=RED, fill_opacity=0.2), "Hello")
        self.add(icon_text)

        custom = IconText(
            Star(), # SVG/JPG/PNG files also accepted
            "World",
            font_size=36,
            icon_height=0.8,
            text_color=YELLOW,
        )
        self.add(custom.next_to(icon_text, DOWN))

```

* `VIconText`: similar to `IconText`, but does not accept raster images as icons. Can be used in a vectorized context though, which makes it suitable as a `Button` content for instance.  

