import plotly.graph_objects as go

X_MIN, X_MAX = -40, 40
Y_MIN, Y_MAX = -20, 90

STARTX = 'Start X (0 -> 1 = left sideline -> right sideline)'
STARTY = 'Start Y (0 -> 1 = back of opponent endzone -> back of own endzone)'
ENDX = 'End X (0 -> 1 = left sideline -> right sideline)'
ENDY = 'End Y (0 -> 1 = back of opponent endzone -> back of own endzone)'

def createThrowCompass(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis=dict(range=[-40, 40], showticklabels=True, showgrid=True),
        yaxis=dict(range=[-20, 90], showticklabels=True, showgrid=True),
        width=500,
        height=900
    )
    return fig

def process_file(df):
    # df = pd.read_csv(path)

    figures = []

    for thrower, group in df.groupby('Thrower'):
        fig = createThrowCompass(f"Throws - {thrower}")

        catch_traces = []
        assist_traces = []
        drop_traces = []
        throwaway_traces = []

        for _, row in group.iterrows():
            if row['Thrower error?'] == 1:
                line_color = 'red'
            elif row['Receiver error?'] == 1:
                line_color = 'purple'
            elif row['Assist?'] == 1:
                line_color = 'green'
            else:
                line_color = 'blue'

            start_x = X_MIN + row[STARTX] * (X_MAX - X_MIN)
            start_y = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
            end_x   = X_MIN + row[ENDX] * (X_MAX - X_MIN)
            end_y   = Y_MAX + row[ENDY] * (Y_MIN - Y_MAX)

            trace = go.Scatter(
                x=[start_x, end_x],
                y=[start_y, end_y],
                line=dict(width=2, color=line_color),
                mode='lines+markers',
                marker=dict(size=5, symbol="arrow-bar-up", angleref="previous"),
                showlegend=False
            )

            if row['Thrower error?'] == 1:
                throwaway_traces.append(trace)
            elif row['Receiver error?'] == 1:
                drop_traces.append(trace)
            elif row['Assist?'] == 1:
                assist_traces.append(trace)
            else:
                catch_traces.append(trace)

        for trace in catch_traces + assist_traces + drop_traces + throwaway_traces:
            fig.add_trace(trace)

        figures.append(fig)

    summary = {}

    return figures, summary
