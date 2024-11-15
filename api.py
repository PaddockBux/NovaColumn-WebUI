import ast
import random
import mariadb
from flask import Flask, jsonify
import cherrypy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

try:
    conn = mariadb.connect(
        user="root",
        password="",
        host="localhost",
        port=3306,
        database="novacolumn"
    )
    print("Successfully connected MariaDB.")
    cursor = conn.cursor()
    print("Initializing tables...")
    cursor.execute("SELECT DISTINCT ip_fk, PORT FROM main")
    unique_servers = cursor.fetchall()
    maxrange = len(unique_servers)
    print(f"Found {maxrange} unique servers")
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    exit(1)

def get_latest_uid(cursor, rand):
    cursor.execute("SELECT MAX(uid) FROM main WHERE ip_fk = ? AND port = ?", (unique_servers[rand][0], unique_servers[rand][1]))
    rand = cursor.fetchone()[0]
    return rand

@app.route('/', methods=['GET'])
def get_main():
    online_type = 0
    while online_type == 0:
        rand = random.randrange(1, maxrange)
        latest = get_latest_uid(cursor, rand)
        cursor.execute(f"SELECT online FROM online WHERE main_fk = ?", (latest,))
        online_type = cursor.fetchone()[0]
    print(f"[GET] {rand}/{latest} - {unique_servers[rand][0], unique_servers[rand][1]}")
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
    return jsonify(info_out)

if __name__ == '__main__':
    cherrypy.tree.graft(app, '/')
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'server.thread_pool': 30,
        'server.max_request_body_size': 0,
        'server.socket_timeout': 60,
        'log.access_file': 'access.log',
        'log.error_file': 'error.log',
        'log.screen': True
    })
    cherrypy.engine.start()
    cherrypy.engine.block()