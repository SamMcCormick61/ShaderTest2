# Setting up SSH keys for GitHub on Raspberry Pi

This guide explains how to generate and configure SSH keys on your Raspberry Pi for use with GitHub.

## Prerequisites

- A Raspberry Pi running Raspberry Pi OS (or another Debian-based distribution).
- Internet connectivity.
- A GitHub account.

## 1. Install OpenSSH Client (if not already installed)

Open a terminal on your Pi and run:
```bash
sudo apt update
sudo apt install -y openssh-client
```

## 2. Check for existing SSH keys

Before generating a new key, check if you already have one:
```bash
ls -al ~/.ssh
```

## 3. Generate a new SSH key

Use the Ed25519 algorithm (recommended) or RSA if Ed25519 is unavailable:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```
or
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

- Press Enter to accept the default file location (e.g., `/home/pi/.ssh/id_ed25519`).
- Optionally enter a passphrase for added security, or leave it empty.

## 4. Start the SSH agent and add your key

```bash
 eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## 5. Add your SSH key to your GitHub account

1. Copy the public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
   Then select and copy the output.

2. On GitHub:
   - Go to **Settings** > **SSH and GPG keys**.
   - Click **New SSH key**.
   - Add a descriptive title (e.g., "Raspberry Pi"), paste the key, and click **Add SSH key**.

## 6. Test the SSH connection

```bash
ssh -T git@github.com
```
You should see a message like:
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

## 7. Use SSH for Git operations

- Clone a repository:
  ```bash
git clone git@github.com:username/repo.git
```
- Or update an existing remote to SSH:
  ```bash
git remote set-url origin git@github.com:username/repo.git
```

You are now set up to use SSH with GitHub on your Raspberry Pi!
