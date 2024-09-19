import ast
from datetime import datetime
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
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    exit(1)

def get_latest_uid(cursor, rand):
    cursor.execute("SELECT ip_fk, port FROM main WHERE uid = ?", (rand,))
    query = cursor.fetchone()
    ip_fk = query[0]
    port = query[1]
    cursor.execute(f"SELECT MAX(uid) FROM main WHERE ip_fk = ? AND port = ?", (ip_fk, port))
    rand = cursor.fetchone()[0]
    return rand

@app.route('/', methods=['GET'])
def get_main():
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(uid) FROM main")
    maxrange = cursor.fetchone()[0]
    rand = random.randrange(1, maxrange)

    latest = get_latest_uid(cursor, rand)

    cursor.execute(f"SELECT online FROM online WHERE main_fk = ?", (latest,))
    online_type = cursor.fetchone()[0]
    while online_type == 0:
        rand = random.randrange(1, maxrange)

        latest = get_latest_uid(cursor, rand)

        cursor.execute(f"SELECT online FROM online WHERE main_fk = ?", (latest,))
        online_type = cursor.fetchone()[0]
        

    print("----------------------")
    print(f"Getting UID {latest}")
    cursor.execute(f"SELECT * FROM main WHERE uid = {latest}")
    req = cursor.fetchone()
    jsonout = {}
    jsonout['port'] = req[2]
    jsonout['time'] = datetime.fromtimestamp(req[3]).strftime('%Y-%m-%d %H:%M:%S')
    jsonout['playercount'] = req[4]
    jsonout['playermax'] = req[5]
    jsonout['players'] = ast.literal_eval(req[8])
    username = []
    userid = []
    for player in jsonout['players']:
        cursor.execute(f"SELECT username FROM playernames WHERE uid = {player}")
        username.append(cursor.fetchone()[0])
        cursor.execute(f"SELECT userid FROM playernames WHERE uid = {player}")
        userid.append(cursor.fetchone()[0])
    jsonout['players'] = username
    jsonout['playersid'] = userid
    jsonout['signed'] = req[9]
    jsonout['ping'] = req[11]

    cursor.execute(f"SELECT address FROM ips WHERE uid = {req[1]}")
    jsonout['ip'] = cursor.fetchone()[0]
    cursor.execute(f"SELECT text FROM motds WHERE uid = {req[6]}")
    jsonout['motd'] = cursor.fetchone()[0]
    cursor.execute(f"SELECT text FROM versions WHERE uid = {req[7]}")
    jsonout['version'] = cursor.fetchone()[0]
    cursor.execute(f"SELECT data FROM icons WHERE uid = {req[10]}")
    jsonout['icon'] = cursor.fetchone()[0]
    print(f"Gave data:\n{jsonout['icon'][:40]}...\n{jsonout['ip']}\n{jsonout['motd']}\n{jsonout['ping']}\n{jsonout['playercount']}\n{jsonout['playermax']}\n{jsonout['players']}\n{jsonout['playersid']}\n{jsonout['port']}\n{jsonout['signed']}\n{jsonout['time']}\n{jsonout['version']}")
    return jsonify(jsonout)

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
