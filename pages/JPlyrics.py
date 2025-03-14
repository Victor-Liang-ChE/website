import re
from dash import html, dcc, callback, Output, Input, clientside_callback
import dash
from sudachipy import dictionary, tokenizer
import pykakasi

kks = pykakasi.kakasi()
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

def add_furigana_katakana(text):
    """Wrap Kanji with ruby using katakana readings (no conversion)."""
    lines = text.splitlines()
    processed_lines = []
    kanji_pattern = re.compile(r'[\u4e00-\u9faf]')
    non_kanji_pattern = re.compile(r'^(?:[\u3040-\u309F\u30A0-\u30FF]+)$')
    for line in lines:
        tokens = tokenizer_obj.tokenize(line, mode)
        result = []
        for token in tokens:
            surface = token.surface()
            reading = token.reading_form()  # Katakana reading
            if kanji_pattern.search(surface) and not non_kanji_pattern.fullmatch(surface) and surface != reading:
                result.append(f"<ruby>{surface}<rt>{reading}</rt></ruby>")
            else:
                result.append(surface)
        processed_lines.append("".join(result))
    return processed_lines

def add_furigana_romanji(text):
    """Wrap Kanji with ruby using romanji conversion."""
    lines = text.splitlines()
    processed_lines = []
    kanji_pattern = re.compile(r'[\u4e00-\u9faf]')
    non_kanji_pattern = re.compile(r'^(?:[\u3040-\u309F\u30A0-\u30FF]+)$')
    for line in lines:
        tokens = tokenizer_obj.tokenize(line, mode)
        result = []
        for token in tokens:
            surface = token.surface()
            reading_kana = token.reading_form()
            conversion = kks.convert(reading_kana)
            romanji = "".join(item['hepburn'] for item in conversion)
            if kanji_pattern.search(surface) and not non_kanji_pattern.fullmatch(surface) and surface != romanji:
                result.append(f"<ruby>{surface}<rt>{romanji}</rt></ruby>")
            else:
                result.append(surface)
        processed_lines.append("".join(result))
    return processed_lines

