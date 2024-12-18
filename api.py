from flask import Flask, jsonify
from flask_cors import CORS
import argparse
import cherrypy
import mariadb
import random
import ast

app = Flask(__name__)
CORS(app)

parse = argparse.ArgumentParser(
    description='''
           _  __              _____     __                   _      __    __   __  ______
          / |/ /__ _  _____ _/ ___/__  / /_ ____ _  ___  ___| | /| / /__ / /  / / / /  _/
         /    / _ \\ |/ / _ `/ /__/ _ \\/ / // /  ' \\/ _ \\/___/ |/ |/ / -_) _ \\/ /_/ // /  
        /_/|_/\\___/___/\\_,_/\\___/\\___/_/\\_,_/_/_/_/_//_/    |__/|__/\\__/_.__/\\____/___/  
                                     NovaColumn-WebUI
           Programmed by & main ideas guy: GoGreek    ::    Co-ideas guy: Draxillian
''',
formatter_class=argparse.RawDescriptionHelpFormatter,
epilog='''
Use case:
python api.py localhost root password novacolumn

Output translation:
[GET] (random unique server) / (latest uid from server) - ((IP foreign key), (port))
'''
# print(f"[GET] {rand}/{latest} - {unique_servers[rand][0], unique_servers[rand][1]}")
)
parse.add_argument('host', type=str, help="host IP of the database")
parse.add_argument('username', type=str, help="database username to use.")
parse.add_argument('password', type=str, help="database password to use.")
parse.add_argument('database', type=str, help="database name to use.")
parse.add_argument('--dbport', type=int, default=3306, help="use a different database port. (default 3306)")
parse.add_argument('--port', type=int, default=8080, help="use a different API port instead of default (8080).")
arguments = parse.parse_args()

try:
    conn = mariadb.connect(
        user=arguments.username,
        password=arguments.password,
        host=arguments.host,
        port=arguments.dbport,
        database=arguments.database
    )
    print(f"Successfully connected MariaDB with user {arguments.username}")
    cursor = conn.cursor()
    memory = None
    unique_servers = None

except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    exit(1)

# def get_unique_servers(cursor, count):
#     if not count:
#         cursor.execute("SELECT MAX(uid) FROM main GROUP BY ip_fk, port")
#         unique_servers = cursor.fetchall()
#         maxrange = len(unique_servers)
#         return maxrange
#     else:
#         cursor.execute("SELECT COUNT(DISTINCT ip_fk, port) FROM main")
#         return cursor.fetchone()

# def get_latest_uid(cursor, rand):
#     cursor.execute("SELECT MAX(uid) FROM main WHERE ip_fk = ? AND port = ?", (unique_servers[rand][0], unique_servers[rand][1]))
#     rand = cursor.fetchone()[0]
#     return rand

@app.route('/', methods=['GET'])
def get_main():
    global memory
    global unique_servers
    cursor.execute("SELECT COUNT(DISTINCT ip_fk, PORT) FROM main")
    sreq = cursor.fetchone()[0]
    if memory != sreq:
        memory = sreq
        cursor.execute("SELECT MAX(m.uid) FROM main m JOIN online o ON m.uid = o.main_fk WHERE o.online = 1 GROUP BY ip_fk, port")
        unique_servers = cursor.fetchall()
    rand = random.randrange(1, memory)
    latest = unique_servers[rand][0]
    print(f"[GET] {rand}")
    cursor.execute('SELECT i.address, a.port, a.ping, a.playercount, a.playermax, a.users_fk, a.signed, FROM_UNIXTIME(a.time), m.text, v.text, c.data FROM main a JOIN ips i ON a.ip_fk = i.uid JOIN motds m ON a.motd_fk = m.uid JOIN versions v ON a.ver_fk = v.uid JOIN icons c ON a.icon_fk = c.uid WHERE a.uid = ? GROUP BY i.address, a.port', (latest,))
    info = cursor.fetchone()
    info_out = {}
    info_out['ip'] = info[0]
    info_out['port'] = info[1]
    info_out['ping'] = info[2]
    info_out['playercount'] = info[3]
    info_out['playermax'] = info[4]
    info_out['signed'] = info[6]
    info_out['time'] = info[7]
    info_out['motd'] = info[8]
    info_out['version'] = info[9]
    info_out['icon'] = info[10]
    playeruidlist = ast.literal_eval(info[5])
    if isinstance(playeruidlist, int):
        playeruidlist = [playeruidlist]
    if playeruidlist != []:
        cursor.execute('SELECT username, userid, valid FROM playernames WHERE uid IN ({})'.format(', '.join(map(str, playeruidlist))))
    playeruidlist_out = cursor.fetchall()
    username = []
    userid = []
    valid = []
    for index in range(len(playeruidlist_out)):
        username.append(playeruidlist_out[index][0])
        userid.append(playeruidlist_out[index][1])
        valid.append(playeruidlist_out[index][2])
    info_out['players'] = username
    info_out['playersid'] = userid
    info_out['validity'] = valid
    cursor.execute('SELECT playercount, FROM_UNIXTIME(time) FROM main WHERE ip_fk = (SELECT uid FROM ips WHERE address = ?) AND port = ?', (info_out['ip'], info_out['port']))
    graph = cursor.fetchall()
    x = []
    y = []
    for index in range(len(graph)):
        x.append(graph[index][0])
        y.append(graph[index][1])
    info_out['playergraph'] = y, x
    print(f"[SENT] {info_out['ip']}:{info_out['port']} - {info_out['playercount']}/{info_out['playermax']}")
    return jsonify(info_out)

if __name__ == '__main__':
    cherrypy.tree.graft(app, '/')
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': arguments.port,
        'server.thread_pool': 30,
        'server.max_request_body_size': 0,
        'server.socket_timeout': 60,
        'log.access_file': 'access.log',
        'log.error_file': 'error.log',
        'log.screen': True
    })
    cherrypy.engine.start()
    cherrypy.engine.block()