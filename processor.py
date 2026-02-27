import io
import re
import pandas as pd
from urllib.parse import quote as url_quote

EXPECTED_FILE_TYPES = [
    "Defensive Blocks",
    "Passes",
    "Player Stats",
    "Points",
    "Possessions",
    "Stall Outs Against",
]

PLAYER_COLS: dict[str, str] = {
    "Defensive Blocks":   "Player",
    "Player Stats":       "Player",
    "Stall Outs Against": "Player",
}

FILENAME_RE = re.compile(
    r"^(Defensive Blocks|Passes|Player Stats|Points|Possessions|Stall Outs Against)"
    r" vs\. (.+?) (\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})(\.csv)?$",
    re.IGNORECASE,
)

def parseFname(filename: str):
    m = FILENAME_RE.match(filename.strip())
    if not m:
        return None

    raw_type = m.group(1)

    canonical = next(
        (t for t in EXPECTED_FILE_TYPES if t.lower() == raw_type.lower()),
        raw_type,
    )

    opponent = m.group(2).strip()
    timestamp = m.group(3)

    return canonical, opponent, timestamp

def processUploads(file_list: list[tuple[str, bytes]]):

    combined: dict[str, list[pd.DataFrame]] = {
        t: [] for t in EXPECTED_FILE_TYPES
    }

    warnings: list[str] = []
    games_seen: dict[str, set[str]] = {}

    for filename, content in file_list:

        parsed = parseFname(filename)
        if not parsed:
            warnings.append(f"Bad filename: '{filename}' -- skipped.")
            continue

        file_type, opponent, _ = parsed

        try:
            df = pd.read_csv(io.BytesIO(content))
        except Exception as exc:
            warnings.append(f"Failed to read '{filename}': {exc}")
            continue

        df.insert(0, "Game", opponent)

        combined[file_type].append(df)
        games_seen.setdefault(opponent, set()).add(file_type)

    for game, present in sorted(games_seen.items()):
        missing = [t for t in EXPECTED_FILE_TYPES if t not in present]
        if missing:
            warnings.append(
                f"Game vs. {game} MISSING: {', '.join(missing)}"
            )

    data: dict[str, pd.DataFrame] = {}

    for file_type, dfs in combined.items():
        if dfs:
            data[file_type] = pd.concat(dfs, ignore_index=True)
        else:
            data[file_type] = pd.DataFrame()

    return data, warnings

def getGameList(data: dict):
    games: set[str] = set()

    for df in data.values():
        if "Game" in df.columns:
            games.update(df["Game"].dropna().astype(str))

    return sorted(games)


def getPlayerList(data: dict):

    if "Player Stats" not in data:
        return []

    df = data["Player Stats"]

    if "Player" not in df.columns:
        return []

    players = df["Player"].dropna().astype(str).unique()

    return sorted(players)

def getPlayerStats(data: dict, game: str = "All", player: str = "Team"):

    df = data.get("Player Stats", pd.DataFrame()).copy()
    if df.empty:
        return df

    if game != "All":
        df = df[df["Game"].astype(str) == game]

    if player != "Team":
        df = df[df["Player"].astype(str) == player]

    return df.reset_index(drop=True)

def getFileData(data: dict, file_type: str,
                game: str = "All",
                player: str = "Team"):

    df = data.get(file_type, pd.DataFrame()).copy()
    if df.empty:
        return df

    # filter by game
    if game != "All":
        df = df[df["Game"].astype(str) == game]

    # filter by player
    if player != "Team":

        if file_type == "Passes":

            t = df["Thrower"].astype(str) if "Thrower" in df else ""
            r = df["Receiver"].astype(str) if "Receiver" in df else ""

            df = df[(t == player) | (r == player)]

        elif file_type in PLAYER_COLS:

            col = PLAYER_COLS[file_type]
            if col in df.columns:
                df = df[df[col].astype(str) == player]

    return df.reset_index(drop=True)


def dataEndpoints(file_type: str, game: str, player: str):
    return (
        f"/api/data/{url_quote(file_type)}"
        f"?game={url_quote(game)}&player={url_quote(player)}"
    )


def listAllColumns(data: dict):

    return {
        file_type: sorted(df.columns.astype(str))
        for file_type, df in data.items()
        if not df.empty
    }

if __name__ == "__main__":
    import sys
    from pathlib import Path

    paths = sys.argv[1:]
    if not paths:
        print("Usage: python processor.py path/to/*.csv")
        sys.exit(1)

    file_list = []

    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[skip] not found: {p}")
            continue

        file_list.append((path.name, path.read_bytes()))

    data, warnings = processUploads(file_list)

    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(" ", w)
    else:
        print("NO WARNINGS")

    games = getGameList(data)
    players = getPlayerList(data)

    print(f"\nGames   ({len(games)}): {games}")
    print(f"Players ({len(players)}): {players}")

    cols = listAllColumns(data)

    print("\nColumns:")
    for file_type, col_list in cols.items():
        print(f"\n{file_type}")
        for c in col_list:
            print(" -", c)
