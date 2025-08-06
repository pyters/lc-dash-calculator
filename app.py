import os
import numpy as np
import plotly.graph_objs as go
import dash
from dash import dcc, html, Input, Output

# Constants
R_load = 50  # Ohms
f_default = 2.4e9  # Default frequency
Z_real_default = 40
Z_imag_default = 13

# Web App
app = dash.Dash(__name__)
server = app.server  # Needed for Render deployment

app.layout = html.Div([
    html.H1("Matching Network Visualizer"),

    html.Div([
        html.Label("Target Real(Z):"),
        dcc.Slider(id='z-real-slider', min=10, max=100, step=1, value=Z_real_default, 
                   marks={i: str(i) for i in range(10, 110, 10)}),
        html.Br(),

        html.Label("Target Imag(Z):"),
        dcc.Slider(id='z-imag-slider', min=-50, max=50, step=1, value=Z_imag_default,
                   marks={i: str(i) for i in range(-50, 55, 10)}),
        html.Br(),

        html.Label("Frequency (GHz):"),
        dcc.Slider(id='freq-slider', min=0.1, max=6, step=0.1, value=f_default / 1e9,
                   marks={i: f"{i}" for i in range(1, 7)}),
    ], style={'padding': 20}),

    dcc.Graph(id='impedance-plot')
])

@app.callback(
    Output('impedance-plot', 'figure'),
    [Input('z-real-slider', 'value'),
     Input('z-imag-slider', 'value'),
     Input('freq-slider', 'value')]
)
def update_graph(z_real, z_imag, freq):
    f = freq * 1e9
    w = 2 * np.pi * f
    Z_target = z_real + 1j * z_imag

    L_vals = np.linspace(0.5e-9, 10e-9, 500)
    C_vals = []
    errors = []

    for L in L_vals:
        X_L = 1j * w * L
        Z_parallel = (X_L * R_load) / (R_load + X_L)
        Z_required_C = Z_target - Z_parallel
        X_C = Z_required_C.imag

        if X_C == 0:
            C = np.inf
        else:
            C = 1 / (w * abs(X_C))

        Z_total = Z_parallel + (-1j / (w * C) if X_C < 0 else 1j / (w * C))
        error = abs(Z_total - Z_target)

        C_vals.append(C * 1e12)
        errors.append(error)

    trace = go.Scatter(
        x=L_vals * 1e9,
        y=C_vals,
        mode='markers',
        marker=dict(
            color=errors,
            colorscale='Viridis',
            colorbar=dict(title='|Zin - Ztarget| (Ohm)'),
            showscale=True
        ),
        name='L vs C'
    )

    layout = go.Layout(
        xaxis={'title': 'Inductance L (nH)'},
        yaxis={'title': 'Capacitance C (pF)'},
        title=f'Matching for Z = {z_real} + j{z_imag} at {freq:.2f} GHz'
    )

    return {'data': [trace], 'layout': layout}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=True, host='0.0.0.0', port=port)
