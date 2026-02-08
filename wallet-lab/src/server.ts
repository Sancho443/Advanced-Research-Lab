import app from './app';

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`[MAX_OP] Server running on port ${PORT}`);
  console.log(`[MAX_OP] Operational Mode: VULNERABLE`);
});