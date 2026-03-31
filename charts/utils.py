def buildTitle(game, player):
    if player == "Team":
        return f"Team Stats vs. {game}" if game != "All" else "Team Stats"
    else:
        return f"{player} vs. {game}" if game != "All" else player

def passesFiltered(passes, possessions, game):
    point_starts = possessions[possessions["Possession"] == 1][["Game", "Point", "Started point on offense?"]]

    merged = passes.merge(point_starts, on=["Game", "Point"], how="left")

    o_passes = merged[merged["Started point on offense?"] == 1].drop(columns=["Started point on offense?"])
    d_passes = merged[merged["Started point on offense?"] == 0].drop(columns=["Started point on offense?"])

    return o_passes, d_passes
