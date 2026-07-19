# Project Zeus

## Sprint 1.1: Foundation Bootstrap

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- Rust (for Tauri build)

### Setup
1. Install root dependencies:
   ```bash
   npm install
   ```
2. Install desktop dependencies:
   ```bash
   cd apps/desktop
   npm install
   ```
3. Install backend dependencies:
   ```bash
   cd apps/backend
   pip install -r requirements.txt
   ```

### Running the application (Development)
From the root directory, run:
```bash
npm run dev
```
This will start both the FastAPI backend and the Tauri desktop app concurrently.
