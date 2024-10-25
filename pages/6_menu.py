from dash import html, dcc, Input, Output, callback
import dash
import requests
from bs4 import BeautifulSoup

dash.register_page(__name__, path='/menu', name="Dining Menu")

def scrape_menu():
    url = 'https://apps.dining.ucsb.edu/menu/week?dc=portola&m=breakfast&m=brunch&m=lunch&m=dinner&m=late-night&food='
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    menu_section = soup.find('div', id='dinner-body')
    if not menu_section:
        print("Dinner menu not found.")
        return "Dinner menu not found."

    tbody = menu_section.find('tbody')
    if not tbody:
        print("No <tbody> found in dinner-body section.")
        return "No <tbody> found in dinner-body section."

    print(f"Extracted <tbody> content: {tbody}")

    # Extract text content from each <tr> element
    menu_items = []
    for tr in tbody.find_all('tr'):
        if 'text-center course-row' in tr.get('class', []):
            text_content = tr.get_text(separator=' ', strip=True)
            menu_items.append({'text': text_content, 'class': 'course-row'})
        else:
            first_dl = tr.find('dl')
            if first_dl:
                items = [dd.text.strip() for dd in first_dl.find_all('dd')]
                menu_items.extend(items)

    return menu_items

layout = html.Div([
    html.H1("Dining Menu"),
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # in milliseconds
        n_intervals=0
    ),
    html.Div(id='menu-output', style={'margin-top': '20px', 'font-size': '12px'})
])

@callback(
    Output('menu-output', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_menu(n_intervals):
    menu_items = scrape_menu()
    if isinstance(menu_items, str):  # Check if an error message was returned
        return menu_items

    # Create the layout for the menu
    menu_layout = []
    for item in menu_items:
        if isinstance(item, dict) and item.get('class') == 'course-row':
            menu_layout.append(html.Li(item['text'], style={'font-size': '20px', 'list-style-type': 'none'}))
        else:
            menu_layout.append(html.Li(item))

    return html.Div([
        html.H2("Today's Dinner Menu"),
        html.Ul(menu_layout)
    ])