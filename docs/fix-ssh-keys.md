# Fix SSH Keys Script

> **Note:** This is a legacy bash script. If you've installed pi-bridge via pip, use the built-in command instead:
> ```bash
> pi-bridge check-ssh
> ```
> The built-in command works with the new config system and is cross-platform.

## Overview

`fix-ssh-keys.sh` is a legacy utility script that automates fixing SSH host key fingerprint issues when you've reinstalled the OS on a Raspberry Pi or when the Pi's SSH keys have changed.

## The Problem It Solves

When you reinstall Raspberry Pi OS or flash a new SD card, the SSH host keys change. SSH detects this and refuses to connect, showing an error like:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
```

This is a security feature to prevent man-in-the-middle attacks, but it's inconvenient when you know the change is legitimate.

## What It Does

The script automates the following steps:

1. **Validates Environment**
   - Checks that it's being run from the pi-shell directory (looks for `config.yml`)

2. **Reads Configuration**
   - Extracts the default Pi name from your `config.yml`
   - Retrieves the host IP and username for that Pi

3. **Clears Old SSH Key**
   - Runs `ssh-keygen -R <host>` to remove the old SSH host key from `~/.ssh/known_hosts`
   - This prevents the "REMOTE HOST IDENTIFICATION HAS CHANGED" error

4. **Establishes New Connection**
   - Connects to the Pi with `StrictHostKeyChecking=no` to automatically accept the new key
   - Tests the connection by running a simple echo command
   - Reports success or failure with color-coded output

## Usage

```bash
./fix-ssh-keys.sh
```

The script will:
- Use the **default Pi** configured in your `config.yml`
- Display status messages in color as it progresses
- Automatically accept the new SSH key fingerprint
- Verify the connection works

## Requirements

- Must be run from the pi-shell directory (where `config.yml` is located)
- A default Pi must be configured in `config.yml`
- `ssh-keygen` must be available on your system (standard on macOS/Linux)

## Example Output

```
[INFO] Default Pi is: pi1
[INFO] Target: pi@192.168.1.10
[INFO] Clearing old SSH key fingerprint for 192.168.1.10...
[SUCCESS] Old SSH key cleared
[INFO] Testing SSH connection to establish new key fingerprint...
[WARNING] You may be prompted to accept the new SSH key fingerprint
[WARNING] Type 'yes' when prompted to continue
[SUCCESS] SSH connection established and new key fingerprint accepted!
[SUCCESS] SSH key fingerprint issue resolved for pi1
[INFO] You can now run deployment scripts without SSH key issues
```

## When to Use This Script

- After reinstalling Raspberry Pi OS
- After flashing a new SD card
- When you see SSH host key verification errors
- After the `pi-bridge check-ssh` command reports "BAD KEY"

## Limitations

- Only works with the **default Pi** configured in `config.yml`
- Does not support specifying a different Pi as a parameter

## Alternative Approach

You can also use the built-in `pi-bridge` command:

```bash
pi-bridge check-ssh
```

This command checks all Pis and interactively prompts you to fix any host key issues.

