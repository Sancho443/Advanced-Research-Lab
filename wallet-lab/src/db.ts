import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

export const pool = new Pool({
  host: process.env.DB_HOST || 'db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASS || 'secret123',
  database: process.env.DB_NAME || 'wallet_db',
  port: 5432,
  max: 20, // Connection limit
  idleTimeoutMillis: 30000,
});