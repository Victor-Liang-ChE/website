from dash import html, dcc, Input, Output, callback
import dash
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

dash.register_page(__name__, path='/menu', name="Dining Menu")

def scrape_menu():
    url = 'https://apps.dining.ucsb.edu/menu/week?dc=portola&m=breakfast&m=brunch&m=lunch&m=dinner&m=late-night&food='
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    menu_section = soup.find('div', id='dinner-body')

    tbody = menu_section.find('tbody')

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
                        if idx == 0 and tr_count in [6, 10, 12]:
                            items.append({'text': text, 'highlight': True})
                        else:
                            items.append({'text': text, 'highlight': False})
                    menu_items[i].extend(items)

    return menu_items

# Get today's date and the date 4 days in the future in PST
pst = pytz.timezone('America/Los_Angeles')
today = datetime.datetime.now(pst)
future_date = today + datetime.timedelta(days=4)
date_range = f"{today.strftime('%m/%d')} to {future_date.strftime('%m/%d')}"

layout = html.Div([
    html.H1(f"Portola Dining Dinner Menu from {date_range}"),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # update every 60 seconds
        n_intervals=0
    ),
    html.Div(id='menu-output', style={'margin-top': '20px', 'font-size': '12px', 'display': 'grid', 'grid-template-columns': 'repeat(5, 1fr)', 'gap': '20px'})
])

@callback(
    Output('menu-output', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_menu(n_intervals):
    menu_items = scrape_menu()
    if isinstance(menu_items, str):  # Check if an error message was returned
        return menu_items

    # Get today's date in PST
    today = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))

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

    return menu_layout