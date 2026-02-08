CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00
);

-- Seeding victims
INSERT INTO wallets (user_id, balance) VALUES (101, 50.00); -- Attacker (You)
INSERT INTO wallets (user_id, balance) VALUES (102, 10000.00); -- Victim (Whale)