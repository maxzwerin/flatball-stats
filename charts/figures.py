import plotly.graph_objects as go
from .constants import *

def createFigure(title):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        width=450, height=800,
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        xaxis=dict(range=[0, 40], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        yaxis=dict(range=[0, 110], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        shapes=[
            dict(type="line", x0=0, x1=40, y0=20,  y1=20,  line=dict(width=3, color="black"), layer="below"),
            dict(type="line", x0=0, x1=40, y0=90,  y1=90,  line=dict(width=3, color="black"), layer="below"),
            dict(type="rect", x0=0, x1=40, y0=0,   y1=110, line=dict(width=4, color="black"), layer="below"),
        ],
    )
    fig.add_trace(go.Scatter(
        x=[20, 20], y=[40, 70], mode="markers",
        marker=dict(symbol="x-thin", size=12, color="gray", line=dict(width=1, color="gray")),
        showlegend=False, hoverinfo="skip",
    ))
    return fig

def addLegend(fig, red, purple, green, lightblue, blue):
    for name, color, group in [
        (red,       RED,       "red"),
        (purple,    PURPLE,    "purple"),
        (green,     GREEN,     "green"),
        (lightblue, LIGHTBLUE, "lightblue"),
        (blue,      BLUE,      "blue"),
    ]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=color, width=3),
            name=name, legendgroup=group, showlegend=True,
        ))

def makeTrace(sx, sy, ex, ey, color, group):
    return go.Scatter(
        x=[sx, ex], y=[sy, ey],
        line=dict(width=2, color=color),
        mode="lines+markers",
        marker=dict(size=10, symbol="arrow-wide", angleref="previous"),
        legendgroup=group, showlegend=False,
    )

def heatmapFig(x, y, z, txt):
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        text=txt, texttemplate="%{text}",
        colorscale="Inferno", showscale=False,
    ))
    fig.add_shape(
        type="line", xref="x", yref="paper",
        x0=len(x) - 1.5, x1=len(x) - 1.5, y0=0, y1=1,
        line=dict(color="#13161f", width=3),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
        height=max(300, len(y) * 28 + 100),
    )
    return fig

def genPasses(data):
    fig = createFigure("Passes")
    buckets = {"red": [], "purple": [], "green": [], "lightblue": [], "blue": []}
    colors  = {"red": RED, "purple": PURPLE, "green": GREEN, "lightblue": LIGHTBLUE, "blue": BLUE}

    for _, row in data.iterrows():
        sx = X_MIN + row[STARTX] * (X_MAX - X_MIN)
        sy = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
        ex = X_MIN + row[ENDX]   * (X_MAX - X_MIN)
        ey = Y_MAX + row[ENDY]   * (Y_MIN - Y_MAX)
        short = row['Distance (m)'] < 10 or sy > ey

        if   row['Thrower error?']:  group = "red"
        elif row['Receiver error?']: group = "purple"
        elif row['Assist?']:         group = "green"
        elif short:                  group = "lightblue"
        else:                        group = "blue"
        buckets[group].append(makeTrace(sx, sy, ex, ey, colors[group], group))

    for group in ("blue", "lightblue", "green", "purple", "red"):
        for trace in buckets[group]:
            fig.add_trace(trace)

    addLegend(fig, "Throwaway", "Drop", "Assist", "Short Pass", "Long Pass")
    return fig

def genReceptions(data):
    fig = createFigure("Receptions")
    buckets = {"red": [], "purple": [], "green": [], "lightblue": [], "blue": []}
    colors  = {"red": RED, "purple": PURPLE, "green": GREEN, "lightblue": LIGHTBLUE, "blue": BLUE}

    for _, row in data.iterrows():
        sx = X_MIN + row[STARTX] * (X_MAX - X_MIN)
        sy = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
        ex = X_MIN + row[ENDX]   * (X_MAX - X_MIN)
        ey = Y_MAX + row[ENDY]   * (Y_MIN - Y_MAX)
        short = row['Distance (m)'] < 10 or sy > ey

        if   row['Receiver error?']: group = "purple"
        elif row['Thrower error?']:  group = "red"
        elif row['Assist?']:         group = "green"
        elif short:                  group = "lightblue"
        else:                        group = "blue"
        buckets[group].append(makeTrace(sx, sy, ex, ey, colors[group], group))

    for group in ("blue", "lightblue", "green", "red", "purple"):
        for trace in buckets[group]:
            fig.add_trace(trace)

    addLegend(fig, "Drop", "Throwaway", "Goal", "Short Pass", "Long Pass")
    return fig

def genPlaytimeHeatmap(stats, possessions, game):
    def parsepts(s):
        if not s or str(s).strip() == "": return []
        return [int(x) for x in str(s).strip('"').split(",") if x.strip()]

    all_games   = sorted(stats["Game"].unique())
    all_players = sorted(stats["Player"].unique())

    stats = stats if game == "All" else stats[stats["Game"] == game]

    all_points, player_points = set(), {}
    for _, row in stats.iterrows():
        pts = parsepts(row["Points played"])
        player_points[row["Player"]] = pts
        all_points.update(pts)

    player_total = {p: {} for p in all_players}
    for _, row in stats.iterrows():
        player_total[row["Player"]][row["Game"]] = int(row["Points played total"])

    game_total   = {p: dict(games) for p, games in player_total.items()}
    player_total = {p: sum(games.values()) for p, games in player_total.items()}

    all_points     = sorted(all_points)
    sorted_players = sorted(all_players, key=lambda p: player_total.get(p, 0))

    if game == "All":
        game_names = sorted(all_games)
        x_labels   = game_names + ["Total"]
        matrix, text_matrix = [], []
        for p in sorted_players:
            row      = [game_total.get(p, {}).get(g, 0) for g in game_names]
            text_row = [str(v) if v else "" for v in row]
            total    = player_total.get(p, 0)
            row.append(total);      text_row.append(str(total))
            matrix.append(row);     text_matrix.append(text_row)
        return heatmapFig(x_labels, sorted_players, matrix, text_matrix)

    x_labels = [str(pt) for pt in all_points] + ["Total"]
    matrix, text_matrix = [], []
    for p in sorted_players:
        played = set(player_points.get(p, []))
        row, text_row, count = [], [], 0
        for pt in all_points:
            if pt in played:
                count += 1
                row.append(count);  text_row.append(str(count))
            else:
                row.append(None);   text_row.append("")
        total = player_total.get(p, 0)
        row.append(total);          text_row.append(str(total))
        matrix.append(row);         text_matrix.append(text_row)
    return heatmapFig(x_labels, sorted_players, matrix, text_matrix)
