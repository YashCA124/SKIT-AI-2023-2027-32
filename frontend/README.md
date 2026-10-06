# Frontend development

Run the FastAPI backend on `http://localhost:8000`, then start the frontend:

```sh
npm install
npm run dev
```

During development, Vite proxies `/auth`, `/tokenauth`, `/health`, and `/ready`
to the backend at `http://localhost:8000`. This keeps API calls same-origin
from the browser and avoids configuring backend CORS for local development.

To use a backend on another address, set `VITE_API_PROXY_TARGET` in a local
`.env.local` file (see `.env.example`) and restart Vite. If `VITE_API_BASE_URL`
is set instead, the frontend calls that API origin directly; the backend must
allow the frontend's origin through CORS. Production builds do not use Vite's
development proxy and should set `VITE_API_BASE_URL` to the deployed API origin.