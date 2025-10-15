# 🎨 LLMReady Frontend - React + Vite + TypeScript

**Status**: Week 8-9 Implementation In Progress  
**Framework**: React 18 + Vite + TypeScript + Tailwind CSS

---

## 📦 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/         # Buttons, Inputs, Cards, etc.
│   │   └── layouts/        # DashboardLayout, etc.
│   ├── pages/              # Page components
│   │   ├── LandingPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── WebsitesPage.tsx
│   │   ├── GenerationsPage.tsx
│   │   └── SubscriptionPage.tsx
│   ├── store/              # Zustand state management
│   │   └── authStore.ts
│   ├── lib/                # Utilities and API client
│   │   └── api.ts
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   ├── App.tsx             # Main app with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

---

## 🛠️ Tech Stack

### Core
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **TypeScript** - Type safety
- **React Router v6** - Routing

### State Management
- **Zustand** - Lightweight state management
- **TanStack Query** - Server state management

### Styling
- **Tailwind CSS** - Utility-first CSS
- **Custom Design System** - Dark theme with purple accent

### HTTP Client
- **Axios** - API requests with interceptors
- JWT token refresh
- Automatic error handling

---

## 📁 Key Files Explained

### `src/lib/api.ts`
- Axios instance configuration
- JWT token interceptors
- Automatic token refresh on 401
- Error handling utilities

### `src/store/authStore.ts`
- Authentication state management
- Login/logout/register actions
- Token persistence in localStorage
- User session management

### `src/types/index.ts`
- TypeScript type definitions
- API request/response types
- Matches backend schema exactly

### `src/App.tsx`
- Main application component
- Route configuration
- Protected route wrapper
- Layout structure

---

## 🎨 Design System

### Colors (Tailwind)
```css
Primary: purple (primary-500 = #8b5cf6)
Background: gray-950 (very dark)
Cards: gray-900
Borders: gray-800
Text: gray-50
Muted: gray-500
```

### Components
- All use dark theme
- Consistent spacing and borders
- Hover effects and transitions
- Responsive by default

---

## 🔐 Authentication Flow

```
1. User enters credentials
   ↓
2. POST /api/v1/auth/login (form-urlencoded)
   ↓
3. Receive access_token + refresh_token
   ↓
4. Store tokens in localStorage
   ↓
5. Set Authorization header on all requests
   ↓
6. On 401 error, try refresh
   ↓
7. If refresh fails, redirect to login
```

---

## 📋 Available Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

---

## 🧪 Testing the Setup

### 1. Check if server runs
```bash
npm run dev
# Should see: Local: http://localhost:3000/
```

### 2. Verify API proxy
- Backend must be running on port 8000
- Vite proxies `/api` requests to `http://localhost:8000`

### 3. Test authentication
1. Navigate to `/register`
2. Create account
3. Should redirect to dashboard
4. Token should persist on refresh

---

## 🔧 Configuration Files

### `vite.config.ts`
- Path aliases (`@/` → `./src/`)
- API proxy configuration
- Port 3000 for dev server

### `tailwind.config.js`
- Custom purple color palette
- Inter font family
- Dark theme defaults

### `tsconfig.json`
- Strict TypeScript settings
- Path mapping for imports
- React JSX transform

---

## 📡 API Integration

### API Client Usage

```typescript
import { api } from '@/lib/api'

// GET request
const response = await api.get('/api/v1/websites')

// POST request
const response = await api.post('/api/v1/websites', {
  url: 'https://example.com',
  name: 'Example Site'
})

// Tokens are automatically added to headers
// Token refresh is automatic on 401
```

### State Management

```typescript
import { useAuthStore } from '@/store/authStore'

function MyComponent() {
  const { user, login, logout } = useAuthStore()
  
  // Access current user
  console.log(user?.email)
  
  // Login
  await login({ email: '...', password: '...' })
  
  // Logout
  logout()
}
```

---

## 🎯 Development Workflow

### Adding a New Page

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Use protected route wrapper if needed

### Adding a New API Endpoint

1. Add types to `src/types/index.ts`
2. Create service function or use inline
3. Use TanStack Query for data fetching

### Adding a New Component

1. Create in `src/components/common/`
2. Use Tailwind classes
3. Make it reusable and typed

---

## 🐛 Common Issues

### "Module not found" errors
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### TypeScript errors in IDE
```bash
# Restart TypeScript server
# VS Code: Cmd+Shift+P → "TypeScript: Restart TS Server"
```

### API not connecting
1. Check backend is running on port 8000
2. Verify VITE_API_URL in .env
3. Check browser console for CORS errors

### Tokens not persisting
1. Check localStorage in browser DevTools
2. Verify authStore.checkAuth() runs on mount
3. Check token expiration

---

## 📚 Next Steps

### Week 8 Remaining Tasks
- [ ] Create reusable UI components
- [ ] Build authentication pages
- [ ] Implement landing page
- [ ] Add form validation

### Week 9 Tasks
- [ ] Dashboard with stats
- [ ] Website management pages
- [ ] Generation tracking UI
- [ ] Subscription management

---

## 🎉 Ready to Code!

The frontend foundation is complete. You can now start building pages and components!

```bash
# Start development
npm run dev

# Start backend (in separate terminal)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Visit `http://localhost:3000` 🚀