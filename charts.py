import plotly.graph_objects as go
import numpy as np

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

def genPlaytimeHeatmap(stats, possessions, game):
    def parsepts(s):
        """Parse '2,3,5,6,...' or '"2,3,5,6,..."' into a list of ints."""
        return [int(x.strip()) for x in str(s).strip('"').split(",") if x.strip().isdigit()]

    if game == "All":
        all_games = sorted(stats["Game"].unique())
        all_players = sorted(stats["Player"].unique())

        # Build player -> {game -> points_played_total}
        player_game = {p: {} for p in all_players}
        for _, row in stats.iterrows():
            player_game[row["Player"]][row["Game"]] = int(row["Points played total"])

        matrix, text_matrix, totals = [], [], []
        for p in all_players:
            row, text_row = [], []
            total = 0
            for g in all_games:
                val = player_game[p].get(g, 0)
                total += val
                row.append(val if val > 0 else None)
                text_row.append(str(val) if val > 0 else "")
            row.append(total)
            text_row.append(str(total))
            matrix.append(row)
            text_matrix.append(text_row)
            totals.append(total)

        # Sort by total ascending
        order = sorted(range(len(all_players)), key=lambda i: totals[i])
        all_players = [all_players[i] for i in order]
        matrix      = [matrix[i] for i in order]
        text_matrix = [text_matrix[i] for i in order]
        totals      = [totals[i] for i in order]

        x_labels = list(all_games) + ["TOTAL"]

        num_games = len(all_games)

# Normalize each game column by its column max
        norm_matrix = []
        for row in matrix:
            norm_matrix.append(list(row))  # copy

        for col_i in range(num_games):
            col_vals = [matrix[row_i][col_i] for row_i in range(len(all_players)) if matrix[row_i][col_i] is not None]
            col_max = max(col_vals) if col_vals else 1
            for row_i in range(len(all_players)):
                val = norm_matrix[row_i][col_i]
                if val is not None:
                    norm_matrix[row_i][col_i] = val / col_max

# Normalize TOTAL column separately
        total_max = max(totals) if totals else 1
        for row_i in range(len(all_players)):
            norm_matrix[row_i][-1] = totals[row_i] / total_max

        fig = go.Figure(go.Heatmap(
            z=norm_matrix,          # normalized for color
            x=x_labels,
            y=all_players,
            text=text_matrix,       # raw numbers shown
            texttemplate="%{text}",
            colorscale="Inferno",
            showscale=False,
            zmin=0,
            zmax=1,
        ))
        fig.add_shape(
            type="line",
            xref="x", yref="paper",
            x0=len(all_games) - 0.5,
            x1=len(all_games) - 0.5,
            y0=0, y1=1,
            line=dict(color="#13161f", width=3),
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, ticks="outside", ticklen=5, tickcolor="#555d7a"),
            yaxis=dict(showgrid=False, ticks="outside", ticklen=5, tickcolor="#555d7a"),
            height=max(300, len(all_players) * 28 + 100),
        )

    else:
        stats = stats[stats["Game"] == game]
        poss = possessions[possessions["Game"] == game]

        our_score = 0
        their_score = 0

        x_labels = []
        for _, row in poss.iterrows():
            offense = bool(row["Started point on offense?"])
            scored = bool(row["Scored?"])
            is_break = (not offense and scored) or (offense and not scored)
            if scored: our_score += 1
            else: their_score += 1
            prefix = "O" if offense else "D"
            label = f"{prefix}: {our_score} - {their_score}"
            if is_break: label += " BREAK"
            x_labels.append(label)

        all_points = set()
        player_points = {}
        for _, row in stats.iterrows():
            pts = parsepts(row["Points played"])
            player_points[row["Player"]] = pts
            all_points.update(pts)

        all_points = sorted(all_points)
        players_sorted = sorted(player_points.keys(), key=lambda p: len(player_points[p]))

        matrix = []
        text_matrix = []
        totals = []

        for p in players_sorted:
            played = set(player_points[p])
            row = []
            text_row = []
            count = 0
            for pt in all_points:
                if pt in played:
                    count += 1
                    row.append(count)
                    text_row.append(str(count))
                else:
                    row.append(None)
                    text_row.append("")

            total = count
            row.append(total)
            text_row.append(str(total))
            matrix.append(row)
            text_matrix.append(text_row)
            totals.append(total)

        x_labels = x_labels[:len(all_points)] # need to trim
        x_labels += ["TOTAL"]

        fig = go.Figure(go.Heatmap(
            z=matrix,
            x=x_labels,
            y=players_sorted,
            text=text_matrix,
            texttemplate="%{text}",
            colorscale="Inferno",
            showscale=False,
            zmin=0,
            zmax=max(totals) if totals else 1,
        ))
        fig.add_shape(
            type="line",
            xref="x", yref="paper",
            x0=len(all_points) - 0.5,
            x1=len(all_points) - 0.5,
            y0=0, y1=1,
            line=dict(color="#13161f", width=3),
        )

        fig.update_layout(
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
            height=max(300, len(stats["Player"].unique()) * 28 + 100),
        )
    return fig

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
    figs = []

    blocks = data.get("Defensive Blocks")
    passes = data.get("Passes")
    stats = data.get("Player Stats")
    points = data.get("Points")
    possessions = data.get("Possessions")
    stalls = data.get("Stall Outs Against")


    if game != "All": 
        passes = passes[passes["Game"] == game]
        
    if player == "Touchmaps": 
        figs.append(genPasses(passes))
        figs.append(genReceptions(passes))
        # TODO:
        # midfield hucks, sideline hucks, sideline short passes,
        # redzone passes, other passes, + normalized variations
    elif player == "Play Time": 
        figs.append(genPlaytimeHeatmap(stats, possessions ,game))
        return buildTitle(game, player), None, figs
    elif player == "Efficiency":
        return buildTitle(game, player), None, figs
    elif player == "Distribution":
        return buildTitle(game, player), None, figs
    else:
        throws = passes[passes["Thrower"] == player]
        receps = passes[passes["Receiver"] == player]

        figs.append(genPasses(throws))
        figs.append(genReceptions(receps))

    return buildTitle(game, player), getStats(data, game, player), figs
