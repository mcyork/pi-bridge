# Uninstalling Pi-Bridge

## Quick Uninstall

```bash
pip uninstall pi-shell
```

This removes the `pi-shell` command and Python package.

## What Gets Left Behind

When you uninstall, these files remain on your system:

### 1. **Configuration File**
- Location: `~/.config/pi-shell/config.yml`
- Contains: Your Pi configurations (hosts, users, passwords/keys)
- Why kept: Preserves your settings if you reinstall

### 2. **SSH Keys**
- Location: `~/.ssh/pi-shell` and `~/.ssh/pi-shell.pub`
- Contains: Your SSH key pair for Pi authentication
- Why kept: Still valid on remote Pis, needed if you reinstall

### 3. **Symlinks**
- Location: `/usr/local/bin/keybird`, `/usr/local/bin/pi1`, etc.
- Contains: Command shortcuts to pi-shell
- Why kept: Harmless, and may be used by other users (multi-user systems)

### 4. **Remote SSH Keys**
- Location: On your Pis at `~/.ssh/authorized_keys`
- Contains: Your public key entries
- Why kept: On remote systems, can't be auto-removed

## Complete Cleanup (Optional)

If you want to completely remove all traces:

### Remove Configuration
```bash
rm -rf ~/.config/pi-shell/
```

### Remove SSH Keys (Local)
```bash
rm ~/.ssh/pi-shell ~/.ssh/pi-shell.pub
```

### Remove Symlinks
```bash
# List all pi-shell symlinks
ls -la /usr/local/bin/ | grep pi-shell

# Remove specific symlinks
rm /usr/local/bin/keybird
rm /usr/local/bin/pi1
# ... etc

# Or remove all at once (be careful!)
find /usr/local/bin -lname '*pi-shell' -delete
```

### Remove SSH Keys from Remote Pis (Manual)

You'll need to manually remove the public key from each Pi:

```bash
# SSH into each Pi
ssh pi@192.168.1.10

# Edit authorized_keys
nano ~/.ssh/authorized_keys

# Remove the line containing: "pi-shell-tool"
# Save and exit
```

Or use this one-liner per Pi:
```bash
ssh pi@192.168.1.10 "sed -i '/pi-shell-tool/d' ~/.ssh/authorized_keys"
```

## Reinstalling Later

If you reinstall pi-shell:
- ✅ Your config will be automatically detected
- ✅ Your SSH keys will still work
- ✅ No need to reconfigure everything

## Keeping Config But Removing Package

If you want to temporarily remove the package but keep settings:

```bash
pip uninstall pi-shell
# Your config stays at ~/.config/pi-shell/

# Later, reinstall:
pip install pi-shell
# Everything still works!
```

## Multi-User Considerations

On shared systems:
- Each user has their own config in `~/.config/pi-shell/`
- Each user has their own SSH keys in `~/.ssh/`
- Symlinks in `/usr/local/bin/` are shared
- **Don't delete symlinks if other users might be using pi-shell!**

## Clean Uninstall Script

Here's a script for complete removal:

```bash
#!/bin/bash
# complete-uninstall.sh

echo "This will completely remove pi-shell and all data."
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    # Uninstall package
    pip uninstall -y pi-shell
    
    # Remove config
    rm -rf ~/.config/pi-shell/
    
    # Remove SSH keys
    rm -f ~/.ssh/pi-shell ~/.ssh/pi-shell.pub
    
    # List symlinks (don't auto-delete for safety)
    echo ""
    echo "Symlinks found (review before deleting):"
    find /usr/local/bin -lname '*pi-shell' 2>/dev/null
    
    echo ""
    echo "To remove symlinks manually:"
    echo "  find /usr/local/bin -lname '*pi-shell' -delete"
    
    echo ""
    echo "✅ Pi-bridge uninstalled"
    echo "⚠️  SSH keys remain on remote Pis (remove manually if needed)"
else
    echo "Uninstall cancelled"
fi
```

## Need Help?

If you're uninstalling because of issues:
- Check [Troubleshooting](../README.md#-troubleshooting) in the README
- Open an [issue](https://github.com/mcyork/pi-shell/issues)
- Maybe we can help fix it instead!

