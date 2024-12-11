import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px


df = pd.read_excel('rend_2016a2022_V2.xlsx',index_col=0)

#No queremos lo que este desde el 2020 debido a las situaciones extraordinarias
df = df.query('Anho<2020')

df.loc[df['Semestre']==13,'Semestre']= 11

# Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    # Dropdowns for Graph 1 and Graph 2
    html.Div([
        html.Div([
                html.Label('Oportunidad de examen final'),
                dcc.Dropdown(
                            id='final-selector1',
                            options=[{'label': f'{i}° Final', 'value': f'Nota.{i}F'} for i in range(1, 4)],
                            value='Nota.1F'
                            )
                ], style={'width': '24%', 'display': 'inline-block'}),
        html.Div([
                html.Label('Agrupación'),
                dcc.Dropdown(
                            id='x-axis-selector',
                            options=[{'label': col, 'value': col} for col in ['Semestre', 'Anho']],
                            value='Semestre'
                            )
                ], style={'width': '24%', 'display': 'inline-block'}),
        html.Div([
                html.Label('Carrera'),
                dcc.Dropdown(
                            id='carrera-selector1',
                            options=[{'label': c, 'value': c} for c in df['Carrera'].dropna().unique()],
                            value=df['Carrera'].unique()[0]
                            )
                ], style={'width': '24%', 'display': 'inline-block'}),
        html.Div([
                html.Label('Semestre'),
                dcc.Dropdown(
                            id='semestre-selector',
                            options=[{'label': s, 'value': s} for s in df['Semestre'].sort_values().unique()],
                            value=df['Semestre'].sort_values().unique()[0]
                            )
                ], style={'width': '24%', 'display': 'inline-block'}),
            ]),
    

    # Graphs 1 and 2
    html.Div([
        dcc.Graph(id='graph-1', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id='graph-2', style={'width': '48%', 'display': 'inline-block'}),
    ]),

    # Dropdowns for Graphs 3 and 4
    html.Div([
        html.Div([
                html.Label('Oportunidad de examen final'),
                dcc.Dropdown(
                            id='final-selector2',
                            options=[{'label': f'{i}° Final', 'value': f'Nota.{i}F'} for i in range(1, 4)],
                            value='Nota.1F'
                            )
                ], style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
                html.Label('Carrera'),
                dcc.Dropdown(
                            id='carrera-selector2',
                            options=[{'label': c, 'value': c} for c in df['Carrera'].dropna().unique()],
                            value=df['Carrera'].unique()[0]
                            )
                ], style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
                html.Label('Año'),
                dcc.Slider (
                            df['Anho'].min(),
                            df['Anho'].max(),
                            step= None,
                            value= df['Anho'].min(),
                            marks= {str(a): str(a) for a in df['Anho'].unique()},
                            id='anho-selector',
                            )
                ], style={'width': '58%', 'display': 'inline-block'}),
            ]),

    # Graphs 3 and 4
    html.Div([
        dcc.Graph(id='graph-3', style={'width': '100%'}),
        dcc.Graph(id='graph-4', style={'width': '100%'}),
    ]),

])

# Callbacks for interactivity with figures 1 and 2
@app.callback(
    Output('graph-1', 'figure'),
    Output('graph-2', 'figure'),
    Input('final-selector1', 'value'),
    Input('x-axis-selector', 'value'),
    Input('carrera-selector1','value'),
    Input('semestre-selector','value')
)
def update_graphs_1_and_2(s_final, s_x, s_car, s_sem):
    # Graph 1: Mean values by Carrera and x-axis
    df_mean = df.groupby([s_x,'Carrera'])[s_final].mean().reset_index()
    fig1 = px.line(df_mean, x= s_x, y= s_final, color='Carrera', 
                   title= f'Promedio de notas en el {s_final[-2]}° final\n\n por {s_x} de cada carrera')

    # Graph 2: Pie chart for selected Nota distribution
    filtered_df = df[(df['Carrera'] == s_car) & (df['Semestre'] == s_sem)]
    order: dict[str, list[str]] = {s_final:[1,2,3,4,5]}
    fig2 = px.pie(filtered_df[s_final].dropna(),
                  names=s_final,
                  category_orders= order,
                  title=f'Distribucion de nota en el {s_final[-2]}° final del {s_sem}° semestre  de la carrera {s_car}') 
    return fig1, fig2

# Callbacks for interactivity with figures 3 and 4
@app.callback(
    Output('graph-3', 'figure'),
    Output('graph-4', 'figure'),
    Input('final-selector2', 'value'),
    Input('carrera-selector2', 'value'),
    Input('anho-selector', 'value'),
)


def update_graphs_3_and_4(s_final, s_car, s_a):
    # Filter DataFrame for the selected Carrera and Año
    filtered_df = df[(df['Carrera'] == s_car) & (df['Anho'] == s_a)]
    filtered_df['Ciclo'] = filtered_df['Semestre'].apply(lambda x: 'CB' if x < 5 else 'CP')
    # Top 10 subjects with highest mean values for the selected final exam
    top_subjects = (filtered_df.groupby('Asignatura')[s_final]
                    .mean().nlargest(10).reset_index())
    
    # Graph 3: Box plot for top 10 subjects
    fig3 = px.box(filtered_df[filtered_df['Asignatura'].isin(top_subjects['Asignatura'])],
                  x='Asignatura', y=s_final,
                  color='Ciclo', color_discrete_map={'CB': 'red', 'CP': 'blue'}
                  )
    fig3.update_layout(title='Top 10 Materias con Mayor Rendimiento',
                       legend_title= "Ciclo profecional (CP) o básico (CB)",
                       legend=dict(itemsizing='constant', )
                       )
    fig3.update_xaxes(tickangle=-45)
    # Bottom 10 subjects with lowest mean values for the selected final exam
    bottom_subjects = (filtered_df.groupby('Asignatura')[s_final]
                       .mean().nsmallest(10).reset_index()
                       )
    # Graph 4: Box plot for bottom 10 subjects
    fig4 = px.box(filtered_df[filtered_df['Asignatura'].isin(bottom_subjects['Asignatura'])],
                  x='Asignatura', y=s_final,
                  color='Ciclo', color_discrete_map={'CB': 'red', 'CP': 'blue'}
                  )
    fig4.update_layout(title='Top 10 Materias con Peor Rendimiento',
                       legend_title= "Ciclo profecional (CP) o básico (CB)",
                       legend=dict(itemsizing='constant', )
                       )
    fig4.update_xaxes(tickangle=-45)
    return fig3, fig4

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8080)
