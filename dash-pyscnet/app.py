from __future__ import absolute_import
from pathlib import Path
import uuid

import dash_uploader as du
import dash
import dash_table
import random
import pandas as pd
from textwrap import dedent
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
import plotly.express as px
import dash_cytoscape as cyto
import pyscnet.NetEnrich as ne
import pyscnet.Preprocessing as pp
from dash.dependencies import Input, Output, State

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = 'PySCNet Dashboard'
UPLOAD_FOLDER_ROOT = r"/home/mwu/dash-sample-apps/apps/dash-pyscnet/data/"
du.configure_upload(app, UPLOAD_FOLDER_ROOT)


def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1800,  # 1800 Mb
        filetypes=['pk'],
        upload_id=uuid.uuid1(),  # Unique session id
    )


def get_GRN_method():
    assert len(
        list(filter(lambda x: 'links' in x, list(object.NetAttrs.keys())))) != 0, "No valid link table available!"
    return list({'label': i, 'value': i} for i in list(filter(lambda x: 'links' in x, list(object.NetAttrs.keys()))))


def get_gene_rank():
    assert 'centralities' in object.NetAttrs.keys(), "No node centralities available!"
    return list({'label': i, 'value': i} for i in list(object.NetAttrs['centralities'].columns[1:]))


def get_cellinfo_column():
    assert 'CellInfo' in object.CellAttrs.keys(), 'No CellInfo available!'
    return list({'label': i, 'value': i} for i in list(object.CellAttrs['CellInfo'].columns))


def windown_sliding_corr(genes, pairwise=True):
    r_window_size = 100
    df = object.ExpMatrix.T
    # Interpolate missing data.
    df_interpolated = df.interpolate()
    # Compute rolling window synchrony
    tmp = df[genes].rolling(window=r_window_size, center=True).mean()
    if pairwise:

        rolling_r = df_interpolated[genes[0]].rolling(window=r_window_size, center=True).corr(df_interpolated[genes[1]])
        return rolling_r, tmp
    else:

        return tmp


def update_object(grn_method, top_links, resolution=0.5):
    new_object = ne.buildnet(object, key_links=grn_method, top=int(top_links))
    new_object = ne.get_centrality(new_object)
    new_object = ne.detect_community(new_object, resolution=resolution)

    return new_object


def update_filter_link(grn_method, top_links, resolution=0.5):
    object = update_object(grn_method, top_links, resolution)
    filtered_link = object.NetAttrs[grn_method].sort_values('weight', ascending=False).head(top_links)
    gene_module = object.NetAttrs['communities']

    color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
             for i in range(len(np.unique(gene_module.group)))]

    gene_module['color'] = [color[i] for i in gene_module.group]
    gene_module = pd.concat([object.NetAttrs['centralities'], gene_module[['color']].reset_index(drop=True)],
                            axis=1)
    object.NetAttrs['communities'] = gene_module
    nodes = [{'data': {'id': name, 'label': name, 'betweenness': betweenness, 'closeness': closeness,
                       'degree': degree, 'pageRank': pageRank, 'color': color}} for
             name, betweenness, closeness, degree, pageRank, color in
             list(gene_module.itertuples(index=False, name=None))]
    edges = [{'data': {'source': source, 'target': target, 'weight': weight}} for source, target, weight in
             list(filtered_link.itertuples(index=False, name=None))]

    new_elements = nodes + edges

    return new_elements


def update_sub_network(click_node=None):
    click_node = list(object.NetAttrs['graph'].node)[0] if click_node is None else click_node
    neighbours = list(object.NetAttrs['graph'].neighbors(click_node))
    gene_module = object.NetAttrs['communities']

    sub_link = pd.DataFrame({'source': np.repeat(click_node, len(neighbours)),
                             'target': neighbours})
    sub_gene_module = gene_module[gene_module.node.isin([click_node] + neighbours)][['node', 'color']]

    sub_nodes = [{'data': {'id': name, 'label': name, 'color': color}} for name, color in
                 sub_gene_module.itertuples(index=False, name=None)]
    sub_edges = [{'data': {'source': source, 'target': target}} for source, target in
                 list(sub_link.itertuples(index=False, name=None))]

    sub_element = sub_nodes + sub_edges

    color = gene_module.loc[gene_module.node == click_node, 'color'].to_list()
    sub_module = gene_module[gene_module.color == color[0]][['node', 'color']]

    inter_node = set(neighbours) & set(sub_module)
    sub_nodes_2 = [{'data': {'id': name, 'label': name, 'color': color}} for name, color in
                   sub_module.itertuples(index=False, name=None)]
    sub_edges_2 = [{'data': {'source': source, 'target': target}}
                   for source, target in
                   list(sub_link.loc[sub_link.target.isin(inter_node)].itertuples(index=False, name=None))]

    sub_element_module = sub_nodes_2 + sub_edges_2

    return [[click_node] + neighbours, sub_element, sub_element_module]


