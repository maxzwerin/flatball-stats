import plotly.graph_objects as go
from .constants import *

def heatmapFig(x, y, z, txt):
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        text=txt, texttemplate="%{text}",
        colorscale="Inferno", showscale=False,
    ))
    fig.add_shape(
        type="line", xref="x", yref="paper",
        x0=len(x) - 1.5, x1=len(x) - 1.5, y0=0, y1=1,
        line=dict(color=BACKGROUND, width=3),
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
            row.append(total);  text_row.append(str(total))
            matrix.append(row); text_matrix.append(text_row)
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
        row.append(total);  text_row.append(str(total))
        matrix.append(row); text_matrix.append(text_row)
    return heatmapFig(x_labels, sorted_players, matrix, text_matrix)
