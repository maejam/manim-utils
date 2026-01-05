# Manim Utils – A collection of lightweight manim utilities.

## Table of Contents

- [Installation](#installation)
- [Utilities](#utilities)
  - [Stencil](#stencil)

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
