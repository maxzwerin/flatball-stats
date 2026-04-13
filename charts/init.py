from .passes       import *
from .heatmap      import genPlaytimeHeatmap
from .stats        import getStats
from .utils        import buildTitle, passesFiltered
from .distribution import genDistribution

def getCharts(data, game, player):
    figs = []
    blocks = data.get("Defensive Blocks")
    passes = data.get("Passes")
    stats = data.get("Player Stats")
    points = data.get("Points")
    possessions = data.get("Possessions")
    stalls = data.get("Stall Outs Against")

    o_passes, d_passes = passesFiltered(passes, possessions, game)

    if game != "All": 
        possessions = possessions[possessions["Game"] == game]
        passes = passes[passes["Game"] == game]

    if player == "Touchmaps": 
        figs.append(getStats(data, game, player))
        figs.append(genTeamPasses(passes, "All Passes"))
        figs.append(genTeamPasses(o_passes, "O Passes"))
        figs.append(genTeamPasses(d_passes, "D Passes"))

        return buildTitle(game, player), figs

    elif player == "Play Time": 
        figs.append(getStats(data, game, player))
        figs.append(genPlaytimeHeatmap(stats, points, game))
        return buildTitle(game, player), figs

    elif player == "Efficiency":
        return buildTitle(game, player), figs

    elif player == "Distribution":
        figs.append(getStats(data, game, player))
        figs.append(genDistribution(passes, "All Passes"))
        figs.append(genDistribution(o_passes, "O Passes"))
        figs.append(genDistribution(d_passes, "D Passes"))
        return buildTitle(game, player), figs

    else:
        throws = passes[passes["Thrower"] == player]
        receps = passes[passes["Receiver"] == player]

        figs.append(getStats(data, game, player))
        figs.append(genPassesAndReceptions(throws, receps))
        # figs.append(genPasses(throws))
        # figs.append(genReceptions(receps))

    return buildTitle(game, player), figs
