import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html 
import numpy as np 
import pandas as pd 

app = dash.Dash(
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"  # Font Awesome link
    ]
)

# Move somewhere else later 
sidebar_content = [
    html.H2("Sidebar", className="display-4"),
    html.Hr(),
    dbc.Nav(
        [
            dbc.NavLink("Tab 1", href="#", id="tab-1-link"),
            dbc.NavLink("Tab 2", href="#", id="tab-2-link"),
            dbc.NavLink("Tab 3", href="#", id="tab-3-link"),
        ],
        vertical=True,
        pills=True,
    ),
]

sidebar = html.Div(
    sidebar_content,
    id="sidebar",
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    },
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Button(html.I(className="fas fa-bars"), id="hamburger-menu-button", outline=True, color="secondary"),
            dbc.NavbarBrand("My Dashboard", className="ms-2"),
        ]
    ),
    color="dark",
    dark=True,
    fixed="top",
)

content = html.Div(
    id="page-content",
    style={"margin-left": "18rem", "margin-top": "4rem", "padding": "2rem"},
    children=[
        html.H1("Welcome!"),
        html.P("Select a tab from the sidebar.")
    ]
)

app.layout = html.Div([
    dcc.Location(id='url'),
    sidebar,
    navbar,
    content
])


app.layout = html.Div([
    dcc.Location(id='url'),
    sidebar,
    navbar,
    content
])

@app.callback(
    [Output("sidebar", "className"),
    Output("page-content", "className"),
    Output("navbar", "style"),
    Output("sidebar", "children"),
    Output("hamburger-menu-button", "n_clicks"),
    ],
    [Input("hamburger-menu-button", "n_clicks")],
    prevent_initial_call=True)
def toggle_sidebar(n_clicks):
    if n_clicks % 2 == 1:
        # Odd clicks mean collapse
        return (
            "collapsed",
            "fullscreen",
            {"margin-left": "2rem", "transition": "padding-left 0.8s width 0.8s", "padding-left": "0rem", "display": "flex", "width": "98%"},
            [],  # Empty content
            n_clicks
        )
    else:
        # Even clicks mean expand
        return (
            "sidebar",
            "page-content",
            {"transition": "padding-left 0.8s width 0.8s", "padding-left": "22rem", "display": "flex", "width": "100%"},
            sidebar_content,  # Restore original content
            n_clicks
        )

@app.callback(
    Output("page-content", "children"),
    [Input("tabs", "value")])
def render_page_content(selected_tab):
    if selected_tab == "tab-1":
        return html.P("This is the content of Tab 1")
    elif selected_tab == "tab-2":
        return html.P("This is the content of Tab 2")
    elif selected_tab == "tab-3":
        return html.P("This is the content of Tab 3")

if __name__ == "__main__":
    app.run(port=8888, debug=True)