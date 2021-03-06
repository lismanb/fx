DROP TABLE IF EXISTS transactions;

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  currency CHAR(3) NOT NULL ,
  rate FLOAT NOT NULL ,
  amount FLOAT NOT NULL ,
  amount_usd FLOAT NOT NULL ,
  rate_at TIMESTAMP NOT NULL DEFAULT NOW(),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);