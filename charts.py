import plotly.graph_objects as go
import numpy as np
import pandas as pd

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

def heatmapFig(x, y, z, txt):
    fig = go.Figure(go.Heatmap(
        z=z,
        x=x,
        y=y,
        text=txt,
        texttemplate="%{text}",
        colorscale="Inferno",
        showscale=False,
    ))
    fig.add_shape(
        type="line",
        xref="x", yref="paper",
        x0=len(x) - 1.5,
        x1=len(x) - 1.5,
        y0=0, y1=1,
        line=dict(color="#13161f", width=3),
    )

    fig.update_layout(
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
        height=max(300, len(y) * 28 + 100),
    )

    return fig

def genPlaytimeHeatmap(stats, possessions, game):
    def parsepts(s):
        if not s or str(s).strip() == "": return []
        return [int(x) for x in str(s).strip('"').split(",") if x.strip()]

    all_games = sorted(stats["Game"].unique())
    all_players = sorted(stats["Player"].unique())
    
    stats = stats if game == "All" else stats[stats["Game"] == game]
    poss = possessions if game == "All" else possessions[possessions["Game"] == game]

    all_points = set()
    player_points = {}
    for _, row in stats.iterrows():
        pts = parsepts(row["Points played"])
        player_points[row["Player"]] = pts
        all_points.update(pts)

    player_total = { p: {} for p in all_players }
    for _, row in stats.iterrows():
        player_total[row["Player"]][row["Game"]] = int(row["Points played total"])
    
    game_total = { p: dict(games) for p, games in player_total.items() }
    player_total = { p: sum(games.values()) for p, games in player_total.items() }

    all_points = sorted(all_points)
    x_labels = [str(pt) for pt in all_points] + ["Total"]

    sorted_players = sorted(all_players, key=lambda p: player_total.get(p, 0))

    matrix = []
    text_matrix = []
    for p in sorted_players:
        played = set(player_points.get(p, []))
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

        total = player_total.get(p, 0)
        row.append(total)
        text_row.append(str(total))

        matrix.append(row)
        text_matrix.append(text_row)

    if game == "All":
        game_names = sorted(all_games)
        x_labels_all = game_names + ["Total"]
        all_matrix = []
        all_text_matrix = []
        for p in sorted_players:
            row = [game_total.get(p, {}).get(g, 0) for g in game_names]
            text_row = [str(v) if v else "" for v in row]
            total = player_total.get(p, 0)
            row.append(total)
            text_row.append(str(total))
            all_matrix.append(row)
            all_text_matrix.append(text_row)
        return heatmapFig(x_labels_all, sorted_players, all_matrix, all_text_matrix)

    return heatmapFig(x_labels, sorted_players, matrix, text_matrix)

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
    passes   = data.get("Passes")
    stats_df = data.get("Player Stats")
    possessions = data.get("Possessions")

    if game != "All":
        passes      = passes[passes["Game"] == game]
        stats_df    = stats_df[stats_df["Game"] == game]
        possessions = possessions[possessions["Game"] == game]

    if player == "Touchmaps":
        total_poss    = len(possessions)
        scored_poss   = int(possessions["Scored?"].sum())
        completed     = int((passes["Turnover?"] == 0).sum())
        throwaways    = int(passes["Thrower error?"].sum())
        drops         = int(passes["Receiver error?"].sum())
        turnovers     = throwaways + drops
        comp_pct      = round(completed / (completed + throwaways) * 100) if (completed + throwaways) else 0
        catch_pct     = round(completed / (completed + drops) * 100)      if (completed + drops)      else 0
        conv_pct      = round(scored_poss / total_poss * 100)             if total_poss               else 0
        turnover_rate = round(turnovers / total_poss, 2)                  if total_poss               else 0

        return [
            {"header": "BIG PICTURE"},
            {"label": "POSSESSION CONV %", "value": f"{conv_pct}%",      "color": "good"},
            {"label": "TURNOVER RATE",     "value": turnover_rate,        "color": "bad"},
            {"header": "OFFENSE"},
            {"label": "COMP %",        "value": f"{comp_pct}%", "color": "good"},
            {"label": "COMPLETIONS",   "value": completed,      "color": "good"},
            {"label": "THROWAWAYS",    "value": throwaways,     "color": "bad"},
            {"label": "CATCH %",       "value": f"{catch_pct}%","color": "good"},
            {"label": "CATCHES",       "value": completed,      "color": "good"},
            {"label": "DROPS",         "value": drops,          "color": "bad"},
        ]

    p = stats_df[stats_df["Player"] == player]

    def col(name):
        return 0 if p.empty else int(p[name].sum())

    def fcol(name):
        return 0.0 if p.empty else float(p[name].sum())

    # raw counting stats
    throws      = col("Throws")
    completions = throws - col("Thrower errors")
    throwaways  = col("Thrower errors")
    catches     = col("Catches")
    drops       = col("Receiver errors")
    goals       = col("Goals")
    assists     = col("Assists")
    sec_assists = col("Secondary assists")
    turnovers   = col("Turnovers")
    blocks      = col("Defensive blocks")
    o_pts       = col("Offense points played")
    d_pts       = col("Defense points played")
    o_won       = col("Offense points won")
    d_won       = col("Defense points won")
    touches     = col("Touches")
    pts_played  = col("Points played total")
    pts_touched = col("Points played with touches")
    dist_thrown = col("Total completed throw distance (m)")
    dist_caught = col("Total caught pass distance (m)")

    # derived stats
    comp_pct      = round(completions / throws * 100)          if throws                    else 0
    catch_pct     = round(catches / (catches + drops) * 100)   if (catches + drops)         else 0
    o_win_pct     = round(o_won / o_pts * 100)                 if o_pts                     else 0
    d_win_pct     = round(d_won / d_pts * 100)                 if d_pts                     else 0
    plus_minus    = (goals + assists + blocks) - turnovers + (sec_assists / 2)
    yards_per_throw = round(dist_thrown / completions)         if completions               else 0
    involvement   = round(pts_touched / pts_played * 100)      if pts_played                else 0

    player_passes = passes[passes["Thrower"] == player]
    total_throws  = len(player_passes)
    huck_pct      = round(player_passes["Huck?"].sum()  / total_throws * 100) if total_throws else 0
    dump_pct      = round(player_passes["Dump?"].sum()  / total_throws * 100) if total_throws else 0
    swing_pct     = round(player_passes["Swing?"].sum() / total_throws * 100) if total_throws else 0
    rz_assists    = int(player_passes[
        (player_passes["Assist?"] == 1) & (player_passes["Throw to endzone?"] == 1)
    ].shape[0])

    return [
        {"header": "BIG PICTURE"},
        {"label": "+/-",          "value": f"{'+' if plus_minus >= 0 else ''}{plus_minus}", "color": "good" if plus_minus >= 0 else "bad"},
        {"label": "INVOLVEMENT",  "value": f"{involvement}%", "color": "neutral"},
        {"label": "O-WIN %",      "value": f"{o_win_pct}%",   "color": "good" if o_win_pct >= 50 else "bad"},
        {"label": "D-WIN %",      "value": f"{d_win_pct}%",   "color": "good" if d_win_pct >= 50 else "bad"},

        {"header": "THROWING"},
        {"label": "COMP %",         "value": f"{comp_pct}%",    "color": "good" if comp_pct >= 80 else "bad"},
        {"label": "COMPLETIONS",    "value": completions,        "color": "good"},
        {"label": "THROWAWAYS",     "value": throwaways,         "color": "bad"},
        {"label": "ASSISTS",        "value": assists,            "color": "good"},
        {"label": "SEC. ASSISTS",   "value": sec_assists,        "color": "good"},
        {"label": "RZ ASSISTS",     "value": rz_assists,         "color": "good"},
        {"label": "YDS/THROW",      "value": f"{yards_per_throw}m", "color": "neutral"},
        {"label": "DIST. THROWN",   "value": f"{dist_thrown}m", "color": "neutral"},

        {"header": "THROWING STYLE"},
        {"label": "HUCK %",  "value": f"{huck_pct}%",  "color": "neutral"},
        {"label": "DUMP %",  "value": f"{dump_pct}%",  "color": "neutral"},
        {"label": "SWING %", "value": f"{swing_pct}%", "color": "neutral"},

        {"header": "RECEIVING"},
        {"label": "CATCH %",     "value": f"{catch_pct}%", "color": "good" if catch_pct >= 90 else "bad"},
        {"label": "CATCHES",     "value": catches,          "color": "good"},
        {"label": "DROPS",       "value": drops,            "color": "bad"},
        {"label": "GOALS",       "value": goals,            "color": "good"},
        {"label": "DIST. CAUGHT","value": f"{dist_caught}m","color": "neutral"},

        {"header": "DEFENSE & MISC"},
        {"label": "D-BLOCKS",    "value": blocks,    "color": "good"},
        {"label": "TURNOVERS",   "value": turnovers, "color": "bad"},
        {"label": "O-PTS PLAYED","value": o_pts,     "color": "neutral"},
        {"label": "D-PTS PLAYED","value": d_pts,     "color": "neutral"},
    ]

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
