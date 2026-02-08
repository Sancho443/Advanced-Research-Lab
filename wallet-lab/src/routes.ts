import { Router, Request, Response } from 'express';
import { WalletService } from './services/wallet.service';

const router = Router();
const walletService = new WalletService();

// GET Balance
router.get('/wallet/:id', async (req: Request, res: Response) => {
  try {
    const wallet = await walletService.getBalance(req.params.id);
    if (!wallet) return res.status(404).json({ error: "Wallet not found" });
    res.json(wallet);
  } catch (err) {
    res.status(500).json({ error: "Internal Server Error" });
  }
});

// POST Transfer (THE VULNERABLE ENDPOINT)
router.post('/transfer', async (req: Request, res: Response) => {
  try {
    const { fromId, toId, amount } = req.body;
    
    // Pass the request to the service layer
    const result = await walletService.transfer(fromId, toId, amount);
    
    res.json(result);
  } catch (err: any) {
    res.status(400).json({ error: err.message || "Transfer failed" });
  }
});

export default router;
