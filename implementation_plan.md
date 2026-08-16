# Implementation Plan: Fix and Streamline Whole App Running Workflow

This plan resolves all issues in running the Plantify backend, frontend, database, migrations, external services, and inter-service communication seamlessly.

## Identified Workflow Issues & Root Causes

1. **Missing Unified Orchestration**: The root project lacked startup scripts or root `package.json` scripts, forcing users to manually manage 5+ steps across separate terminal windows.
2. **Frontend Authentication Block on Scans & API Calls**: Backend protected endpoints reject unauthenticated requests with HTTP 401/403. The frontend UI had no active login screen and didn't auto-authenticate, leading to failed scan/identification requests out of the box.
3. **Frontend API Base URL on Android/Real Devices**: `services/api.ts` defaulted to `http://localhost:8000`. On Android emulators (`10.0.2.2`), iOS simulators, and real devices over LAN (Expo Go), hardcoded `localhost` fails to connect.
4. **Web Upload FormData Compatibility**: On Expo Web, passing `{ uri, name, type }` into `FormData` results in `[object Object]` instead of a `Blob`, causing FastAPI file validation to fail.
5. **CORS Rigidity**: FastAPI CORS configuration only permitted hardcoded `http://localhost:8081`, blocking alternate ports (e.g. 8082), LAN IPs, and emulators.
6. **Environment & Configuration Mismatches**: `backend/.env.example` had port `5433` while `docker-compose.yml` maps `5434:5432`. `Plantify_UI` was missing `.env.example` and `EXPO_PUBLIC_API_URL`.
7. **Leftover Spring Boot Files in Frontend**: Misplaced `pom.xml`, `mvnw`, `src/` in `Plantify_UI` caused clutter and confusion.

---

## User Review Required

> [!NOTE]
> For seamless local testing, the frontend will automatically provision/authenticate a default user session (`alina.smith@gmail.com`) in `services/api.ts` if no token is stored in AsyncStorage. This allows immediate use of scanning, plant care, disease diagnosis, AI chat, and cart features without an upfront login barrier.

---

## Proposed Changes

### 1. Root Orchestration & Development Workflow

#### [NEW] [package.json](file:///c:/Users/Yash/Desktop/appDev/Plantify/package.json)
Root `package.json` with npm scripts:
- `npm run dev` / `npm run dev:all`: Starts database, backend, and frontend concurrently.
- `npm run dev:backend`: Runs docker-compose up, runs migrations, seeds products, and launches uvicorn on port 8000.
- `npm run dev:frontend`: Starts Expo in `Plantify_UI`.
- `npm run db:up`: Starts PostgreSQL and Redis containers.
- `npm run db:migrate`: Runs Alembic migrations (`alembic upgrade head`).
- `npm run db:seed`: Seeds products into PostgreSQL.
- `npm test`: Runs pytest suite.

#### [NEW] [start-all.ps1](file:///c:/Users/Yash/Desktop/appDev/Plantify/start-all.ps1) & [start-all.sh](file:///c:/Users/Yash/Desktop/appDev/Plantify/start-all.sh)
One-click cross-platform scripts for Windows PowerShell and Unix that:
1. Verify Docker is running and launch PostgreSQL container on port 5434.
2. Run database migrations and seed catalog products.
3. Start backend uvicorn server in a new terminal/job.
4. Start Expo frontend server in a new terminal.

#### [NEW] [README.md](file:///c:/Users/Yash/Desktop/appDev/Plantify/README.md)
Comprehensive root documentation detailing architecture, prerequisites, quick start guide, API endpoints, environment variables, and troubleshooting.

---

### 2. Backend Enhancements

#### [MODIFY] [app/main.py](file:///c:/Users/Yash/Desktop/appDev/Plantify/backend/app/main.py)
- Enhance CORSMiddleware with `allow_origin_regex` to support localhost on any port, `127.0.0.1`, `10.0.2.2`, LAN IP addresses (`192.168.*`, `10.*`, `172.*`), and Expo origins.

#### [MODIFY] [.env.example](file:///c:/Users/Yash/Desktop/appDev/Plantify/backend/.env.example) & [README.md](file:///c:/Users/Yash/Desktop/appDev/Plantify/backend/README.md)
- Correct port from `5433`/`5432` to `5434` matching `docker-compose.yml`.
- Add explicit instructions for starting Docker PostgreSQL container.

---

### 3. Frontend Enhancements (`Plantify_UI`)

#### [MODIFY] [services/api.ts](file:///c:/Users/Yash/Desktop/appDev/Plantify/Plantify_UI/services/api.ts)
- **Dynamic API Base URL**: Auto-detect host IP via `expo-constants` and `Platform.OS` (`10.0.2.2:8000` for Android emulator, LAN IP for physical device, `localhost:8000` for web/iOS).
- **Auto-Authentication & Interceptor**: Add `ensureAuth()` and Axios request interceptor that auto-authenticates default user (`alina.smith@gmail.com`) when token is absent or expired, preventing 401 errors.
- **Web vs Native File Upload**: Support both browser `Blob` conversion on Web and `{ uri, name, type }` on React Native.
- **Complete Endpoint Coverage**: Add API methods for Product categories, catalog, cart management, AI chat agent, and full pipeline runner.

#### [MODIFY] [.env](file:///c:/Users/Yash/Desktop/appDev/Plantify/Plantify_UI/.env) & [NEW] [.env.example](file:///c:/Users/Yash/Desktop/appDev/Plantify/Plantify_UI/.env.example)
- Add `EXPO_PUBLIC_API_URL=http://localhost:8000` and clear documentation.

#### [DELETE] Leftover Spring Boot files
- Remove `pom.xml`, `mvnw`, `mvnw.cmd`, `HELP.md`, `src/`, `target/`, `.mvn/` from `Plantify_UI`.

---

## Verification Plan

### Automated Verification
1. Run backend unit & integration tests:
   ```bash
   cd backend
   .\.venv\Scripts\pytest tests/ -v
   ```
2. Verify TypeScript type check on frontend:
   ```bash
   cd Plantify_UI
   npx tsc --noEmit
   ```
3. Test backend health and API endpoints with live PostgreSQL container:
   - `GET /api/health`
   - `POST /api/auth/login` and `POST /api/auth/register`
   - `GET /api/products/categories`
   - `GET /api/products`
   - `GET /api/cart`
4. Test Alembic migration & seeding:
   ```bash
   .\.venv\Scripts\alembic upgrade head
   .\.venv\Scripts\python -m app.scripts.seed_products
   ```

### Manual Verification
1. Run `start-all.ps1` to test the single-command workflow.
2. Confirm Expo dev server launches without errors.
3. Validate that frontend API calls succeed without 401 Unauthorized errors.
