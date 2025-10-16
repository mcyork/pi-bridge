# Uninstalling Pi-Bridge

## Quick Uninstall

```bash
pip uninstall pi-bridge
```

This removes the `pi-bridge` command and Python package.

## What Gets Left Behind

When you uninstall, these files remain on your system:

### 1. **Configuration File**
- Location: `~/.config/pi-bridge/config.yml`
- Contains: Your Pi configurations (hosts, users, passwords/keys)
- Why kept: Preserves your settings if you reinstall

### 2. **SSH Keys**
- Location: `~/.ssh/pi-bridge` and `~/.ssh/pi-bridge.pub`
- Contains: Your SSH key pair for Pi authentication
- Why kept: Still valid on remote Pis, needed if you reinstall

### 3. **Symlinks**
- Location: `/usr/local/bin/keybird`, `/usr/local/bin/pi1`, etc.
- Contains: Command shortcuts to pi-bridge
- Why kept: Harmless, and may be used by other users (multi-user systems)

### 4. **Remote SSH Keys**
- Location: On your Pis at `~/.ssh/authorized_keys`
- Contains: Your public key entries
- Why kept: On remote systems, can't be auto-removed

## Complete Cleanup (Optional)

If you want to completely remove all traces:

### Remove Configuration
```bash
rm -rf ~/.config/pi-bridge/
```

### Remove SSH Keys (Local)
```bash
rm ~/.ssh/pi-bridge ~/.ssh/pi-bridge.pub
```

### Remove Symlinks
```bash
# List all pi-bridge symlinks
ls -la /usr/local/bin/ | grep pi-bridge

# Remove specific symlinks
rm /usr/local/bin/keybird
rm /usr/local/bin/pi1
# ... etc

# Or remove all at once (be careful!)
find /usr/local/bin -lname '*pi-bridge' -delete
```

### Remove SSH Keys from Remote Pis (Manual)

You'll need to manually remove the public key from each Pi:

```bash
# SSH into each Pi
ssh pi@192.168.1.10

# Edit authorized_keys
nano ~/.ssh/authorized_keys

# Remove the line containing: "pi-bridge-tool"
# Save and exit
```

Or use this one-liner per Pi:
```bash
ssh pi@192.168.1.10 "sed -i '/pi-bridge-tool/d' ~/.ssh/authorized_keys"
```

## Reinstalling Later

If you reinstall pi-bridge:
- ✅ Your config will be automatically detected
- ✅ Your SSH keys will still work
- ✅ No need to reconfigure everything

## Keeping Config But Removing Package

If you want to temporarily remove the package but keep settings:

```bash
pip uninstall pi-bridge
# Your config stays at ~/.config/pi-bridge/

# Later, reinstall:
pip install pi-bridge
# Everything still works!
```

## Multi-User Considerations

On shared systems:
- Each user has their own config in `~/.config/pi-bridge/`
- Each user has their own SSH keys in `~/.ssh/`
- Symlinks in `/usr/local/bin/` are shared
- **Don't delete symlinks if other users might be using pi-bridge!**

## Clean Uninstall Script

Here's a script for complete removal:

```bash
#!/bin/bash
# complete-uninstall.sh

echo "This will completely remove pi-bridge and all data."
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    # Uninstall package
    pip uninstall -y pi-bridge
    
    # Remove config
    rm -rf ~/.config/pi-bridge/
    
    # Remove SSH keys
    rm -f ~/.ssh/pi-bridge ~/.ssh/pi-bridge.pub
    
    # List symlinks (don't auto-delete for safety)
    echo ""
    echo "Symlinks found (review before deleting):"
    find /usr/local/bin -lname '*pi-bridge' 2>/dev/null
    
    echo ""
    echo "To remove symlinks manually:"
    echo "  find /usr/local/bin -lname '*pi-bridge' -delete"
    
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
- Open an [issue](https://github.com/mcyork/pi-bridge/issues)
- Maybe we can help fix it instead!

