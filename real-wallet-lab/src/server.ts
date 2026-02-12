import express from 'express';
import { WalletService } from './services/wallet.service';

const app = express();
app.use(express.json());
const service = new WalletService();

app.get('/wallet/:id', async (req, res) => {
  const w = await service.getBalance(req.params.id);
  res.json(w || { error: 'Not found' });
});

app.post('/wallet/transfer', async (req, res) => {
  try {
    const { fromId, toId, amount } = req.body;
    const result = await service.transfer(fromId, toId, amount);
    res.json(result);
  } catch (e: any) { 
      res.status(400).json({ error: e.message }); 
  }
});

app.listen(3000, () => console.log('[MAX_OP] Bank running on Localhost:3000 (HTTP)'));