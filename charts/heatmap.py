import plotly.graph_objects as go
from .constants import *

def heatmapFig(x, y, z, txt):
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        text=txt, texttemplate="%{text}",
        colorscale="Inferno", showscale=False,
    ))
    shapes = [
        dict(
            type="line", xref="x", yref="paper",
            x0=i - 0.5, x1=i - 0.5, y0=0, y1=1,
            line=dict(color=LIGHTGRAY, width=0.5),
        )
        for i in range(1, len(x))
    ]
    shapes += [
        dict(
            type="line", xref="paper", yref="y",
            x0=0, x1=1,
            y0=i - 0.5, y1=i - 0.5,
            line=dict(color=LIGHTGRAY, width=0.5),
        )
        for i in range(1, len(y))
    ]
    shapes += [
        dict(
            type="line", xref="x", yref="paper",
            x0=len(x) - 1.5, x1=len(x) - 1.5, y0=0, y1=1,
            line=dict(color=BACKGROUND, width=3),
        )
    ]
    fig.update_layout(
        shapes=shapes,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(
            showgrid=False, tickangle=-30,
            showline=True, linecolor=BACKGROUND, linewidth=2,
            mirror=True, ticks="outside", tickcolor=BACKGROUND,
        ),
        yaxis=dict(
            showgrid=False,
            showline=True, linecolor=BACKGROUND, linewidth=2,
            mirror=True, ticks="outside", tickcolor=BACKGROUND,
        ),
        height=max(300, len(y) * 28 + 100),
    )
    return fig

def buildPointLabels(possessions, game):
    poss = possessions[possessions["Game"] == game].copy()
    poss["Started on offense?"] = poss["Started on offense?"].fillna(0).astype(int)
    poss["Scored?"]             = poss["Scored?"].fillna(0).astype(int)

    known = (
        poss.groupby("Point")
            .agg(
                offense=("Started on offense?", "first"),
                scored= ("Scored?", "max"),
            )
            .sort_index()
            .reset_index()
    )

    # build a full point range including points we never had possession
    all_point_nums = list(range(1, int(poss["Point"].max()) + 1))
    known_dict     = {int(row["Point"]): row for _, row in known.iterrows()}

    # reconstruct all points, inferring missing ones
    full_points = []
    last_scored = None

    for pt_num in all_point_nums:
        if pt_num in known_dict:
            row = known_dict[pt_num]
            on_offense = int(row["offense"]) == 1
            scored = int(row["scored"])  == 1
        else:
            if last_scored is True: on_offense = False
            elif last_scored is False: on_offense = True
            else: on_offense = False  # fallback for first point
            scored = False

        full_points.append((pt_num, on_offense, scored))
        last_scored = scored

    # build labels
    labels    = []
    our_score = 0
    opp_score = 0

    for pt_num, on_offense, scored in full_points:
        if scored: our_score += 1
        else:      opp_score += 1

        prefix = "O" if on_offense else "D"
        score  = f"{our_score}-{opp_score}"

        if   not on_offense and scored:  suffix = " BREAK"
        elif on_offense and not scored:  suffix = " BROKEN"
        else:                            suffix = ""

        labels.append(f"{prefix}: {score}{suffix}")

    return labels[:-1]

def perGameHeatmap(stats, possessions, game, sorted_players):
    def parsepts(s):
        if not s or str(s).strip() == "": return []
        return [int(x) for x in str(s).strip('"').split(",") if x.strip()]

    stats_game = stats[stats["Game"] == game]
    poss_game = possessions[possessions["Game"] == game]
    poss_game = poss_game[:-1]

    # authoritative point list from possessions, not from player stats
    all_points = list(range(1, int(poss_game["Point"].max()) + 1))

    player_points = {}
    for _, row in stats_game.iterrows():
        player_points[row["Player"]] = set(parsepts(row["Points played"]))

    point_labels = buildPointLabels(possessions, game)
    x_labels = point_labels + [f"Total ({len(all_points)})"]

    matrix, text_matrix = [], []
    for p in sorted_players:
        played = player_points.get(p, set())
        row, text_row, count = [], [], 0
        for pt in all_points:
            if pt in played:
                count += 1
                row.append(count)
                text_row.append(str(count))
            else:
                row.append(None)
                text_row.append("")

        row.append(count)
        text_row.append(str(count))
        matrix.append(row)
        text_matrix.append(text_row)

    return heatmapFig(x_labels, sorted_players, matrix, text_matrix)

def allGamesHeatmap(all_games, all_players, player_total, game_total, sorted_players):
    game_names = sorted(all_games)
    x_labels = game_names + ["Total"]

    # per-game max for normalization
    game_max = {
        g: max((game_total.get(p, {}).get(g, 0) for p in all_players), default=1) or 1
        for g in game_names
    }
    total_max = max(player_total.values(), default=1) or 1

    matrix, text_matrix = [], []
    for p in sorted_players:
        norm_row = [
            game_total.get(p, {}).get(g, 0) / game_max[g]
            for g in game_names
        ]
        text_row = [
            str(game_total.get(p, {}).get(g, 0)) or ""
            for g in game_names
        ]

        total = player_total.get(p, 0)
        norm_row.append(total / total_max)
        text_row.append(str(total))

        matrix.append(norm_row)
        text_matrix.append(text_row)

    return heatmapFig(x_labels, sorted_players, matrix, text_matrix)


def genPlaytimeHeatmap(stats, possessions, game):
    all_games   = sorted(stats["Game"].unique())
    all_players = sorted(stats["Player"].unique())

    player_total_by_game = {p: {} for p in all_players}
    for _, row in stats.iterrows():
        player_total_by_game[row["Player"]][row["Game"]] = int(row["Points played total"])

    game_total   = {p: dict(g) for p, g in player_total_by_game.items()}
    player_total = {p: sum(g.values()) for p, g in player_total_by_game.items()}

    sorted_players = sorted(all_players, key=lambda p: player_total.get(p, 0))

    if game == "All":
        return allGamesHeatmap(
            all_games, all_players,
            player_total, game_total, sorted_players,
        )

    return perGameHeatmap(stats, possessions, game, sorted_players)
