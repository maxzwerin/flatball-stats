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

    def col(name):  return 0   if p.empty else int(p[name].sum())
    def fcol(name): return 0.0 if p.empty else float(p[name].sum())

    # --- main counting stats ---
    goals       = col("Goals")
    assists     = col("Assists")
    sec_assists = col("Secondary assists")
    blocks      = col("Defensive blocks")
    turnovers   = col("Turnovers")

    # --- nerd: involvement ---
    pts_played  = col("Points played total")
    pts_touched = col("Points played with touches")
    involvement = round(pts_touched / pts_played * 100) if pts_played else 0

    # --- nerd: win % ---
    o_pts   = col("Offense points played")
    d_pts   = col("Defense points played")
    o_won   = col("Offense points won")
    d_won   = col("Defense points won")
    o_win_pct = round(o_won / o_pts * 100) if o_pts else 0
    d_win_pct = round(d_won / d_pts * 100) if d_pts else 0

    # --- nerd: yards ---
    throw_vert = fcol("Total completed throw gain (m)")
    catch_vert = fcol("Total caught pass gain (m)")
    throw_dist = fcol("Total completed throw distance (m)")
    catch_dist = fcol("Total caught pass distance (m)")
    total_vert = round(throw_vert + catch_vert)
    # horizontal approximated as pythagorean remainder
    throw_horiz = sum(
        abs(row["Left-to-right distance (m)"])
        for _, row in passes[passes["Thrower"] == player].iterrows()
        if row["Turnover?"] == 0
    )
    catch_horiz = sum(
        abs(row["Left-to-right distance (m)"])
        for _, row in passes[passes["Receiver"] == player].iterrows()
        if row["Turnover?"] == 0
    )
    total_horiz = round(throw_horiz + catch_horiz)

    # --- nerd: throwing/catching % ---
    throws_all  = passes[passes["Thrower"] == player]
    catches_all = passes[passes["Receiver"] == player]
    total_throws  = len(throws_all)
    total_catches = len(catches_all)
    throw_comp  = int((throws_all["Turnover?"]  == 0).sum())
    catch_comp  = int((catches_all["Turnover?"] == 0).sum())  # non-drop catches
    throw_pct   = round(throw_comp  / total_throws  * 100) if total_throws  else 0
    catch_pct   = round(catch_comp  / total_catches * 100) if total_catches else 0

    # --- nerd: completion % by category ---
    def comp_pct_str(mask):
        subset = throws_all[mask]
        total  = len(subset)
        if total == 0: return "N/A"
        comp = int((subset["Turnover?"] == 0).sum())
        return f"{round(comp / total * 100)}% ({comp}/{total})"

    # initiation = first throw of each possession
    first_throws = (
        passes.sort_values("Created")
              .groupby(["Game", "Possession"], sort=False)
              .first()
              .reset_index()
    )
    initiation_ids = set(first_throws.index)
    player_throw_idx = throws_all.index

    huck_mask     = throws_all["Huck?"]         == 1
    sideline_mask = (throws_all["From sideline?"] == 1) | (throws_all["To sideline?"] == 1)
    redzone_mask  = throws_all["Throw to endzone?"] == 1
    init_mask     = throws_all.index.isin(
        first_throws[first_throws["Thrower"] == player].index
    )
    other_mask    = ~huck_mask & ~sideline_mask & ~redzone_mask & ~init_mask

    return [
        # --- main stats ---
        {"header": "OFFENSE"},
        {"label": "GOALS",       "value": goals,       "color": "good"},
        {"label": "ASSISTS",     "value": assists,      "color": "good"},
        {"label": "SEC ASSISTS", "value": sec_assists,  "color": "good"},
        {"header": "DEFENSE"},
        {"label": "D-BLOCKS",   "value": blocks,    "color": "good"},
        {"label": "TURNOVERS",  "value": turnovers, "color": "bad"},

        # --- nerd stats (advanced=True) ---
        {"header": "EFFICIENCY", "advanced": True},
        {"label": "THROW %",     "value": f"{throw_pct}% ({throw_comp}/{total_throws})",   "color": "good" if throw_pct >= 80 else "bad",  "advanced": True},
        {"label": "CATCH %",     "value": f"{catch_pct}% ({catch_comp}/{total_catches})",  "color": "good" if catch_pct >= 90 else "bad",  "advanced": True},
        {"label": "INVOLVEMENT", "value": f"{involvement}%",                                "color": "neutral",                              "advanced": True},
        {"label": "O-WIN %",     "value": f"{o_win_pct}% ({o_won}/{o_pts})",               "color": "good" if o_win_pct >= 50 else "bad",  "advanced": True},
        {"label": "D-WIN %",     "value": f"{d_win_pct}% ({d_won}/{d_pts})",               "color": "good" if d_win_pct >= 50 else "bad",  "advanced": True},

        {"header": "YARDS", "advanced": True},
        {"label": "VERT YARDS",  "value": f"{total_vert}m",  "color": "neutral", "advanced": True},
        {"label": "HORIZ YARDS", "value": f"{total_horiz}m", "color": "neutral", "advanced": True},

        {"header": "COMPLETION BY TYPE", "advanced": True},
        {"label": "HUCK",      "value": comp_pct_str(huck_mask),     "color": "neutral", "advanced": True},
        {"label": "SIDELINE",  "value": comp_pct_str(sideline_mask), "color": "neutral", "advanced": True},
        {"label": "RED ZONE",  "value": comp_pct_str(redzone_mask),  "color": "neutral", "advanced": True},
        {"label": "INITIATION","value": comp_pct_str(init_mask),     "color": "neutral", "advanced": True},
        {"label": "OTHER",     "value": comp_pct_str(other_mask),    "color": "neutral", "advanced": True},
    ]