def create_page_1():
    page_1 = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4('Cell distribution'),
                html.Br(),
                dcc.Graph(id='cell_distribution'),
                dbc.Row([
                    dbc.Col([
                        html.P('color encoded by:', style={'color': 'white'}),
                        dcc.Dropdown(options=get_cellinfo_column(), id='color_code', value='Condition')
                    ]),
                    dbc.Col([
                        html.P('shape encoded by:', style={'color': 'white'}),
                        dcc.Dropdown(options=get_cellinfo_column(), id='shape_code')
                    ])
                ])
            ]),
            dbc.Col([
                html.H4('Cell percentage'),
                html.Br(),
                dcc.Graph(id='cell_percentage')
            ])
        ]),
        html.Br(),
        html.H4("Cell annotation table"),
        html.Hr(),
        dash_table.DataTable(id='table',
                             columns=[{'name': i, 'id': i} for i in object.CellAttrs['CellInfo'].columns],
                             data=object.CellAttrs['CellInfo'].to_dict('records'),
                             fixed_rows={'headers': True},
                             style_table={'overflowX': 'scroll',
                                          'overflowY': 'scroll',
                                          'width': '100%',
                                          'height': '50%',
                                          'minWidth': '100%',
                                          'maxHeight': '50ex'},
                             style_cell={'overflow': 'hidden',
                                         'maxWidth': 2,
                                         'textOverflow': 'ellipsis',
                                         'backgroundColor': '#457b9d',
                                         'color': 'white',
                                         'textAlign': 'center'},
                             style_header={'fontWeight': 'bold',
                                           'color': 'black',
                                           'backgroundColor': 'rgb(230,230,230)'},
                             sort_action='native', sort_mode='multi', filter_action='native')
    ])
    return page_1


def create_page_2():
    page_2 = html.Div([
        html.H4("Gene annotation table"),
        html.Br(),
        dash_table.DataTable(id='table',
                             columns=[{'name': i, 'id': i} for i in object.GeneAttrs['GeneInfo'].columns],
                             data=object.GeneAttrs['GeneInfo'].to_dict('rows'),
                             fixed_rows={'headers': True},
                             style_table={'overflow': 'scroll',
                                          'width': '100%',
                                          'height': '100%',
                                          'maxHeight': '80ex'},
                             style_cell={'overflow': 'hidden',
                                         'height': 'auto',
                                         'lineHeight': '15px',
                                         'backgroundColor': '#457b9d',
                                         'color': 'white',
                                         'textAlign': 'center'},
                             style_header={'fontWeight': 'bold',
                                           'color': 'black',
                                           # 'font-size': '14px',
                                           'backgroundColor': 'rgb(230,230,230)'},
                             sort_action='native', sort_mode='multi', filter_action='native'),

        html.Br(),
        html.H4('Choose two genes:'),
        dbc.Row([

            dbc.Col([
                html.P('Gene A', style={'color': 'white'}),
                dcc.Dropdown(options=list({'label': i, 'value': i} for i in list(object.GeneAttrs['GeneInfo'].index)),
                             id='gene_a', value=list(object.GeneAttrs['GeneInfo'].index)[0])
            ]),

            dbc.Col([
                html.P('Gene B', style={'color': 'white'}),
                dcc.Dropdown(options=list({'label': i, 'value': i} for i in list(object.GeneAttrs['GeneInfo'].index)),
                             id='gene_b', value=list(object.GeneAttrs['GeneInfo'].index)[1])
            ]),

            dbc.Col([
                html.P('Cells ordered by ', style={'color': 'white'}),
                dcc.Dropdown(options=get_cellinfo_column(), id='cell_order')
            ])
        ]),
        html.Br(),
        dcc.Graph(id='gene_correlation_1'),
        dcc.Graph(id='gene_correlation_2')
    ])

    return page_2


