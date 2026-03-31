import plotly.graph_objects as go
from .constants import *

def statTable(left_title, left_rows, right_title, right_rows):
    ROW_H = 32 # very specific
    PAD = 30

    col1 = [f"<em>{r[0]}</em>" for r in left_rows]
    col2 = [r[1] for r in left_rows]
    col3 = [f"<em>{r[0]}</em>" for r in right_rows]
    col4 = [r[1] for r in right_rows]

    n = len(col1)
    total_h = n * ROW_H + PAD

    fig = go.Figure(
        go.Table(
            columnwidth=[2, 1, 2, 1],
            header=dict(
                values=[f"<b>{left_title}</b>", "", f"<b>{right_title}</b>", ""],
                fill_color=WHITE,
                align="left",
                line=dict(width=0)
            ),
            cells=dict(
                values=[col1, col2, col3, col4],
                fill_color=WHITE,
                align=["left", "right", "left", "right"],
                line=dict(width=0)
            ),
        )
    )

    fig.add_shape(
        type="line",
        x0=0, x1=1,
        y0=1 - (ROW_H / total_h), y1=1 - (ROW_H / total_h),
        line=dict(color="black", width=1),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=total_h,
    )

    return fig

def getStats(data, game, player):
    passes      = data.get("Passes")
    stats_df    = data.get("Player Stats")
    possessions = data.get("Possessions")
    points      = data.get("Points")
    blocks_df   = data.get("Defensive Blocks")

    if game != "All":
        passes      = passes[passes["Game"] == game]
        stats_df    = stats_df[stats_df["Game"] == game]
        possessions = possessions[possessions["Game"] == game]
        points      = points[points["Game"] == game]
        blocks_df   = blocks_df[blocks_df["Game"] == game]

    if player in ("Touchmaps", "Play Time", "Efficiency", "Distribution"):
        return teamStats(passes, possessions, points, blocks_df)
    return playerStats(passes, stats_df, blocks_df, player)


def teamStats(passes, possessions, points, blocks_df) -> go.Figure:
    o_points = points[points["Started on offense?"] == 1]
    d_points = points[points["Started on offense?"] == 0]
    o_played = len(o_points)
    d_played = len(d_points)
    o_won    = int(o_points["Scored?"].sum())
    d_won    = int(d_points["Scored?"].sum())
    hold_pct  = round(o_won / o_played * 100) if o_played else 0
    break_pct = round(d_won / d_played * 100) if d_played else 0

    completed    = int((passes["Turnover?"] == 0).sum())
    throwaways   = int(passes["Thrower error?"].sum())
    total_throws = completed + throwaways
    comp_pct     = round(completed / total_throws * 100) if total_throws else 0

    hucks     = passes[passes["Huck?"] == 1]
    huck_comp = int((hucks["Turnover?"] == 0).sum())
    huck_pct  = round(huck_comp / len(hucks) * 100) if len(hucks) else 0

    rz      = passes[passes["Throw to endzone?"] == 1]
    rz_comp = int((rz["Turnover?"] == 0).sum())
    rz_pct  = round(rz_comp / len(rz) * 100) if len(rz) else 0

    o_clean_hold = int(((o_points["Turnovers"] == 0) & (o_points["Scored?"] == 1)).sum())
    o_dirty_hold = int(((o_points["Turnovers"]  > 0) & (o_points["Scored?"] == 1)).sum())
    o_broken     = int((o_points["Scored?"] == 0).sum())
    o_clean_pct  = round(o_clean_hold / o_played * 100) if o_played else 0
    o_dirty_pct  = round(o_dirty_hold / o_played * 100) if o_played else 0
    o_broken_pct = round(o_broken     / o_played * 100) if o_played else 0

    d_clean_loss = int(((d_points["Defensive blocks"] == 0) & (d_points["Scored?"] == 0)).sum())
    d_dirty_loss = int(((d_points["Defensive blocks"]  > 0) & (d_points["Scored?"] == 0)).sum())
    d_break      = int((d_points["Scored?"] == 1).sum())
    d_clean_pct  = round(d_clean_loss / d_played * 100) if d_played else 0
    d_dirty_pct  = round(d_dirty_loss / d_played * 100) if d_played else 0
    d_break_pct  = round(d_break      / d_played * 100) if d_played else 0

    left_rows = [
        ("HOLD %", f"{hold_pct}%"),
        ("BREAK %", f"{break_pct}%"),
        ("COMPLETION %", f"{comp_pct}%"),
        ("HUCK %", f"{huck_pct}%"),
        ("REDZONE %", f"{rz_pct}%"),
    ]

    right_rows = [
        ("CLEAN HOLD %", f"{o_clean_pct}%"),
        ("DIRTY HOLD %", f"{o_dirty_pct}%"),
        ("BROKEN %", f"{o_broken_pct}%"),
        ("BREAK %", f"{d_break_pct}%"),
        ("CLEAN D %", f"{d_clean_pct}%"),
    ]

    return statTable("BIG PICTURE", left_rows, "EFFICIENCY", right_rows)


def playerStats(passes, stats_df, blocks_df, player) -> go.Figure:
    p = stats_df[stats_df["Player"].str.strip() == player.strip()]

    def col(name):  return 0   if p.empty else int(p[name].sum())

    throws      = col("Throws")
    completions = throws - col("Thrower errors")
    catches     = col("Catches")
    drops       = col("Receiver errors")
    goals       = col("Goals")
    assists     = col("Assists")
    sec_assists = col("Secondary assists")
    turnovers   = col("Turnovers")
    o_pts       = col("Offense points played")
    d_pts       = col("Defense points played")
    o_won       = col("Offense points won")
    d_won       = col("Defense points won")
    pts_played  = col("Points played total")
    pts_touched = col("Points played with touches")

    p_blocks     = blocks_df[blocks_df["Player"].str.strip() == player.strip()]
    total_blocks = len(p_blocks)

    comp_pct    = round(completions / throws * 100)        if throws            else 0
    catch_pct   = round(catches / (catches + drops) * 100) if (catches + drops) else 0
    o_win_pct   = round(o_won / o_pts * 100)               if o_pts             else 0
    d_win_pct   = round(d_won / d_pts * 100)               if d_pts             else 0
    involvement = round(pts_touched / pts_played * 100)    if pts_played        else 0
    plus_minus  = (goals + assists + total_blocks) - turnovers + (sec_assists * 0.5)
    pm_str      = f"{'+' if plus_minus >= 0 else ''}{plus_minus}"

    left_rows = [
        ("PLUS / MINUS", pm_str),
        ("GOALS", goals),
        ("ASSISTS", assists),
        ("D-BLOCKS", total_blocks),
        ("TURNOVERS", turnovers),
    ]

    right_rows = [
        ("INVOLVEMENT", f"{involvement}%"),
        ("O-WIN %", f"{o_win_pct}%"),
        ("D-WIN %", f"{d_win_pct}%"),
        ("COMP %", f"{comp_pct}%"),
        ("CATCH %", f"{catch_pct}%"),
    ]

    return statTable("PRODUCTION", left_rows, "EFFICIENCY", right_rows)
