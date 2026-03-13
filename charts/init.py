from .passes  import genTeamPasses, genPasses, genReceptions
from .heatmap import genPlaytimeHeatmap
from .stats   import getStats
from .utils   import buildTitle

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
        figs.extend(genTeamPasses(passes))
    elif player == "Play Time": 
        figs.append(genPlaytimeHeatmap(stats, points, game))
        return buildTitle(game, player), getStats(data, game, player), figs
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
