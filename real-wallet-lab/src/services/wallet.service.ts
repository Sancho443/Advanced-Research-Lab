import pool from '../db';

export class WalletService {
  async getBalance(id: string) {
    const res = await pool.query('SELECT * FROM wallets WHERE id = $1', [id]);
    return res.rows[0];
  }

  async transfer(from: number, to: number, amt: number) {
    const client = await pool.connect();
    try {
      // 1. READ Balance
      const res = await client.query('SELECT balance FROM wallets WHERE id = $1', [from]);
      const balance = parseFloat(res.rows[0].balance);

      if (balance < amt) throw new Error('Insufficient funds');

      // 2. THE GAP (Simulated Lag)
      await new Promise(r => setTimeout(r, 1000));

      // 3. WRITE New Balance
      await client.query('UPDATE wallets SET balance = balance - $1 WHERE id = $2', [amt, from]);
      await client.query('UPDATE wallets SET balance = balance + $1 WHERE id = $2', [amt, to]);

      return { success: true, newBalance: balance - amt };
    } finally {
      client.release();
    }
  }
}