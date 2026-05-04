import textwrap
from dataclasses import dataclass
from pathlib import Path

import pygments
from manim import ManimColor
from manim.mobject.text.text_mobject import MarkupText
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
    dedent: bool = True,
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
    dedent
        Whether the code should be dedented or not. Defaults to True.

    Returns
    -------
    An instance of :class:`.HighlightedCode`. This instance has 2 attributes:
    * `lines`: a list of individual code lines as :class:`manim.MarkupText` ready to be
    rendered.
    * `bgcolor`: the background color as defined by the chosen style.

    Notes
    -----
    Tags in a string (e.g. `"<script>alert(42)</script>"`) will result in a ValueError
    raised by MarkupText ("ValueError: Unknown tag 'script' on line x char x").
    The solution is to use another lexer for that one line (e.g. javascript).

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
    if dedent:
        code_string = textwrap.dedent(code_string)

    # Process token by token to preserve multi-line tokens formatting (eg docstrings)
    highlighted = []
    current_line = ""

    for token_type, value in pygments.lex(code_string, lexer):
        if "\n" not in value:
            current_line += pygments.format([(token_type, value)], formatter)

        elif value == "\n":
            highlighted.append(current_line)
            current_line = ""

        else:
            # Multiline token
            lines = value.splitlines()

            # Prepend pending content (indentation) to the first line of the token
            if current_line:
                first_line = pygments.format([(token_type, lines[0])], formatter)
                first_line = current_line + first_line
                highlighted.append(first_line)
                current_line = ""
            else:
                highlighted.append(pygments.format([(token_type, lines[0])], formatter))

            # Append all middle lines as complete lines
            for line in lines[1:-1]:
                highlighted.append(pygments.format([(token_type, line)], formatter))

            # The last part starts the next line
            current_line += pygments.format([(token_type, lines[-1])], formatter)

    # Final flush
    if current_line.strip():
        highlighted.append(current_line)

    def prepare_line(line: str) -> MarkupText:
        # NOTE: add leading dot to preserve indentation when building the MarkupText.
        # Needs to be done after highlighting to not mess with the lexer
        dotted = "." + line
        # NOTE: Define a fallback color otherwise some styles are not rendered
        # properly with PangoMarkupFormatter (eg `algol`).
        wrapped = f'<span foreground="#000000">{dotted}</span>'
        markup = MarkupText(wrapped, font=font, font_size=font_size)
        markup[0].set_opacity(0)
        return markup

    highlighted_code_lines = map(prepare_line, highlighted)
    return HighlightedCode(
        list(highlighted_code_lines), ManimColor(formatter.style.background_color)
    )


def get_styles_list() -> list[str]:
    """Return the list of available pygments styles."""
    return list(get_all_styles())
