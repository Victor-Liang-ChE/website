import re
from dash import html, dcc, callback, Output, Input, clientside_callback
import dash
from sudachipy import dictionary, tokenizer

dash.register_page(__name__, path='/jplyrics', name="Japanese Lyrics Furigana Toggle")

# Initialize tokenizer
tokenizer_obj = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.C

def katakana_to_hiragana(text):
    result = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(ch)
    return "".join(result)

def add_furigana_lines(text):
    lines = text.splitlines()
    processed_lines = []
    kanji_pattern = re.compile(r'[\u4e00-\u9faf]')
    # Pattern to match full hiragana or full katakana
    non_kanji_pattern = re.compile(r'^(?:[\u3040-\u309F\u30A0-\u30FF]+)$')
    for line in lines:
        tokens = tokenizer_obj.tokenize(line, mode)
        result = []
        for token in tokens:
            surface = token.surface()
            reading = katakana_to_hiragana(token.reading_form())
            # Only wrap with ruby if surface contains at least one Kanji,
            # is not entirely hiragana/katakana, and the reading differs.
            if kanji_pattern.search(surface) and not non_kanji_pattern.fullmatch(surface) and surface != reading:
                result.append(f"<ruby>{surface}<rt>{reading}</rt></ruby>")
            else:
                result.append(surface)
        processed_lines.append("".join(result))
    return processed_lines

def merge_adjacent_duplicates(lines):
    if not lines:
        return []
    merged = []
    count = 1
    prev_line = lines[0]
    for i in range(1, len(lines)):
        if lines[i] == prev_line:
            count += 1
        else:
            merged.append(f"{prev_line} x{count}" if count > 1 else prev_line)
            prev_line = lines[i]
            count = 1
    merged.append(f"{prev_line} x{count}" if count > 1 else prev_line)
    return merged

# The left container (with buttons and textarea) is positioned fixed on the left 
# so it won't affect the centering of the lyrics.
left_container = html.Div(
    id="left-container",
    children=[
        html.Div([
            html.Button("Hide/Show Input", id="hide-button-jplyrics", n_clicks=0,
                        style={'width': '100%', 'margin-bottom': '10px'}),
            html.Button("Toggle Furigana", id="toggle-button-jplyrics", n_clicks=0,
                        style={'width': '100%', 'margin-bottom': '10px'})
        ], style={'display': 'flex', 'flexDirection': 'column', 'margin-bottom': '20px'}),
        html.Div(
            id="textarea-container",
            children=[
                dcc.Textarea(
                    id="japanese-input",
                    style={'width': '90%', 'height': '500px'},
                    placeholder='Paste the lyrics here...'
                )
            ],
            style={'display': 'block', 'margin': '0', 'padding': '0'}
        )
    ],
    style={
        'position': 'absolute',
        'left': '0',
        'top': '0px',  # moved below the nav bar
        'width': '320px',
        'padding': '10px',
        'backgroundColor': '#010131', # new container color
        'zIndex': 10
    }
)

lyrics_container = html.Div(
    id="lyrics-container",
    children=[
        # inner container centers the markdown and allows vertical scrolling
        html.Div(
            id="lyrics-inner",
            children=[
                dcc.Markdown(
                    id="output-text",
                    dangerously_allow_html=True,
                    style={'textAlign': 'center', 'fontSize': '24px', 'width': '100%', 'lineHeight': '2.3'}
                )
            ],
            style={
                'maxWidth': '800px',
                'width': '100%',
                'margin': '0 auto',
                'padding': '20px'
            }
        )
    ],
    style={
        'position': 'absolute',
        'left': '0',
        'right': '0',
        'top': '0',
        'bottom': '0',
        'overflowY': 'auto',
        'display': 'flex',
        'justifyContent': 'center'
    }
)

layout = html.Div([
    lyrics_container,
    left_container,
    # Cache stores
    dcc.Store(id='lyrics-store'),
    dcc.Store(id='toggle-state', data={'furigana': False})
], style={'position': 'relative', 'height': '100vh', 'width': '100vw'})

#
# SERVER CALLBACK: Compute and cache both plain and furigana versions.
#
@callback(
    Output('lyrics-store', 'data'),
    [Input('japanese-input', 'value')]
)
def update_lyrics_store(text):
    if not text:
        return {'plain': "", 'furigana': ""}
    plain_lines = merge_adjacent_duplicates(text.splitlines())
    plain_content = "<br>".join(plain_lines)
    furigana_lines = merge_adjacent_duplicates(add_furigana_lines(text))
    furigana_content = "<br>".join(furigana_lines)
    return {'plain': plain_content, 'furigana': furigana_content}

#
# CLIENTSIDE CALLBACK: Toggle furigana display (clientside).
#
dash.get_app().clientside_callback(
    """
    function(n_clicks, cache) {
        if (!cache) { return ""; }
        // Toggle: if n_clicks is odd, show cached furigana; else plain.
        var showFurigana = (n_clicks % 2 === 1);
        return showFurigana ? cache.furigana : cache.plain;
    }
    """,
    Output('output-text', 'children'),
    [Input('toggle-button-jplyrics', 'n_clicks'),
     Input('lyrics-store', 'data')]
)

#
# CLIENTSIDE CALLBACK: Hide/Show the textarea (buttons remain above).
#
dash.get_app().clientside_callback(
    """
    function(n_clicks) {
        // If hide button click count is odd, hide the textarea; else show it.
        if (n_clicks % 2 === 1) {
            return {'display': 'none'};
        } else {
            return {'display': 'block', 'margin': '0', 'padding': '0'};
        }
    }
    """,
    Output('textarea-container', 'style'),
    Input('hide-button-jplyrics', 'n_clicks')
)