def create_page_3():
    elements = update_filter_link(grn_method=get_GRN_method()[0]['value'], top_links=50)
    neighbours, sub_element_1, sub_element_2 = update_sub_network(click_node=None)
    rolling_neighbour = windown_sliding_corr(neighbours, pairwise=False)
    gene_dynamics = px.scatter(rolling_neighbour, title='Gene expression level')
    gene_dynamics.update_layout(xaxis_title="Cell name", yaxis_title="Expression level")
    def_text = 'please click on the gene node!'

    def_stylesheet = [{
        'selector': 'node',
        'style': {'label': 'data(id)',
                  'color': 'white',
                  'background-color': '#D8B75B'}
    }]
    page_3 = html.Div([
        html.H1("Create you own gene network"),
        html.Br(),
        dbc.Row([
            dbc.Col([
                html.P('Choose GRN method', style={'color': 'white'}),
                dcc.Dropdown(id='grn_method', options=get_GRN_method(), value=get_GRN_method()[0]['value']),

                html.Br(),
                html.P('Choose top links', style={'color': 'white'}),
                dcc.RadioItems(id='top_links',
                               options=list({'label': str(i), 'value': str(i)} for i in [50, 100, 200, 500, 1000]),
                               value="50", labelStyle={'display': 'inline-block', 'margin-right': '1rem'},
                               style={'color': 'white'}),

                html.Br(),
                html.P('Choose resolution for module detection', style={'color': 'white'}),
                dcc.Slider(id='resolution', min=0, max=1, step=0.1, value=0.5,
                           marks={0: {'label': '0'},
                                  0.5: {'label': '0.5'},
                                  1: {'label': 1}}),

                html.Br(),
                html.P('Choose network layout', style={'color': 'white'}),
                dcc.Dropdown(
                    id='net_layout',
                    value='grid',
                    clearable=False,
                    options=[
                        {'label': name.capitalize(), 'value': name}
                        for name in ['grid', 'random', 'circle', 'cose', 'concentric']
                    ]
                ),

                html.Br(),
                html.P('Node size encoded by', style={'color': 'white'}),
                dcc.Dropdown(id='node_size_encode', options=get_gene_rank(), value=get_gene_rank()[0]['value'])
            ], width=3.5, style={"margin-left": "1rem"}),

            dbc.Col([
                cyto.Cytoscape(
                    id='gene_network',
                    layout={'name': 'grid'},
                    style={'width': '100%', 'height': '450px', 'background-color': 'black'},
                    stylesheet=def_stylesheet,
                    elements=elements
                )
            ])

        ]),
        html.Br(),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H5(id='node_neighbors', children=def_text, style={'color': 'white'}),
                cyto.Cytoscape(
                    id='selected_node_neighbors',
                    layout={'name': 'cose'},
                    style={'width': '90%', 'height': '350px', 'background-color': 'black'},
                    stylesheet=def_stylesheet,
                    elements=sub_element_1
                )]),
            dbc.Col([
                html.H5(id='node_module', children=def_text, style={'color': 'white'}),
                cyto.Cytoscape(
                    id='selected_node_module',
                    layout={'name': 'grid'},
                    style={'width': '90%', 'height': '350px', 'background-color': 'black'},
                    stylesheet=def_stylesheet,
                    elements=sub_element_2
                )
            ])
        ]),
        html.Br(),
        html.H5('Gene dynamics'),
        dcc.Graph(id='gene_dynamics_plot', figure=gene_dynamics, style={'height': '600px'})

    ], style={"margin-left": "1rem"})

    return page_3


SIDEBAR_STYLE = {
    "height": "100%",
    "font-size": "20px",
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "28rem",
    "padding": "2rem 1rem",
    "background-color": "#1d3557",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "28rem",
    "margin-right": "0rem",
    "padding": "2rem 1rem",
    "background-color": "#457b9d"
}
sidebar = html.Div(
    [
        html.H3("PySCNet Dashboard", className="display-4"),
        html.P("A python dashboard for pyscnet visualization.", style={'color': 'white', "font-size": "15px"}),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Introduction", href="/page-0", id="page-0-link", style={"margin-bottom": "1rem"}),
                dbc.NavLink("Cell Attributes", href="/page-1", id="page-1-link", style={"margin-bottom": "1rem"}),
                dbc.NavLink("Gene Attributes", href="/page-2", id="page-2-link", style={"margin-bottom": "1rem"}),
                dbc.NavLink("Network Attributes", href="/page-3", id="page-3-link", style={"margin-bottom": "1rem"}),
                dbc.NavLink("Contact", href="/page-4", id="page-4-link"),
                html.Hr(),
                html.Div(
                    [
                        get_upload_component(id='dash-uploader'),
                    ],
                    style={  # wrapper div style
                        'textAlign': 'center',
                        'width': '200px',
                        'padding': '10px',
                        'margin-left': '1rem',
                        'display': 'inline-block',
                        'color': 'white'
                    })
            ],
            vertical=True,
            pills=True,
        ),
    ],

    style=SIDEBAR_STYLE,
)

