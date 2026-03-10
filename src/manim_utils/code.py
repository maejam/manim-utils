import textwrap
from dataclasses import dataclass
from pathlib import Path

from manim import ManimColor
from manim.mobject.text.text_mobject import MarkupText
from pygments import highlight
from pygments.formatters.pangomarkup import PangoMarkupFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer, guess_lexer_for_filename
from pygments.styles import get_all_styles


@dataclass
class HighlightedCode:
    """Encapsulate the highlited code and the background color."""

    lines: list[MarkupText]
    bgcolor: ManimColor


def highlight_code(
    code_file: Path | str | None = None,
    code_string: str | None = None,
    language: str | None = None,
    style: str = "vim",
    tab_width: int = 4,
    font: str = "Monospace",
    font_size: int = 22,
) -> HighlightedCode:
    """Highlight a piece of code with the pygments library.

    Parameters
    ----------
    code_file
        The path to the code file to highlight.
    code_string
        Alternatively, the code string to highlight.
    language
        The programming language of the code. If not specified, it will be
        guessed from the file extension or the code itself.
    style
        The style to use for the code highlighting. Defaults to ``"vim"``.
        A list of all available styles can be obtained by calling
        :func:`.get_styles_list`.
    tab_width
        The width of a tab character in spaces. Defaults to 4.
    font
        The font to be used.
    font_size
        The size of the font to be used

    Returns
    -------
    An instance of :class:`.HighlightedCode`. This instance has 2 attributes:
    * `lines`: a list of individual code lines as :class:`manim.MarkupText` ready to be
    rendered.
    * `bgcolor`: the background color as defined by the chosen style.

    Examples
    --------
    >>> import manim as m

    >>> from manim_utils.code import highlight_code

    >>> class CodeHighlighting(m.Scene):
    ...     def construct(self):
    ...         code = highlight_code(
    ...             code_string='''
    ...         def func():
    ...             pass
    ...         ''',
    ...             language="python",
    ...             style="gruvbox-light",
    ...         )
    ...         code_group = m.VGroup(code.lines).arrange(m.DOWN, aligned_edge=m.LEFT)
    ...         self.add(
    ...             m.SurroundingRectangle(code_group).set_fill(
    ...                 code.bgcolor, opacity=1
    ...             ),
    ...             code_group,
    ...         )
    ...         print(code.bgcolor type(code.bgcolor))
    #FBF1C7 <class 'manim.utils.color.core.ManimColor'>

    """
    lexer = get_lexer_by_name(language) if language is not None else None
    if code_file is not None:
        code_file = Path(code_file)
        code_string = code_file.read_text(encoding="utf-8")
        if lexer is None:
            lexer = guess_lexer_for_filename(code_file.name, code_string)
    elif code_string is not None:
        if lexer is None:
            lexer = guess_lexer(code_string)
    else:
        raise ValueError("Either a code file or a code string must be specified.")

    formatter = PangoMarkupFormatter(style=style)
    code_string = code_string.expandtabs(tabsize=tab_width).lstrip("\n")
    code_string = textwrap.dedent(code_string)
    code_lines = code_string.splitlines()

    def prepare_line(line: str) -> MarkupText:
        line = "." + line
        highlighted = highlight(line, lexer, formatter)
        # Define a fallback color otherwise some styles are not rendered
        # properly with PangoMarkupFormatter (eg `algol`).
        wrapped = f'<span foreground="#000000">{highlighted}</span>'
        markup = MarkupText(wrapped, font=font, font_size=font_size)
        markup[0].set_opacity(0)
        return markup

    highlighted_code_lines = map(prepare_line, code_lines)
    return HighlightedCode(
        list(highlighted_code_lines), ManimColor(formatter.style.background_color)
    )


def get_styles_list() -> list[str]:
    """Return the list of available pygments styles."""
    return list(get_all_styles())
