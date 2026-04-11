# Manim Utils – A collection of lightweight manim utilities.

## Table of Contents

- [Installation](#installation)
- [Utilities](#utilities)
  - [Stencil](#stencil)
  - [code](#code)
  - [animations](#animations)

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

A set of utilities to manipulate code within your manim scenes. This is designed to be more flexible and lightweight than the manim `Code` Mobject. Can be used with [Paragraph](https://docs.manim.community/en/stable/reference/manim.mobject.text.text_mobject.Paragraph.html), [Table](https://docs.manim.community/en/stable/reference/manim.mobject.table.Table.html) or [manim-grid](https://github.com/maejam/manim-grid) for instance.

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


class LazyAnimationScene(Scene):
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


class TrackedAnimationScene(Scene):
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
