from dash import html, dcc, Input, Output, callback
import dash
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

dash.register_page(__name__, path='/menu', name="Dining Menu")

def scrape_menu(meal="dinner"):
    # Use the same URL (it returns menu for all meals) but choose the section based on meal type.
    url = 'https://apps.dining.ucsb.edu/menu/week?dc=portola&m=breakfast&m=brunch&m=lunch&m=dinner&m=late-night&food='
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        # identify the section based on meal value, e.g., "dinner-body", "breakfast-body", "lunch-body"
        menu_section = soup.find('div', id=f'{meal}-body')
        tbody = menu_section.find('tbody')
    except AttributeError:
        return None  # Return None if the menu section or tbody is not found

    # Extract text content from each <tr> element for the next 5 days
    menu_items = [[] for _ in range(5)]
    tr_count = 0
    for tr in tbody.find_all('tr'):
        tr_count += 1
        tds = tr.find_all('td')
        for i in range(min(5, len(tds))):
            if 'text-center course-row' in tr.get('class', []):
                text_content = tds[i].get_text(separator=' ', strip=True)
                text_content = text_content.replace('(v)', '').replace('(vgn)', '').strip()
                menu_items[i].append({'text': text_content, 'class': 'course-row'})
            else:
                first_dl = tds[i].find('dl')
                if first_dl:
                    items = []
                    for idx, dd in enumerate(first_dl.find_all('dd')):
                        text = dd.text.strip().replace('(v)', '').replace('(vgn)', '').strip()
                        if meal == 'lunch':
                            # For lunch, highlight if idx==0 and tr_count in [6, 10, 12]
                            if idx == 0 and tr_count in [6, 10, 12, 14]:
                                items.append({'text': text, 'highlight': True})
                            else:
                                items.append({'text': text, 'highlight': False})
                        elif meal == 'breakfast':
                            # For breakfast, do not highlight anything
                            items.append({'text': text, 'highlight': False})
                        else:
                            # For dinner (or other meals), preserving original logic
                            if idx == 0 and tr_count in [4, 10, 12]:
                                items.append({'text': text, 'highlight': True})
                            else:
                                items.append({'text': text, 'highlight': False})
                    menu_items[i].extend(items)
    return menu_items

layout = html.Div([
    # Flex container with space-between so the title is on the left and dropdown on the right
    html.Div([
        html.H1(id='menu-title', style={'marginLeft': '20px'}),
        dcc.Dropdown(
            id='meal-dropdown',
            options=[
                {'label': 'Breakfast', 'value': 'breakfast'},
                {'label': 'Lunch', 'value': 'lunch'},
                {'label': 'Dinner', 'value': 'dinner'}
            ],
            value='dinner',  # default selection is dinner
            clearable=False,
            style={'width': '200px', 'color': 'black', 'marginRight': '20px'}  # set dropdown text to black and add right margin
        )
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '20px', 'width': '100%'}),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # update every 60 seconds
        n_intervals=0
    ),
    html.Div(id='menu-output', style={
        'margin-top': '20px',
        'font-size': '12px',
        'display': 'grid',
        'grid-template-columns': 'repeat(5, 1fr)',
        'gap': '20px'
    })
])

@callback(
    [Output('menu-output', 'children'),
     Output('menu-title', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('meal-dropdown', 'value')]
)
def update_menu(n_intervals, meal_type):
    menu_items = scrape_menu(meal_type)
    if menu_items is None:  # Check if an error message was returned
        return [html.Div("No menu this week", style={'font-size': '20px', 'color': 'red'})], "Portola Dining Menu"

    # Get today's date in PST
    pst = pytz.timezone('America/Los_Angeles')
    today = datetime.datetime.now(pst)
    future_date = today + datetime.timedelta(days=4)
    date_range = f"{today.strftime('%m/%d')} to {future_date.strftime('%m/%d')}"

    # Create the layout for the menu for the next 5 days
    menu_layout = []
    for day, items in enumerate(menu_items):
        day_title = (today + datetime.timedelta(days=day)).strftime('%A, %m/%d')
        day_layout = [html.H3(day_title)]
        for item in items:
            if isinstance(item, dict) and item.get('class') == 'course-row':
                day_layout.append(html.Li(item['text'], style={'font-size': '20px', 'list-style-type': 'none'}))
            elif isinstance(item, dict) and item.get('highlight'):
                day_layout.append(html.Li(item['text'], style={'font-weight': 'bold', 'color': 'red'}))
            else:
                day_layout.append(html.Li(item['text']))
        menu_layout.append(html.Div(day_layout))
    return menu_layout, f"Portola Dining {meal_type.capitalize()} Menu from {date_range}"