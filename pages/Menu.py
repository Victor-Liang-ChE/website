from dash import html, dcc, Input, Output, callback
import dash
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

dash.register_page(__name__, path='/menu', name="Dining Menu")

def process_tbody(tbody, meal, highlight):
    """
    Process the tbody for a particular meal.
    For lunch, highlight is True when requested;
    for brunch entries (meal=='brunch') highlight will be False.
    For breakfast and dinner, the appropriate highlighting logic is applied.
    """
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
                        # Logic for lunch with highlighting
                        if meal == 'lunch' and highlight:
                            if idx == 0 and tr_count in [6, 10, 12, 14]:
                                items.append({'text': text, 'highlight': True})
                            else:
                                items.append({'text': text, 'highlight': False})
                        # Breakfast: no highlighting
                        elif meal == 'breakfast':
                            items.append({'text': text, 'highlight': False})
                        # Dinner highlighting logic
                        elif meal == 'dinner':
                            if idx == 0 and tr_count in [4, 10, 12]:
                                items.append({'text': text, 'highlight': True})
                            else:
                                items.append({'text': text, 'highlight': False})
                        else:
                            # For brunch entries, no highlighting even though processed under lunch
                            items.append({'text': text, 'highlight': False})
                    menu_items[i].extend(items)
    return menu_items

def scrape_menu(meal="dinner"):
    # Fetch the menu page (all meals are included)
    url = 'https://apps.dining.ucsb.edu/menu/week?dc=portola&m=breakfast&m=brunch&m=lunch&m=dinner&m=late-night&food='
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    if meal == 'lunch':
        # For Lunch/Brunch mode, try to get both lunch and brunch sections
        merged_menu = [[] for _ in range(5)]
        # Process lunch section (with highlighting)
        lunch_section = soup.find('div', id='lunch-body')
        if lunch_section:
            tbody_lunch = lunch_section.find('tbody')
            lunch_menu = process_tbody(tbody_lunch, meal='lunch', highlight=True)
            for i in range(5):
                merged_menu[i].extend(lunch_menu[i])
        # Process brunch section (no highlighting)
        brunch_section = soup.find('div', id='brunch-body')
        if brunch_section:
            tbody_brunch = brunch_section.find('tbody')
            brunch_menu = process_tbody(tbody_brunch, meal='brunch', highlight=False)
            for i in range(5):
                merged_menu[i].extend(brunch_menu[i])
        # If neither section is found, return None
        if not lunch_section and not brunch_section:
            return None
        return merged_menu
    else:
        # For breakfast or dinner, use the respective section
        menu_section = soup.find('div', id=f'{meal}-body')
        if not menu_section:
            return None
        tbody = menu_section.find('tbody')
        # For breakfast force no highlight; for dinner use highlighting
        if meal == 'breakfast':
            return process_tbody(tbody, meal, highlight=False)
        else:
            return process_tbody(tbody, meal, highlight=True)

layout = html.Div([
    # Flex container with space-between so the title is on the left and dropdown on the right
    html.Div([
        html.H1(id='menu-title', style={'marginLeft': '20px'}),
        dcc.Dropdown(
            id='meal-dropdown',
            options=[
                {'label': 'Breakfast', 'value': 'breakfast'},
                {'label': 'Lunch/Brunch', 'value': 'lunch'},
                {'label': 'Dinner', 'value': 'dinner'}
            ],
            value='dinner',  # default selection is dinner
            clearable=False,
            style={'width': '200px', 'color': 'black', 'marginRight': '20px'}
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
    if menu_items is None:
        return [html.Div("No menu this week", style={'font-size': '20px', 'color': 'red'})], "Portola Dining Menu"

    pst = pytz.timezone('America/Los_Angeles')
    today = datetime.datetime.now(pst)
    future_date = today + datetime.timedelta(days=4)
    date_range = f"{today.strftime('%m/%d')} to {future_date.strftime('%m/%d')}"

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