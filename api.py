import argparse
import cherrypy
import mariadb
import base64
import re
import os

parse = argparse.ArgumentParser(
    description='''
                  _  _               ___     _                     _   ___ ___ 
                 | \\| |_____ ____ _ / __|___| |_  _ _ __  _ _ ___ /_\\ | _ \\_ _|
                 | .` / _ \\ V / _` | (__/ _ \\ | || | '  \\| ' \\___/ _ \\|  _/| | 
                 |_|\\_\\___/\\_/\\__,_|\\___\\___/_|\\_,_|_|_|_|_||_| /_/ \\_\\_| |___|
                                          NovaColumn-API
           Programmed by & main ideas guy: GoGreek    ::    Co-ideas guy: Draxillian
''',
formatter_class=argparse.RawDescriptionHelpFormatter
)
parse.add_argument('host', type=str, help="host IP of the database")
parse.add_argument('username', type=str, help="database username to use.")
parse.add_argument('database', type=str, help="database name to use.")
parse.add_argument('--password', type=str, default="", help="database password to use. (default empty (''))")
parse.add_argument('--dbport', type=int, default=3306, help="use a different database port. (default 3306)")
parse.add_argument('--aport', type=int, default=8080, help="use a different API port. (default 8080)")
parse.add_argument('--ahost', type=str, default='localhost', help="use a different API host. (default localhost)")
parse.add_argument('--limit', type=int, default=75, help="add a hard limit to the API response given. (default 75, can be disabled with -1)")
parse.add_argument('--image', type=str, default=os.path.abspath('assets/pack64.png'), help="the path to the default image when servers have no icon. (default assets/pack64.png)")
arguments = parse.parse_args()

if arguments.limit < 1:
    print("--limit cannot be less than 1")
    exit(1)

try:
    conn = mariadb.connect(
        user=arguments.username,
        password=arguments.password,
        host=arguments.host,
        port=arguments.dbport,
        database=arguments.database
    )
    conn.autocommit = True
    print(f"Successfully connected MariaDB with user {arguments.username}")
    cursor = conn.cursor()

except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    exit(1)

def cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

cherrypy.tools.cors = cherrypy.Tool('before_handler', cors)

def jsonError(code, string):
    cherrypy.response.status = code
    return cherrypy._json.encode({'error': string})