page_1 = html.Div(id='page_1-1', children=html.H4('please upload object!', style={'color': 'white'}))
page_2 = html.Div(id='page_2-2', children=html.H4('please upload object!', style={'color': 'white'}))
page_3 = html.Div(id='page_3-3', children=html.H4('please upload object!', style={'color': 'white'}))

content = html.Div(id="page-content", style=CONTENT_STYLE)
app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


# /Users/angelawu/Desktop/dash-pyscnet/data/pyscnet_tox_WT.pk

@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(0, 5)],
    [Input("url", "pathname")])
def toggle_active_links(pathname):
    if pathname == "/":
        return True, False, False, False, False
    return [pathname == f"/page-{i}" for i in range(0, 5)]


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/page-0"]:
        return dcc.Markdown(dedent(open('assets/Introduction.md', 'r').read()))
    elif pathname == "/page-1":
        return page_1
    elif pathname == "/page-2":
        return page_2
    elif pathname == "/page-3":
        return page_3
    elif pathname == "/page-4":
        return dcc.Markdown(dedent(open('assets/Contact.md', 'r').read()))
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


@app.callback([Output('page_1-1', 'children'),
               Output('page_2-2', 'children'),
               Output('page_3-3', 'children')],
              [Input('dash-uploader', 'isCompleted'),
               Input('dash-uploader', 'fileNames'),
               Input('dash-uploader', 'upload_id')])
def get_a_list(is_completed, filenames, upload_id):
    if is_completed and filenames is not None:
        global object
        object = pp.load_Gnetdata_object(UPLOAD_FOLDER_ROOT + '/' + str(upload_id) + '/' + filenames[0])

        new_page_1 = create_page_1()
        new_page_2 = create_page_2()
        new_page_3 = create_page_3()

        return [new_page_1, new_page_2, new_page_3]


@app.callback([Output('gene_correlation_1', 'figure'),
               Output('gene_correlation_2', 'figure')],
              [Input('gene_a', 'value'),
               Input('gene_b', 'value')])
def gene_cor_curve(gene_a, gene_b):
    rolling_1, rolling_2 = windown_sliding_corr([gene_a, gene_b], pairwise=True)
    f1 = px.scatter(rolling_1, title='Window rolling pearson correlation')
    f2 = px.scatter(rolling_2, title='Gene expression level')

    f1.update_layout(xaxis_title="Cell name",
                     yaxis_title="Pearson correlation")

    f2.update_layout(xaxis_title="Cell name",
                     yaxis_title="Expression level")

    return f1, f2


@app.callback([Output('gene_network', 'elements'),
               Output('gene_network', 'layout'),
               Output('gene_network', 'stylesheet')],
              [Input('grn_method', 'value'),
               Input('top_links', 'value'),
               Input('net_layout', 'value'),
               Input('resolution', 'value'),
               Input('node_size_encode', 'value')])
def update_gene_network(grn_method, top_links, net_layout, resolution, node_size_encode):
    new_elements = update_filter_link(grn_method=grn_method,
                                      top_links=int(top_links), resolution=resolution)
    new_layout = {'name': net_layout, 'animate': True}

    new_stylesheet = [
        {
            'selector': 'node',
            'style': {
                'label': 'data(id)',
                'background-color': 'data(color)',
                'size': 'data(' + node_size_encode + ')',
                'color': 'white'}
        }]
    return [new_elements, new_layout, new_stylesheet]


@app.callback([Output('selected_node_neighbors', 'elements'),
               Output('selected_node_module', 'elements'),
               Output('selected_node_neighbors', 'stylesheet'),
               Output('selected_node_module', 'stylesheet'),
               Output('node_neighbors', 'children'),
               Output('node_module', 'children'),
               Output('gene_dynamics_plot', 'figure')],
              [Input('gene_network', 'tapNodeData')])
def update_sub_net(data):
    if data:
        neighbours, new_sub_elements_1, new_sub_elements_2 = update_sub_network(data['id'])
        new_stylesheet_1 = [{
            'selector': 'node',
            'style': {
                'label': 'data(id)',
                'color': 'white',
                'background-color': 'data(color)'
            }
        }]

        neighbour_text = 'Genes connected to ' + data['id']
        module_text = 'Genes assigned to the same module as ' + data['id']

        rolling_neighbour = windown_sliding_corr(neighbours, pairwise=False)
        gene_dynamics = px.scatter(rolling_neighbour, title='Gene expression level')
        gene_dynamics.update_layout(xaxis_title="Cell name",
                                    yaxis_title="Expression level")

    return [new_sub_elements_1, new_sub_elements_2, new_stylesheet_1,
            new_stylesheet_1, neighbour_text, module_text, gene_dynamics]


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port='8080', debug=True,
                   dev_tools_ui=False, dev_tools_props_check=False)