def add_furigana_lines(text):
    """Wrap Kanji with ruby using hiragana readings (converted from katakana)."""
    lines = text.splitlines()
    processed_lines = []
    kanji_pattern = re.compile(r'[\u4e00-\u9faf]')
    non_kanji_pattern = re.compile(r'^(?:[\u3040-\u309F\u30A0-\u30FF]+)$')
    for line in lines:
        tokens = tokenizer_obj.tokenize(line, mode)
        result = []
        for token in tokens:
            surface = token.surface()
            reading = token.reading_form()  # Katakana reading
            reading_hiragana = katakana_to_hiragana(reading)
            if kanji_pattern.search(surface) and not non_kanji_pattern.fullmatch(surface) and surface != reading_hiragana:
                result.append(f"<ruby>{surface}<rt>{reading_hiragana}</rt></ruby>")
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
                        style={'width': '100%', 'margin-bottom': '10px'}),
            # New dropdown for furigana format:
            dcc.Dropdown(
                id='furigana-format-dropdown',
                options=[
                    {'label': 'Hiragana', 'value': 'hiragana'},
                    {'label': 'Katakana', 'value': 'katakana'},
                    {'label': 'Romanji', 'value': 'romanji'}
                ],
                value='hiragana',  # default is Hiragana
                clearable=False,
                style={'width': '100%', 'margin-bottom': '10px', 'color': 'black', 'textAlign': 'center', 'justifyContent': 'center'}
            )
        ], style={'display': 'flex', 'flexDirection': 'column', 'margin-bottom': '0px'}),
        html.Div(
            id="textarea-container",
            children=[
                dcc.Textarea(
                    id="japanese-input",
                    style={'width': '98%', 'height': '450px'},
                    placeholder='Paste the lyrics here...'
                ),
                dcc.Loading(
                    id="loading-spinner",
                    type="circle",
                    children=[html.Div(id='dummy-output')],
                    style={'margin-top': '80px'}
                )
            ],
            style={'display': 'block', 'margin': '0 auto', 'padding': '0', 'textAlign': 'center'}
        )
    ],
    style={
        'position': 'absolute',
        'left': '0',
        'top': '0px',
        'width': '220px',
        'padding': '10px',
        'backgroundColor': '#08306b',
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
    dcc.Store(id='toggle-state', data={'furigana': False}),
    # Expandable Step-by-Step Thought Process Journal
    html.Div(
        children=html.Details([
            html.Summary("Journal"),
            dcc.Markdown("""
- kinda been getting bored of music lately, i gotta listen to some old songs again 
- ame to cappuccino is such a good song, she actually recommended the best songs ahhahhaha
- gonna try singing it by following the lyrics, but it sucks that i cant read most of the kanji lmao
- can i somehow enable the hirigana that sits on top of the kanji? oh i can cool
- oh its called furigana ok
- i wanna be able to toggle the furigana on and off so i can test my memory but spicetify doesnt let me toggle it on and off quickly
- ill just build my own furigana toggle thing then
- okok so i want a toggle button, probably a input box for copy and pasting the lyrics and then...
- detect the kanji? i know the kanji has multiple readings like the kanji for "one" can sound like "hito" or "ii"
- i want a dictionary that knows the context of the sentence and then give me the right kanji reading
- gonna look it up... something something tokenizer... like the tokens chatgpt uses??
- to split the sentence into words... ok
- gonna try the package MeCab i guess it looks like it has the best numbers on this tokenizer comparison chart
- nawww i know this doesnt sound right... 揺蕩 sounds like its sang: tayutau not youutouu... 
- prob something wrong with the tokenizer, gonna try another one
- ngl maybe the slowest one on that chart, sudachi, might give me more accurate results 
- like do i really care about how fast the tokenizer is? you not gonna troll me and load for a minute right?
- yea thats what i thought lmao, barely slower
- and it gave me the right reading too ok ill just stick with this then
- aight it looks like its coming together now! i should prob add more options like katakana and romanji for the furigana
- ahh sudachipy doesnt have a romanji conversion, can i hard code the romanji comversion in???
- jk lmao im gonna have to use another package for that
- pykakasi it is then...  
- awesome its working!!! i kinda want to hide the input box when im done using it tho, its so big an distracting 
- translation next??? i know the google translate is kinda ass... ill try anyway
- yea it is ass LMAO
- can i just take the translations from musixmatch? i know thats what spicetify does
- man they got a paid API that aint worth it for me
- ahh whatever ill just live without the translations ;-;
            """, style={'color': 'white', 'fontSize': '16px'})
        ]),
        style={
            'position': 'fixed',
            'bottom': '0',
            'width': '100%',
            'backgroundColor': '#08306b',
            'padding': '10px',
            'zIndex': 20
        }
    )
], style={'position': 'relative', 'height': '100vh', 'width': '100vw'})

#
# SERVER CALLBACK: Compute and cache both plain and furigana versions.
#
@callback(
    Output('lyrics-store', 'data'),
    Output('dummy-output', 'children'),
    [Input('japanese-input', 'value')]
)
def update_lyrics_store(text):
    if not text:
        return {'plain': "", 'hiragana': "", 'katakana': "", 'romanji': ""}, None
    plain_lines = merge_adjacent_duplicates(text.splitlines())
    plain_content = "<br>".join(plain_lines)
    hiragana_lines = merge_adjacent_duplicates(add_furigana_lines(text))
    hiragana_content = "<br>".join(hiragana_lines)
    katakana_lines = merge_adjacent_duplicates(add_furigana_katakana(text))
    katakana_content = "<br>".join(katakana_lines)
    romanji_lines = merge_adjacent_duplicates(add_furigana_romanji(text))
    romanji_content = "<br>".join(romanji_lines)
    return {'plain': plain_content, 'hiragana': hiragana_content, 
            'katakana': katakana_content, 'romanji': romanji_content}, None

#
# CLIENTSIDE CALLBACK: Toggle furigana display (clientside).
#
dash.get_app().clientside_callback(
    """
    function(n_clicks, cache, fmt) {
        if (!cache) { return ""; }
        // Determine whether to show furigana based on toggle button (odd clicks = show furigana)
        var showFurigana = (n_clicks % 2 === 1);
        if (showFurigana) {
            // Use the selected format from the dropdown (fmt)
            return cache[fmt] || cache.hiragana;
        } else {
            return cache.plain;
        }
    }
    """,
    Output('output-text', 'children'),
    [Input('toggle-button-jplyrics', 'n_clicks'),
     Input('lyrics-store', 'data'),
     Input('furigana-format-dropdown', 'value')]
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
