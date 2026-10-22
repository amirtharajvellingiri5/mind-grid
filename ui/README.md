# GridMind UI

Small React app for asking the GridMind API questions.

```bash
npm install
npm run dev   # http://localhost:5173
```

Requests go to `/api/*`, which Vite proxies to the API:

- Local API or SSH tunnel on :8000 (default): `ssh -i ~/.ssh/enterprise_ai_vps -N -L 8000:localhost:8000 root@147.93.154.37`
- Public URL: `API_TARGET=https://mind-grid.147.93.154.37.sslip.io API_AUTH=user:pass npm run dev`
- Calling the API directly instead (needs its `CORS_ORIGINS` to include this origin): `VITE_API_URL=http://host:8000 npm run dev`
