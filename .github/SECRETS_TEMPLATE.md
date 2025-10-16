# GitHub Secrets Configuration Template

This file lists all the secrets you need to configure in your GitHub repository for CI/CD and deployment to work properly.

## How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret listed below

---

## 🔑 Required Secrets for Deployment

### Server Access

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SSH_PRIVATE_KEY` | Private SSH key for server access | Content of `~/.ssh/llmready_deploy` |
| `SERVER_HOST` | Your server's IP address or domain | `123.45.67.89` or `server.example.com` |
| `SERVER_USER` | Username on the server | `llmready` |

### Production Configuration

| Secret Name | Description | Example |
|------------|-------------|---------|
| `PRODUCTION_DOMAIN` | Your production domain name | `llmready.com` |
| `PRODUCTION_API_URL` | Full API URL | `https://llmready.com/api` |

### Stripe Configuration

| Secret Name | Description | Example |
|------------|-------------|---------|
| `STRIPE_PUBLIC_KEY` | Stripe publishable key | `pk_live_...` |

### Email Notifications

| Secret Name | Description | Example |
|------------|-------------|---------|
| `MAIL_SERVER` | SMTP server address | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP server port | `587` |
| `MAIL_USERNAME` | SMTP username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | SMTP password or app password | `your-app-password` |
| `NOTIFICATION_EMAIL` | Email to receive notifications | `dev-team@example.com` |

---

## 📝 SSH Key Setup

**Important**: You have two options for SSH keys. See **[SSH_KEY_CLARIFICATION.md](../SSH_KEY_CLARIFICATION.md)** for detailed comparison.

### Option 1: Use Your Existing SSH Key (Simpler)

If you already have an SSH key that connects to your server:

```bash
# Display your existing private key
cat ~/.ssh/id_ed25519  # or ~/.ssh/id_rsa

# Copy the entire private key and add it to GitHub Secret: SSH_PRIVATE_KEY
# Your public key is already on the server, so you're done! ✅
```

**Pros**: Quick setup, no changes needed on server
**Cons**: Less secure for production (your personal key in GitHub)

### Option 2: Create a Dedicated SSH Key (Recommended)

Create a separate key just for GitHub Actions deployments:

```bash
# Generate a new SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deployment" -f ~/.ssh/github_actions_deploy

# Press Enter twice (no passphrase for automation)

# Display the private key (add this to SSH_PRIVATE_KEY secret)
cat ~/.ssh/github_actions_deploy

# Display the public key (add this to your server's authorized_keys)
cat ~/.ssh/github_actions_deploy.pub
```

Then add the public key to your server:
```bash
ssh your-user@your-server
echo "your-public-key-here" >> ~/.ssh/authorized_keys
```

**Pros**: More secure, better separation of concerns
**Cons**: Requires adding public key to server

---

## 📧 Gmail SMTP Configuration

If using Gmail for notifications:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Scroll down to "App passwords"
   - Generate password for "Mail"
3. **Use these settings**:
   - `MAIL_SERVER`: `smtp.gmail.com`
   - `MAIL_PORT`: `587`
   - `MAIL_USERNAME`: Your Gmail address
   - `MAIL_PASSWORD`: The 16-character app password

---

## ✅ Verification Checklist

Before running your first deployment, verify:

- [ ] All server access secrets are configured
- [ ] SSH connection works: `ssh -i ~/.ssh/llmready_deploy llmready@your-server-ip`
- [ ] Production domain points to your server
- [ ] Stripe keys are for production (pk_live_...)
- [ ] Email notifications are tested
- [ ] Server setup script has been run
- [ ] Production .env file exists on server

---

## 🔒 Security Best Practices

1. **Never commit secrets to the repository**
2. **Use separate keys for different environments**
3. **Rotate keys regularly**
4. **Use app passwords instead of account passwords**
5. **Restrict SSH key to specific IP if possible**
6. **Enable GitHub secret scanning**

---

## 🆘 Troubleshooting

### SSH Connection Issues

If deployment fails with SSH errors:

```bash
# Test SSH connection manually
ssh -i ~/.ssh/llmready_deploy llmready@your-server-ip

# Check if key has correct permissions
chmod 600 ~/.ssh/llmready_deploy

# Verify public key on server
ssh llmready@your-server-ip "cat ~/.ssh/authorized_keys"
```

### Email Notification Issues

If you're not receiving emails:

1. Check spam/junk folder
2. Verify MAIL_* secrets are correct
3. Test SMTP connection manually:
   ```bash
   telnet smtp.gmail.com 587
   ```
4. Ensure app password (not regular password) is used for Gmail

### Stripe Key Issues

Make sure you're using the correct keys:
- **Production**: Use `pk_live_...` and `sk_live_...`
- **Testing**: Use `pk_test_...` and `sk_test_...`

Find your keys at: https://dashboard.stripe.com/apikeys

---

## 📚 Additional Resources

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [SSH Key Generation Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [Stripe API Keys](https://stripe.com/docs/keys)