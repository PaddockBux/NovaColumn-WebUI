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
    rand = random.randrange(1, maxrange)
    print(f"Getting unique server {rand} - {unique_servers[rand][0], unique_servers[rand][1]}")

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
    valid = []
    for player in jsonout['players']:
        cursor.execute(f"SELECT username FROM playernames WHERE uid = {player}")
        username.append(cursor.fetchone()[0])
        cursor.execute(f"SELECT userid FROM playernames WHERE uid = {player}")
        userid.append(cursor.fetchone()[0])
        cursor.execute(f"SELECT valid FROM playernames WHERE uid = {player}")
        valid.append(cursor.fetchone()[0])
    jsonout['players'] = username
    jsonout['playersid'] = userid
    jsonout['validity'] = valid
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
    cursor.execute("SELECT * FROM main WHERE ip_fk = ? AND port = ?", (req[1], req[2]))
    request = cursor.fetchall()
    x = []
    y = []
    for index in range(len(request)):
        y.append(request[index][4])
        x.append(request[index][3])
        # x.append(datetime.fromtimestamp(request[index][3]).strftime('%Y-%m-%d %H:%M:%S'))
    jsonout['playergraph'] = x, y
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
