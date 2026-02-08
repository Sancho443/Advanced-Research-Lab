import express from 'express';
import walletRoutes from './routes';

const app = express();

// Middleware to parse JSON bodies
app.use(express.json());

// Mount the Wallet Routes
app.use('/', walletRoutes);

export default app;