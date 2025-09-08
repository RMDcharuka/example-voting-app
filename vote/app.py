from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging

# ----------------------------
# Environment Variables
# ----------------------------
OPTION_A = os.getenv('OPTION_A', "Cats")
OPTION_B = os.getenv('OPTION_B', "Dogs")
HOSTNAME = socket.gethostname()

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-6379-tcp.vote-app.local')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_TIMEOUT = int(os.getenv('REDIS_TIMEOUT', 5))

# Optional: Postgres configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres-5432-tcp.vote-app.local')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')

# ----------------------------
# Flask App Setup
# ----------------------------
app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

# ----------------------------
# Redis Connection
# ----------------------------
def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            socket_timeout=REDIS_TIMEOUT
        )
    return g.redis

# ----------------------------
# Flask Routes
# ----------------------------
@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        vote = request.form.get('vote')
        if vote:
            redis = get_redis()
            app.logger.info('Received vote for %s', vote)
            data = json.dumps({'voter_id': voter_id, 'vote': vote})
            try:
                redis.rpush('votes', data)
            except Exception as e:
                app.logger.error('Redis push failed: %s', e)

    resp = make_response(render_template(
        'index.html',
        option_a=OPTION_A,
        option_b=OPTION_B,
        hostname=HOSTNAME,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
