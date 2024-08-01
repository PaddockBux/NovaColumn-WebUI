import json
import random
import mariadb
from flask import Flask, jsonify, request

app = Flask(__name__)

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
    cursor.execute(f"SELECT * FROM main WHERE uid = {random.randrange(0, maxrange)}")
    req = cursor.fetchone()
    # (114, 40, 25579, 1722446968.5482442, 0, 10, 3, 2, '[]', 1, 20, 146.869)
    jsonout = {}
    jsonout['port'] = req[2]
    jsonout['time'] = req[3]
    jsonout['playercount'] = req[4]
    jsonout['playermax'] = req[5]
    jsonout['players'] = json.loads(req[8])
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

    return jsonify(jsonout)

if __name__ == '__main__':
   app.run()