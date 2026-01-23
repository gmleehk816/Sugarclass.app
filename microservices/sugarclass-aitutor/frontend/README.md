# Sugarclass AI Tutor Frontend

A modern React-based frontend for the Sugarclass AI Tutor application with a beautiful glassmorphism UI.

## Features

- **Subject-based Tutoring**: Select from available subjects to start learning
- **AI Tutor Integration**: Intelligent tutoring system with session management
- **File Upload**: Upload documents to provide context for the AI
- **Source Citations**: View supporting evidence from materials
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Status**: Connection status indicator
- **Beautiful UI**: Glassmorphism design with smooth animations

## Prerequisites

- Node.js 18+ and npm/yarn
- Docker and Docker Compose
- Backend AI Tutor RAG Service running (see below)

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
# API URL (optional, defaults to http://localhost:8000)
VITE_API_URL=http://localhost:8000

# Gemini API Key (for direct API calls)
GEMINI_API_KEY=your_api_key_here
```

### API Proxy

The Vite dev server is configured to proxy API requests to the backend:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

## Backend API Integration

The frontend integrates with two main API endpoints:

### 1. Tutor API (`/api/tutor`)
- `POST /session/start` - Start a new tutor session
- `POST /chat` - Send a message to the tutor
- `POST /session/end` - End a tutor session
- `GET /subjects` - Get available subjects
- `GET /health` - Health check

### 2. RAG API (`/api`)
- `POST /query` - Query documents with RAG (fallback)
- `POST /query/stream` - Stream query response
- `GET /health` - Health check

## Project Structure

```
frontend/
├── components/
│   ├── FileUpload.tsx    # File upload component
│   ├── Navbar.tsx        # Navigation bar
│   └── SourceCard.tsx    # Source citation card
├── services/
│   ├── apiService.ts     # API integration layer
│   └── geminiService.ts  # Direct Gemini API calls
├── types.ts              # TypeScript type definitions
├── App.tsx              # Main application component
├── index.css             # Global styles
├── index.html            # HTML template
├── vite.config.ts        # Vite configuration
└── tsconfig.json         # TypeScript configuration
```

## Building for Production

```bash
npm run build
```

The build output will be in `dist/` directory.

## Preview Production Build

```bash
npm run preview
```

## Key Components

### App.tsx
Main application component that handles:
- Chat interface
- Subject selection
- File upload management
- Session management
- API integration with fallback logic

### apiService.ts
Service layer for API communication:
- Health checks
- Subject listing
- Session management
- Chat functionality
- Document querying

### Navbar.tsx
Navigation bar with:
- System status indicator
- Selected subject display
- Sidebar toggle
- New session button

## Deployment

### Docker Deployment

The frontend can be deployed using Docker:

```bash
# Build the image
docker build -t luminaai-frontend .

# Run the container
docker run -p 3000:3000 luminaai-frontend
```

### Nginx Deployment

For production, the frontend is typically served by Nginx. See `nginx.conf` for configuration.

## Troubleshooting

### Backend Connection Issues

If you see connection errors:
1. Ensure the backend is running: `docker-compose ps`
2. Check RAG service logs: `docker-compose logs rag_service`
3. Test API directly: `curl http://localhost:8000/health`
4. Check CORS settings in backend (already configured)
5. Verify the API proxy configuration in `vite.config.ts`

### TypeScript Errors

After installing dependencies, restart your TypeScript server:
- VS Code: Press `Cmd/Ctrl + Shift + P` → "TypeScript: Restart TS Server"

### Build Issues

If build fails:
1. Clear node_modules: `rm -rf node_modules package-lock.json`
2. Reinstall dependencies: `npm install`
3. Try clearing Vite cache: `rm -rf .vite dist`

## Development Tips

- Use browser DevTools to inspect network requests
- Check console for API errors
- The app has a 30-second health check interval
- User sessions are persisted in localStorage
- Selected subjects are saved for future visits

## License

MIT
