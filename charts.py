import plotly.graph_objects as go

BACKGROUND = "#0d0f14"
WHITE = "#ffffff"
BLUE = "#6495ed"
LIGHTBLUE = "#89cff0"
GREEN = "#00ff40"
RED = "#e23d28"
PURPLE = "#df73ff"

X_MIN, X_MAX = 0, 40
Y_MIN, Y_MAX = 0, 110

STARTX = 'Start X (0 -> 1 = left sideline -> right sideline)'
STARTY = 'Start Y (0 -> 1 = back of opponent endzone -> back of own endzone)'
ENDX = 'End X (0 -> 1 = left sideline -> right sideline)'
ENDY = 'End Y (0 -> 1 = back of opponent endzone -> back of own endzone)'

def createFigure(title):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        width=450,
        height=800,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(range=[0, 40], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        yaxis=dict(range=[0, 110], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        shapes=[
            dict(type="line", x0=0, x1=40, y0=20, y1=20, line=dict(width=3, color="black"), layer="below"),
            dict(type="line", x0=0, x1=40, y0=90, y1=90, line=dict(width=3, color="black"), layer="below"),
            dict(type="rect", x0=0, x1=40, y0=0, y1=110, line=dict(width=4, color="black"), layer="below"),
        ],
    )
    fig.add_trace(go.Scatter(
        x=[20, 20], y=[40, 70], mode="markers",
        marker=dict(symbol="x-thin", size=12, color="gray", line=dict(width=1, color="gray")),
        showlegend=False, hoverinfo="skip",
    ))
    return fig


def addLegend(fig, red, purple, green, lightblue, blue):
    items = [
        (red,       RED,       "red"),
        (purple,    PURPLE,    "purple"),
        (green,     GREEN,     "green"),
        (lightblue, LIGHTBLUE, "lightblue"),
        (blue,      BLUE,      "blue"),
    ]
    for name, color, group in items:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines",
            line=dict(color=color, width=3),
            name=name,
            legendgroup=group,
            showlegend=True,
        ))
    fig.update_layout()

def makeTrace(sx, sy, ex, ey, color, group):
    return go.Scatter(
        x=[sx, ex], y=[sy, ey],
        line=dict(width=2, color=color),
        mode="lines+markers",
        marker=dict(size=10, symbol="arrow-wide", angleref="previous"),
        legendgroup=group,
        showlegend=False,
    )


def genPasses(data):
    fig = createFigure("Passes")

    buckets = {"red": [], "purple": [], "green": [], "lightblue": [], "blue": []}
    colors  = {"red": RED, "purple": PURPLE, "green": GREEN, "lightblue": LIGHTBLUE, "blue": BLUE}
    short_threshold = 10

    for _, row in data.iterrows():
        sx = X_MIN + row[STARTX] * (X_MAX - X_MIN)
        sy = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
        ex = X_MIN + row[ENDX]   * (X_MAX - X_MIN)
        ey = Y_MAX + row[ENDY]   * (Y_MIN - Y_MAX)

        short_throw = row['Distance (m)'] < short_threshold or sy > ey

        if   row['Thrower error?']:  group = "red"
        elif row['Receiver error?']: group = "purple"
        elif row['Assist?']:         group = "green"
        elif short_throw:            group = "lightblue"
        else:                        group = "blue"

        buckets[group].append(makeTrace(sx, sy, ex, ey, colors[group], group))

    # intentionally rendering catches first
    for group in ("blue", "lightblue", "green", "purple", "red"):
        for trace in buckets[group]:
            fig.add_trace(trace)

    addLegend(fig, "Throwaway", "Drop", "Assist", "Short Pass", "Long Pass")
    return fig


def genReceptions(data):
    fig = createFigure("Receptions")

    buckets = {"red": [], "purple": [], "green": [], "lightblue": [], "blue": []}
    colors  = {"red": RED, "purple": PURPLE, "green": GREEN, "lightblue": LIGHTBLUE, "blue": BLUE}
    short_threshold = 10

    for _, row in data.iterrows():
        sx = X_MIN + row[STARTX] * (X_MAX - X_MIN)
        sy = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
        ex = X_MIN + row[ENDX]   * (X_MAX - X_MIN)
        ey = Y_MAX + row[ENDY]   * (Y_MIN - Y_MAX)

        short_throw = row['Distance (m)'] < short_threshold or sy > ey

        if   row['Receiver error?']: group = "purple"
        elif row['Thrower error?']:  group = "red"
        elif row['Assist?']:         group = "green"
        elif short_throw:            group = "lightblue"
        else:                        group = "blue"

        buckets[group].append(makeTrace(sx, sy, ex, ey, colors[group], group))

    # intentionally rendering catches first
    for group in ("blue", "lightblue", "green", "red", "purple"):
        for trace in buckets[group]:
            fig.add_trace(trace)

    addLegend(fig, "Drop", "Throwaway", "Goal", "Short Pass", "Long Pass")
    return fig

def getStats(data, game, player):
    return {
        "throws":       900,
        "completions":  170,
        "throwaways":   10,
        "comp_pct":     90,
        "throw_yards":  250,
        "assists":      12,
        "receptions":   180,
        "drops":        0,
        "catch_pct":    100,
        "recep_yards":  400,
        "goals":        19,
    }

def buildTitle(game, player):
    if player == "Team":
        return f"Team Stats vs. {game}" if game != "All" else "Team Stats"
    else:
        return f"{player} vs. {game}" if game != "All" else player

def getCharts(data, game, player):
    passes = data.get("Passes")

    if passes is None or passes.empty:
        print("No pass data available")
        return []

    if game != "All": 
        passes = passes[passes["Game"] == game]
        
    if player != "Team": 
        throws = passes[passes["Thrower"] == player]
        receps = passes[passes["Receiver"] == player]

    if passes.empty:
        print(f"No data available for game={game!r} player={player!r}")
        return []

    figs = []

    if player != "Team": 
        figs.append(genPasses(throws))
        figs.append(genReceptions(receps))
    else:
        figs.append(genPasses(passes))
        figs.append(genReceptions(passes))

    return buildTitle(game, player), getStats(data, game, player), figs
