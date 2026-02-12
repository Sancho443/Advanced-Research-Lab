import { Pool } from 'pg';
export default new Pool({
  user: 'sanchez', host: 'localhost', database: 'wallet_db', password: 'password', port: 5432
});
