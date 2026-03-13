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

    if player == "Touchmaps" or "Play Time":
        return teamStats(passes, possessions, points, blocks_df)
    return playerStats(passes, stats_df, blocks_df, player)


def teamStats(passes, possessions, points, blocks_df):
    # --- big picture ---
    o_points  = points[points["Started on offense?"] == 1]
    d_points  = points[points["Started on offense?"] == 0]
    o_played  = len(o_points)
    d_played  = len(d_points)
    o_won     = int(o_points["Scored?"].sum())
    d_won     = int(d_points["Scored?"].sum())
    hold_pct  = round(o_won / o_played * 100) if o_played else 0
    break_pct = round(d_won / d_played * 100) if d_played else 0

    completed    = int((passes["Turnover?"] == 0).sum())
    throwaways   = int(passes["Thrower error?"].sum())
    total_throws = completed + throwaways
    comp_pct     = round(completed / total_throws * 100) if total_throws else 0

    hucks        = passes[passes["Huck?"] == 1]
    huck_comp    = int((hucks["Turnover?"] == 0).sum())
    huck_pct     = round(huck_comp / len(hucks) * 100) if len(hucks) else 0

    rz           = passes[passes["Throw to endzone?"] == 1]
    rz_comp      = int((rz["Turnover?"] == 0).sum())
    rz_pct       = round(rz_comp / len(rz) * 100) if len(rz) else 0

    o_clean_hold  = int(((o_points["Turnovers"] == 0) & (o_points["Scored?"] == 1)).sum())
    o_dirty_hold  = int(((o_points["Turnovers"]  > 0) & (o_points["Scored?"] == 1)).sum())
    o_broken      = int((o_points["Scored?"] == 0).sum())
    o_clean_pct   = round(o_clean_hold / o_played * 100) if o_played else 0
    o_dirty_pct   = round(o_dirty_hold / o_played * 100) if o_played else 0
    o_broken_pct  = round(o_broken     / o_played * 100) if o_played else 0

    d_clean_loss  = int(((d_points["Defensive blocks"] == 0) & (d_points["Scored?"] == 0)).sum())
    d_dirty_loss  = int(((d_points["Defensive blocks"]  > 0) & (d_points["Scored?"] == 0)).sum())
    d_break       = int((d_points["Scored?"] == 1).sum())
    d_clean_pct   = round(d_clean_loss / d_played * 100) if d_played else 0
    d_dirty_pct   = round(d_dirty_loss / d_played * 100) if d_played else 0
    d_break_pct   = round(d_break      / d_played * 100) if d_played else 0

    return [
        {"header": "BIG PICTURE"},
        {"label": "HOLD %",  "value": f"{hold_pct}% ({o_won}/{o_played})",  "color": "good" if hold_pct  >= 50 else "bad"},
        {"label": "BREAK %", "value": f"{break_pct}% ({d_won}/{d_played})", "color": "good" if break_pct >= 30 else "bad"},

        {"header": "OFFENSIVE EFFICIENCY"},
        {"label": "CLEAN HOLD %", "value": f"{o_clean_pct}% ({o_clean_hold}/{o_played})", "color": "good"},
        {"label": "DIRTY HOLD %", "value": f"{o_dirty_pct}% ({o_dirty_hold}/{o_played})", "color": "neutral"},
        {"label": "BROKEN %",     "value": f"{o_broken_pct}% ({o_broken}/{o_played})",    "color": "bad"},

        {"header": "DEFENSIVE EFFICIENCY"},
        {"label": "BREAK %",      "value": f"{d_break_pct}% ({d_break}/{d_played})",     "color": "good"},
        {"label": "DIRTY HOLD%", "value": f"{d_dirty_pct}% ({d_dirty_loss}/{d_played})", "color": "neutral"},
        {"label": "CLEAN HOLD%", "value": f"{d_clean_pct}% ({d_clean_loss}/{d_played})", "color": "bad"},
    ]


def playerStats(passes, stats_df, blocks_df, player):
    p = stats_df[stats_df["Player"].str.strip() == player.strip()]

    def col(name):  return 0   if p.empty else int(p[name].sum())
    def fcol(name): return 0.0 if p.empty else float(p[name].sum())

    throws       = col("Throws")
    completions  = throws - col("Thrower errors")
    throwaways   = col("Thrower errors")
    catches      = col("Catches")
    drops        = col("Receiver errors")
    goals        = col("Goals")
    assists      = col("Assists")
    sec_assists  = col("Secondary assists")
    turnovers    = col("Turnovers")
    o_pts        = col("Offense points played")
    d_pts        = col("Defense points played")
    o_won        = col("Offense points won")
    d_won        = col("Defense points won")
    pts_played   = col("Points played total")
    pts_touched  = col("Points played with touches")
    dist_thrown  = col("Total completed throw distance (m)")
    gain_thrown  = col("Total completed throw gain (m)")
    dist_caught  = col("Total caught pass distance (m)")
    avg_throw    = round(fcol("Average completed throw distance (m)"), 1)
    avg_catch    = round(fcol("Average caught pass distance (m)"), 1)
    stalls_ag    = col("Stall outs against")

    p_blocks     = blocks_df[blocks_df["Player"].str.strip() == player.strip()]
    total_blocks = len(p_blocks)

    comp_pct     = round(completions / throws * 100)          if throws            else 0
    catch_pct    = round(catches / (catches + drops) * 100)   if (catches + drops) else 0
    o_win_pct    = round(o_won / o_pts * 100)                 if o_pts             else 0
    d_win_pct    = round(d_won / d_pts * 100)                 if d_pts             else 0
    involvement  = round(pts_touched / pts_played * 100)      if pts_played        else 0
    plus_minus   = (goals + assists + total_blocks) - turnovers + (sec_assists * 0.5)
    pm_str       = f"{'+' if plus_minus >= 0 else ''}{plus_minus}"

    return [
        {"header": "BIG PICTURE"},
        {"label": "+/-",         "value": pm_str, "color": "good" if plus_minus >= 0 else "bad"},
        {"label": "GOALS",       "value": goals, "color": "good"},
        {"label": "D-BLOCKS",    "value": total_blocks, "color": "good"},
        {"label": "ASSISTS",     "value": assists, "color": "good"},
        {"label": "SEC ASSISTS", "value": sec_assists, "color": "good"},
        {"label": "THROWAWAYS",  "value": throwaways, "color": "bad"},
        {"label": "DROPS",       "value": drops, "color": "bad"},

        {"header": "IMPACT"},
        {"label": "INVOLVEMENT", "value": f"{involvement}%", "color": "good" if involvement >= 50 else "bad"},
        {"label": "O-WIN %",     "value": f"{o_win_pct}% ({o_won}/{o_pts})", "color": "good" if o_win_pct >= 50 else "bad"},
        {"label": "D-WIN %",     "value": f"{d_win_pct}% ({d_won}/{d_pts})", "color": "good" if d_win_pct >= 50 else "bad"},
        {"label": "COMP %",      "value": f"{comp_pct}% ({completions}/{throws})", "color": "good" if comp_pct >= 80 else "bad"},
        {"label": "CATCH %",     "value": f"{catch_pct}% ({catches}/{catches+drops})", "color": "good" if catch_pct >= 90 else "bad"},
    ]
