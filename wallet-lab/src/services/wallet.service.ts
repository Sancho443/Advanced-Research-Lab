import { pool } from '../db';

export class WalletService {
  
  async getBalance(walletId: string) {
    const result = await pool.query('SELECT * FROM wallets WHERE id = $1', [walletId]);
    return result.rows[0];
  }

  async transfer(fromId: number, toId: number, amount: number) {
    // 1. GET CURRENT BALANCE
    const senderRes = await pool.query('SELECT balance FROM wallets WHERE id = $1', [fromId]);
    const sender = senderRes.rows[0];

    if (!sender) throw new Error('Sender not found');
    const balance = parseFloat(sender.balance);

    if (balance < amount) {
      throw new Error('Insufficient funds');
    }

    // 2. ARTIFICIAL DELAY (The Vulnerability)
    await new Promise(r => setTimeout(r, 1000));

    // 3. UPDATE BALANCES
    await pool.query('UPDATE wallets SET balance = balance - $1 WHERE id = $2', [amount, fromId]);
    await pool.query('UPDATE wallets SET balance = balance + $1 WHERE id = $2', [amount, toId]);

    return { success: true, newBalance: balance - amount };
  }
}
