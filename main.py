import ast
import time
from datetime import datetime
from collections import defaultdict
import random
import mariadb
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
requests_data = defaultdict(list)
RATE_LIMIT = 100 # requests
TIME_WINDOW = 60  # seconds

@app.before_request
def limit_remote_addr():
    ip = request.remote_addr
    requests = requests_data[ip]
    now = time.time()

    # Filter out old requests
    requests = [req for req in requests if req > now - TIME_WINDOW]
    requests_data[ip] = requests

    if len(requests) >= RATE_LIMIT:
        return jsonify({"error": "rate limit exceeded"}), 429

    requests.append(now)

try:
    conn = mariadb.connect(
        user="root",
        password="",
        host="localhost",
        port=3306,
        database="novadevel_main"
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")

@app.route('/api/main', methods=['GET'])
def get_main():
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(uid) FROM main")
    maxrange = cursor.fetchone()[0]
    rand = random.randrange(0, maxrange)
    print(f"Getting UID {rand}")
    cursor.execute(f"SELECT * FROM main WHERE uid = {rand}")
    req = cursor.fetchone()
    # (114, 40, 25579, 1722446968.5482442, 0, 10, 3, 2, '[]', 1, 20, 146.869)
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
   app.run()