const express = require('express');
const async = require('async');
const { Pool } = require('pg');
const cookieParser = require('cookie-parser');
const path = require('path');
const http = require('http');

const app = express();
const server = http.Server(app);
const io = require('socket.io')(server);

// ---- Environment variables for Postgres ----
const POSTGRES_HOST = process.env.POSTGRES_HOST || 'postgres-5432-tcp.vote-app.local';
const POSTGRES_PORT = process.env.POSTGRES_PORT || 5432;
const POSTGRES_DB = process.env.POSTGRES_DB || 'postgres';
const POSTGRES_USER = process.env.POSTGRES_USER || 'postgres';
const POSTGRES_PASSWORD = process.env.POSTGRES_PASSWORD || 'postgres';
const PORT = process.env.PORT || 4000;

// ---- Socket.io connection ----
io.on('connection', function (socket) {
  socket.emit('message', { text: 'Welcome!' });

  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

// ---- PostgreSQL pool ----
const pool = new Pool({
  host: POSTGRES_HOST,
  port: POSTGRES_PORT,
  user: POSTGRES_USER,
  password: POSTGRES_PASSWORD,
  database: POSTGRES_DB,
});

// ---- Retry until Postgres is available ----
async.retry(
  { times: 1000, interval: 1000 },
  function (callback) {
    pool.connect(function (err, client, done) {
      if (err) {
        console.error('Waiting for db');
      }
      callback(err, client);
    });
  },
  function (err, client) {
    if (err) {
      return console.error('Giving up on db connection');
    }
    console.log('Connected to db');
    getVotes(client);
  }
);

// ---- Function to get votes from Postgres and emit to frontend ----
function getVotes(client) {
  client.query('SELECT vote, COUNT(id) AS count FROM votes GROUP BY vote', [], function (err, result) {
    if (err) {
      console.error('Error performing query: ' + err);
    } else {
      const votes = collectVotesFromResult(result);
      io.sockets.emit('scores', JSON.stringify(votes));
    }

    // Poll every second
    setTimeout(() => getVotes(client), 1000);
  });
}

// ---- Helper function to process query result ----
function collectVotesFromResult(result) {
  const votes = { a: 0, b: 0 };
  result.rows.forEach(row => {
    votes[row.vote] = parseInt(row.count);
  });
  return votes;
}

// ---- Express middleware ----
app.use(cookieParser());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'views')));

// ---- Serve index.html ----
app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname, 'views/index.html'));
});

// ---- Start server ----
server.listen(PORT, function () {
  console.log('App running on port ' + PORT);
});
