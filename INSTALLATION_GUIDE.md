# 🔧 Week 1 Installation Guide

## Prerequisites Installation for macOS

You need to install **Docker** and **PostgreSQL** before we can proceed with the backend setup.

---

## Step 1: Install Docker Desktop (Required)

Docker Desktop includes everything we need for running PostgreSQL and Redis in containers.

### Installation Commands

```bash
# Install Docker Desktop via Homebrew
brew install --cask docker

# After installation completes, open Docker Desktop from Applications
# Wait for Docker to start (you'll see the Docker icon in your menu bar)
```

### Verify Installation

```bash
# This should show Docker version (run after Docker Desktop starts)
docker --version
docker compose version
```

**⏱️ Time**: ~5-10 minutes (including download)

---

## Step 2: Install PostgreSQL 15 (Optional but Recommended)

While we'll run PostgreSQL in Docker for development, having the `psql` client installed locally is useful for debugging.

### Installation Commands

```bash
# Install PostgreSQL 15
brew install postgresql@15

# Add to PATH (add this to your ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Verify Installation

```bash
# This should show PostgreSQL version
psql --version
```

**⏱️ Time**: ~3-5 minutes

---

## Step 3: Verify Your Installation

After installing both, run these commands:

```bash
# Check Docker
docker --version
# Expected: Docker version 24.x.x or higher

# Check PostgreSQL client
psql --version
# Expected: psql (PostgreSQL) 15.x

# Check Docker is running
docker ps
# Expected: Empty list (no containers running yet)
```

---

## What's Next?

Once you've completed these installations:

1. ✅ Docker Desktop is running (you see the whale icon in your menu bar)
2. ✅ `docker --version` works
3. ✅ (Optional) `psql --version` works

**Then notify me and we'll continue with:**
- Creating the backend directory structure
- Setting up Docker Compose for PostgreSQL & Redis
- Creating the FastAPI application
- Defining database models
- Running migrations

---

## Troubleshooting

### Docker Desktop won't start
- Make sure you have enough disk space (at least 10GB free)
- Check System Preferences → Security & Privacy for any blocked applications
- Try restarting your Mac

### Homebrew issues
```bash
# Update Homebrew first
brew update
brew upgrade
```

### PATH issues with PostgreSQL
```bash
# Manually add to PATH for current session
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
```

---

## Estimated Total Time

- **Docker Desktop**: 5-10 minutes
- **PostgreSQL**: 3-5 minutes  
- **Verification**: 2 minutes
- **Total**: ~10-15 minutes

Once installed, we'll spend ~2 hours setting up the complete backend foundation! 🚀