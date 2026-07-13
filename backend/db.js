const { Pool } = require("pg");

const pool = new Pool({
  user: "postgres",
  host: "localhost",
  database: "csr_chatbot",
  password: "saanvi123",
  port: 5432,
});

module.exports = pool;