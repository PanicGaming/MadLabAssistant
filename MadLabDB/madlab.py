import sqlite3
from datetime import datetime

def init_db(path):
    def check_table(cursor, tablename):
        query = "SELECT name FROM sqlite_master WHERE type='table' and name=?"
        return cursor.execute(query, (tablename,)).fetchone()

    with sqlite3.connect(path) as conn:
        c = conn.cursor()
        if not check_table(c, "Games"):
            c.execute("CREATE TABLE Games\n"
                      "            (gameid INTEGER PRIMARY KEY ASC,\n"
                      "             gamename TEXT,\n"
                      "             UNIQUE (gamename)"
                      "             )")
        if not check_table(c, "Streams"):
            c.execute("CREATE TABLE Streams\n"
                      "            (streamid INTEGER PRIMARY KEY ASC,\n"
                      "             gameid INTEGER, \n"
                      "             title TEXT, \n"
                      "             streamdate TIMESTAMP, "
                      "             state TEXT, "
                      "             FOREIGN KEY (gameid) REFERENCES Games(gameid)\n"
                      "             )")

        if not check_table(c, "Info"):
            c.execute("CREATE TABLE Info\n"
                      "             (infoid INTEGER PRIMARY KEY ASC,\n"
                      "              infokey TEXT,\n"
                      "              strval TEXT,\n"
                      "              intval INTEGER,\n"
                      "              UNIQUE (infokey)\n"
                      "             )")


def add_stream(path, game, title, when):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        _gameid = None
        if "" == game:
            res = c.execute('SELECT intval, strval FROM Info\n'
                                'WHERE infokey="CurrentGame"').fetchone()
            _gameid = res["intval"]
            game = res["strval"]
        else:
            res = c.execute('SELECT gameid FROM Games\n'
                            'WHERE gamename = ?', (game,)).fetchone()
            if res:
                _gameid = res["gameid"]

        if _gameid:
            if not when:
                _when = None
            else:
                _when = datetime.strptime(when.replace("/", "-"), "%m-%d-%y %H:%M")
            if not title:
                _title = "No working stream title"
            else:
                _title = title
            c.execute('INSERT INTO Streams\n'
                      '(gameid, title, streamdate, state)'
                      'VALUES (?, ?, ?, ?)', (_gameid, _title, _when, "SCH"))
            conn.commit()
            if not when:
                msg = f"Added {title} stream for {game} on unspecified date."
            else:
                msg = f"Added {title} stream for {game} on {when}."
        else:
            msg = f"No entry for {game}.  Please add it first."
        return msg

def start_stream(path):
    return

def stop_stream(path):
    return

def add_game(path, game):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        num = c.execute('INSERT OR IGNORE INTO Games (gamename)\n'
                        'VALUES (?)', (game,)).rowcount
        conn.commit()
        if num > 0:
            return f"Now tracking {game} for streaming"
        else:
            return f"Already tracking {game}.  Did you mean to !addstream instead?"


def set_current(path, game):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("INSERT INTO INFO\n"
                  "(infokey)\n"
                  "SELECT 'CurrentGame'\n"
                  "WHERE NOT EXISTS (SELECT 1 FROM INFO WHERE infokey = 'CurrentGame')\n")
        conn.commit()
        res = c.execute("SELECT gameid\n"
                        "FROM Games\n"
                        "WHERE gamename = ?", (game,)).fetchone()
        if res:
            gameid = res["gameid"]
        else:
            return f"Game {game} is not tracked."

        c.execute("UPDATE INFO\n"
                  "SET strval = ?,\n"
                  "    intval = ?\n", (game, gameid))

        conn.commit()
        return f"{game} is now the current game!"

def get_next_stream(path):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        res = c.execute("SELECT G.gamename as gamename, "
                  "       S.title as title, "
                  "       S.streamdate as streamdate, "
                  "FROM Games AS G "
                  " JOIN Streams AS S ON G.gameid = s.gameid "
                  "WHERE S.state = 'SCH' "
                  " AND S.streamdate IS NOT NULL "
                  "ORDER BY S.streamdate DESC "
                  "LIMIT 1"
                  )
        if res:
            _game = res["gamename"]
            _title = res["title"]
            _when = res["streamdate"]
            return f"{_game} - {_title} will be streaming on {_when}"
        else:
            return f"No current streams are scheduled."