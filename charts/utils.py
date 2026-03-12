def buildTitle(game, player):
    if player == "Team":
        return f"Team Stats vs. {game}" if game != "All" else "Team Stats"
    else:
        return f"{player} vs. {game}" if game != "All" else player
