# Update Deployment SSH for New User

Since you removed root access, you need to update GitHub Actions to use your new user.

## 🔧 What to Update

### 1. Create SSH Key for New User

On your server:
```bash
# Switch to your new user
su - ebadarou  # (or your username)

# Create .ssh directory if doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy
# Press Enter for no passphrase (for automation)

# Add to authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Display private key (you'll need this for GitHub)
cat ~/.ssh/github_deploy
```

### 2. Update GitHub Secrets

Go to: https://github.com/YOUR_REPO/settings/secrets/actions

Update these secrets:

**SSH_PRIVATE_KEY:**
- Copy the ENTIRE output from `cat ~/.ssh/github_deploy`
- Include `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`

**SERVER_USER:**
- Change from: `root`
- To: `ebadarou` (your actual username)

**SERVER_HOST:** (should stay same)
- Your server IP or domain

---

### 3. Update User Permissions

Your new user needs sudo access for deployment commands:

```bash
# Add to sudoers
sudo visudo

# Add this line (replace ebadarou with your username):
ebadarou ALL=(ALL) NOPASSWD: /bin/systemctl restart llmready-backend, /bin/systemctl restart llmready-celery-worker, /bin/systemctl reload nginx, /bin/mkdir, /bin/chown, /bin/chmod, /bin/tar, /bin/mv
```

This allows deployment script to restart services without password.

---

### 4. Test SSH Connection

From your local machine:
```bash
# Test new SSH key works
ssh -i path/to/github_deploy ebadarou@your-server "echo 'SSH works'"

# Should connect without password
```

---

### 5. Test Deployment

```bash
./scripts/deploy.sh
```

Should now deploy using new user!

---

## ⚠️ Alternative: Deploy User

Instead of your personal user, you could create dedicated `deploy` user:

```bash
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy
# Then use deploy user for deployments
```

This is cleaner for production.

---

**Choose:** Update personal user OR create deploy user, then update GitHub secrets! 🚀