class api:
    @cherrypy.expose()
    def search(self, **kwargs):
        allowedParams = {'suid', 'ip', 'version', 'protocol', 'port', 'icon', 'playercount', 'playermax', 'motd', 'limit', 'order', 'desc', 'online'}
        columns = ['suid', 'ip', 'port', 'ping', 'playercount', 'playermax', 'playerinfo', 'signed', 'timestamp', 'motd', 'version', 'icon_id', 'availability']
        disallowedParams = {'limit', 'order', 'desc'}
        intTypeParams = {'limit', 'port', 'protocol', 'icon', 'playercount', 'playermax'}
        boolTypeParams = {'online'}
        allowedBoolParams = {'true': '1', 'false': '0', '0': '0', '1': '1'}
        filterMapping = {
            'suid': 'a.uid',
            'ip': 'i.address',
            'port': 'a.port',
            'playercount': 'a.playercount',
            'playermax': 'a.playermax',
            'signed': 'a.signed',
            'timestamp': 'a.time',
            'motd': 'm.utext',
            'version': 'v.text',
            'protocol': 'a.protocol',
            'icon_id': 'a.icon_fk',
            'online': 'o.online',
            'random': 'RAND()'
        }
        
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if not set(kwargs.keys()).issubset(allowedParams):
            return jsonError(400, "invalid argument")

        for arg, key in kwargs.items():
            if arg in intTypeParams:
                try:
                    int(key)
                except ValueError:
                    return jsonError(400, f"{arg} must be an integer")
            if arg in boolTypeParams:
                try:
                    if key not in allowedBoolParams:
                        return jsonError(400, f"{arg} can only be 'true', 'false', 1, or 0")
                    kwargs[arg] = allowedBoolParams[key]
                except ValueError:
                    return jsonError(400, f"{arg} must be an boolean (true/false, 1/0)")
            
        query = (
            "SELECT a.uid, i.address, a.port, a.ping, a.playercount, a.playermax, "
            "a.signed, FROM_UNIXTIME(a.time), m.text, m.utext, v.text, a.protocol, c.uid, o.online, FROM_UNIXTIME(o.time), GROUP_CONCAT(CONCAT_WS('|', p.username, p.userid, p.valid) SEPARATOR '; ')"
            "FROM main a "
            "JOIN ips i ON a.ip_fk = i.uid "
            "JOIN motds m ON a.motd_fk = m.uid "
            "JOIN versions v ON a.ver_fk = v.uid "
            "JOIN icons c ON a.icon_fk = c.uid "
            "JOIN online o ON a.uid = o.main_fk "
            "LEFT JOIN rel_player_server r ON a.uid = r.main_fk "
            "LEFT JOIN playernames p ON r.player_fk = p.uid "
            "WHERE o.time = (SELECT MAX(time) FROM online WHERE main_fk = a.uid) "
        )

        keyOrder = []
        doOrder = False
        descOrder = False
        addLim = False
        wildcards = {'motd', 'ip', 'version'}
        if not kwargs.get('suid'):
            query += " AND a.time = (SELECT MAX(a2.time) FROM main a2 JOIN ips i2 ON a2.ip_fk = i2.uid WHERE i2.address = i.address AND a2.port = a.port)"
            for item, key in kwargs.items():
                if item not in disallowedParams:
                    if 'WHERE' in query:
                        query += " AND"
                    else:
                        query += " WHERE"
                if item in wildcards:
                    query += " " + filterMapping[item] + " LIKE ?"
                elif item == 'limit':
                    addLim = True
                elif item == 'order':
                    doOrder = True
                elif item == 'desc':
                    descOrder = True
                else:
                    pattern = re.compile(r'^(>=|<=|>|<|!=)?(\d+)$')
                    match = pattern.match(key)
                    if match:
                        operator = match.group(1) or '='
                        number = int(match.group(2))
                    try:
                        query += " " + filterMapping[item] + f" {operator} ?"
                    except UnboundLocalError:
                        return jsonError(400, "invalid operand")
                    key = number

                keyOrder.append(key)
            query += " GROUP BY i.address, a.port"
        else:
            allowedUIDParams = {'suid', 'limit', 'order', 'desc'}
            if not set(kwargs.keys()).issubset(allowedUIDParams):
                return jsonError(400, "only limit and sorting arguments allowed on suid")
            for item, key in kwargs.items():
                if item not in disallowedParams:
                    if 'WHERE' in query:
                        query += " AND"
                    else:
                        query += " WHERE"
                if item == 'suid':
                    query += " i.address = (SELECT address FROM ips i JOIN main a ON a.ip_fk = i.uid WHERE a.uid = ?) AND a.port = (SELECT port FROM main WHERE uid = ?)"
                    for _ in range(0, 2):
                        keyOrder.append(key)
                elif item == 'limit':
                    addLim = True
                elif item == 'order':
                    doOrder = True
                elif item == 'desc':
                    descOrder = True
                if item != 'suid':
                    keyOrder.append(key)
        if "GROUP BY" in query:
            query += ", a.uid"
        else:
            query += " GROUP BY a.uid"
        if doOrder:
            query += " ORDER BY "
            keyOrder.remove(kwargs.get('order'))
            orderArray = str(kwargs.get('order')).split('|')
            for index, item in enumerate(orderArray):
                if item in filterMapping:
                    if index > 0:
                        query += ", "
                    query += filterMapping[item]
                else:
                    return jsonError(400, "invalid order type")
            if descOrder:
                keyOrder.remove(kwargs.get('desc'))
                query += " DESC"
        if addLim:
            if int(kwargs.get('limit')) < 1:
                return jsonError(400, "limit cannot be negative or 0")
            query += " LIMIT ?"
            keyOrder.remove(kwargs.get('limit'))
            if arguments.limit == -1:
                keyOrder.append(int(kwargs.get('limit')))
            elif int(kwargs.get('limit')) > arguments.limit:
                keyOrder.append(arguments.limit)
            else:
                keyOrder.append(int(kwargs.get('limit')))
        elif not arguments.limit == -1:
            query += " LIMIT ?"
            keyOrder.append(arguments.limit)

        cursor.execute(query, keyOrder)
        results = cursor.fetchall()

        response = []
        for row in results:
            row_list = list(row)
            pInfo = []
            for usr in str(row_list[15]).split(';'):
                usr = usr.strip()
                if usr:
                    parts = usr.split('|')
                    if len(parts) >= 3:
                        username = parts[0].strip()
                        userid = parts[1].strip()
                        valid = parts[2].strip()
                        pInfo.append({
                            'username': username,
                            'userid': userid,
                            'valid': valid
                        })
            row_list.insert(6, pInfo)   
            row_list[8] = str(row_list[8])
            row_list[9] = {'formatted': row_list[9], 'unformatted': row_list[10]}
            row_list.remove(row_list[10])
            row_list[10] = {'text': row_list[10], 'protocol': row_list[11]}
            row_list.remove(row_list[11])
            row_list[13] = str(row_list[13])
            row_list[12] = {'online': bool(row_list[12]), 'last_checked': row_list[13]}
            row_list.remove(row_list[13])
            response.append(dict(zip(columns, row_list)))
        return cherrypy._json.encode(response)

    @cherrypy.expose
    def icon(self, **kwargs):
        allowedParams = {'id', 'base'}
        cherrypy.response.headers['Content-Type'] = 'application/json'
        if not kwargs.get('id'):
            return jsonError(400, "no arguments given")
        if not set(kwargs.keys()).issubset(allowedParams):
            return jsonError(400, "invalid argument")
        try:
            int(kwargs.get('id'))
        except Exception:
            return jsonError(400, "id must be an integer")
        cursor.execute("SELECT data FROM icons WHERE uid = ?", (kwargs.get('id'),))
        try:
            sreq = cursor.fetchone()[0]
        except Exception:
            return jsonError(404, "icon not found")
        if sreq == "NO_ICON":
            if 'base' in kwargs:
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                with open(arguments.image, 'rb') as file:
                    return "data:image/png;base64," + base64.b64encode(file.read()).decode('utf-8')
            else:
                cherrypy.response.headers['Content-Type'] = 'image/png'
                with open(arguments.image, 'rb') as file:
                    return file.read()
        elif sreq:
            if 'base' in kwargs:
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                return sreq
            else:
                cherrypy.response.headers['Content-Type'] = 'image/png'
                return base64.b64decode(sreq[22:] + "=")
    
    @cherrypy.expose
    def player(self, **kwargs):
        allowedParams = {'username', 'uuid'}
        filterMapping = {'username': 'p.username', 'uuid': 'p.userid'}
        mainColumns = []

        cherrypy.response.headers['Content-Type'] = 'application/json'

        if not kwargs:
            return jsonError(400, "no arguments given")
        if not set(kwargs.keys()).issubset(allowedParams):
            return jsonError(400, "invalid argument")
        if len(kwargs.items()) > 1:
            return jsonError(400, "cannot have more than 1 argument")
        
        for arg, key in kwargs.items():
            values = key.split('|')
            conditions = " OR ".join(["{} LIKE ?".format(filterMapping[arg]) for _ in values])
            playerInfoQuery = "SELECT * FROM playernames p WHERE {}".format(conditions)
            cursor.execute(playerInfoQuery, values)
            playerInfoRequest = cursor.fetchall()

            vIn = ""
            for item in playerInfoRequest:
                vIn += item[1] + "|"
            serversQuery = "SELECT m.uid, FROM_UNIXTIME(m.time), p.uid FROM main m JOIN rel_player_server mp ON m.uid = mp.main_fk JOIN playernames p ON mp.player_fk = p.uid WHERE {} REGEXP ?".format(filterMapping[arg])
            cursor.execute(serversQuery, (vIn,))
            serverRequest = cursor.fetchall()

        for item in playerInfoRequest:
            subColumns = {}
            playerInfoColumns = {}
            playerInfoColumns['username'] = item[1]
            playerInfoColumns['uuid'] = item[2]
            playerInfoColumns['validity'] = item[3]
            subColumns['playerinfo'] = playerInfoColumns

            serverList = []
            for serverUID in serverRequest:
                if serverUID[2] == item[0]:
                    listed = list(serverUID)
                    listed[1] = str(listed[1])
                    serverList.append({'suid': listed[0], 'timestamp': listed[1]})
            subColumns['servers'] = serverList

            mainColumns.append(subColumns)

        return cherrypy._json.encode(mainColumns)

    @cherrypy.expose
    def index(self):
        with open("static/index.html", "r") as file:
            return file.read()

if __name__ == '__main__':
    if 'logs' not in os.listdir():
        os.mkdir(os.path.abspath("logs/"))

    cherrypy.config.update({
        'server.socket_host': arguments.ahost,
        'server.socket_port': arguments.aport,
        'environment': 'production',
        'log.access_file': os.path.abspath("logs/access.log"),
        'log.error_file': os.path.abspath("logs/error.log"),
        'log.screen': True,
        'tools.cors.on': True
    })
    cherrypy.tree.mount(api(), "/")

    cherrypy.tree.mount(None, "/swagger.json", {
    "/": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.abspath("assets/swagger.json")
    }
    })
    cherrypy.tree.mount(None, "/favicon.ico", {
    "/": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.abspath("assets/nova.png")
    }
    })

    cherrypy.engine.start()
    cherrypy.engine.block()