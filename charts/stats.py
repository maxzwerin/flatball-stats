def getStats(data, game, player):
    passes   = data.get("Passes")
    stats_df = data.get("Player Stats")
    possessions = data.get("Possessions")

    if game != "All":
        passes      = passes[passes["Game"] == game]
        stats_df    = stats_df[stats_df["Game"] == game]
        possessions = possessions[possessions["Game"] == game]

    if player == "Touchmaps":
        return teamStats(passes, possessions)
    return playerStats(passes, stats_df, player)

def teamStats(passes, possessions):
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

def playerStats(passes, stats_df, player):
    p = stats_df[stats_df["Player"] == player]

    def col(name): return 0 if p.empty else int(p[name].sum())
    def fcol(name): return 0.0 if p.empty else float(p[name].sum())

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
