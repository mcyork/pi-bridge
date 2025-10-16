# Pi Bridge - Enhanced Raspberry Pi Management Tool

A CLI tool for managing multiple Raspberry Pi devices over SSH with automatic Pi detection through symlinks.

## 📦 Installation

Before using the tool, install the required Python dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `paramiko` - SSH library for Python
- `PyYAML` - YAML configuration file parser
- `cryptography` - For SSH key generation

## 🚀 Quick Start

### Option 1: SSH Key Authentication (Recommended)

1.  **Configure a Pi with automatic key setup:**
    ```bash
    ./pi_bridge add pi1 --host 192.168.1.10 --user pi --password raspberry --push-key
    ```
    This will:
    - Generate an SSH key pair at `~/.ssh/pi-bridge` (if it doesn't exist)
    - Push the public key to the Pi for password-less authentication
    - Save the configuration to `config.yml` with the key path
    - Create a `./pi1` symlink for easy access
    
    **Benefits:** No passwords stored in config, more secure, no password prompts!

### Option 2: Password Authentication

1.  **Configure a Pi with password:**
    ```bash
    ./pi_bridge add pi1 --host 192.168.1.10 --user pi --password raspberry
    ```
    This command saves the new Pi to `config.yml` and creates a `./pi1` symlink for easy access.
    
    **Note:** Password will be stored in plain text in `config.yml`.

2.  **Check its status:**
    ```bash
    ./pi_bridge status pi1
    ```

3.  **Run a command:**
    ```bash
    # Use the symlink
    ./pi1 run "uname -a"

    # Or use the main tool
    ./pi_bridge run "uname -a" --pi pi1
    ```

4.  **Add to PATH (Optional but Recommended):**
    
    Adding the `scripts` directory to your PATH allows you to run commands from anywhere without `./`:
    
    ```bash
    # Add this line to your ~/.zshrc (Mac) or ~/.bashrc (Linux)
    export PATH="$PATH:/Users/yourusername/projects/pi-bridge/scripts"
    
    # Then reload your shell configuration
    source ~/.zshrc  # or source ~/.bashrc
    ```
    
    After adding to PATH, you can run commands like:
    ```bash
    pi1 run "uname -a"           # Instead of ./pi1 run "uname -a"
    pi_bridge list               # Instead of ./pi_bridge list
    ```
    
    This is especially useful for LLM assistants, as they can run commands without worrying about the tool's location.

## 🔧 Available Commands

The tool is organized into sub-commands for different actions.

### Core Actions (`run`, `read`, `write`)

These commands perform actions on a target Pi.

-   `run <command>`: Execute a shell command.
-   `run-stream <command>`: Stream output from a long-running command.
-   `read <remote_path>`: Read a file from the Pi.
-   `write <remote_path> <content>`: Write content to a file.

**Example:**
```bash
# Reboot pi2
./pi2 run "sudo reboot"

# Read the hostname from the default pi
./pi_bridge read "/etc/hostname"
```

### Management Actions (`add`, `remove`, `list`, `status`, `set-default`)

These commands help you manage your list of Pis.

-   `add <name> --host <host> --user <user> --password <password> [--push-key]`: Add a new Pi. Creates a symlink.
    - Use `--push-key` to automatically set up SSH key authentication (recommended - password used once to push key, then not stored)
    - Without `--push-key`, password is stored in config for ongoing authentication (less secure)
-   `remove <name>`: Remove a Pi. Deletes the symlink.
-   `list`: Show all configured Pis in a table.
-   `set-default <name>`: Set the default Pi for commands.
-   `status [name]`: Check connectivity and get the hostname for one or all Pis.

**Example:**
```bash
# See all configured Pis
./pi_bridge list

# Check if all Pis are online
./pi_bridge status

# Add a new Pi named 'pi-hole' with SSH key authentication (recommended)
./pi_bridge add pi-hole --host 192.168.1.20 --user admin --password raspberry --push-key

# Or add with password authentication only
./pi_bridge add pi-hole --host 192.168.1.20 --user admin --password raspberry

# Set it as the default
./pi_bridge set-default pi-hole
```

## ⚙️ Configuration (`config.yml`)

Device details are stored in `config.yml`. While you can edit it manually, it's recommended to use the `add` and `remove` commands.

**Note:** You can mix and match authentication methods - some Pis can use SSH keys while others use passwords.

### Example:
```yaml
pi1:
  host: 192.168.1.10
  user: pi
  key: /Users/yourusername/.ssh/pi-bridge  # SSH key authentication (recommended)
pi2:
  host: 192.168.1.20
  user: pi
  password: raspberry  # Password authentication
default: pi1
```

## 🔑 SSH Key Authentication

The tool can automatically set up SSH key-based authentication, which is more secure and convenient than passwords.

### How It Works:
1. When you use `--push-key` with the `add` command, the tool:
   - Generates an ED25519 SSH key pair at `~/.ssh/pi-bridge` (if it doesn't exist)
   - Connects to the Pi using the provided password (one time only)
   - Copies the public key to the Pi's `~/.ssh/authorized_keys`
   - Saves the key path in `config.yml`

2. All future connections use the SSH key automatically - no password needed!

### Benefits:
- ✅ **More Secure:** No passwords stored in plain text
- ✅ **Convenient:** No password prompts during operations
- ✅ **One Key for All:** Same key can be used for all your Pis
- ✅ **LLM-Friendly:** No interactive password prompts when used by AI assistants

### Manual Key Setup:
If you prefer to use your own SSH key:
```bash
./pi_bridge add pi1 --host 192.168.1.10 --user pi --key ~/.ssh/id_rsa
```

## 🎯 How It Works

The tool determines which Pi to connect to in the following order of priority:
1.  The `--pi <name>` command-line argument.
2.  The name of the symlink used to execute the script (e.g., `./pi1`).
3.  The `default` entry in `config.yml`.

## 🆘 Troubleshooting

-   **Connection Errors:** Use `./pi_bridge status` to check connectivity. Ensure the host IP is correct and the device is on the network.
-   **Host Key Errors:** If you see a "BadHostKeyException", it means the Pi's SSH key has changed (e.g., after an OS reinstall). The tool will provide you with the correct `ssh-keygen -R <host>` command to run to fix it.
-   **Authentication Errors:** If you don't store a password in the config, the tool will prompt you for one. For non-interactive use, consider setting up SSH key-based authentication and providing the key path in `config.yml`.

## 📋 Requirements

-   Python 3.6+
-   paramiko (SSH library)
-   PyYAML
-   SSH access to your Raspberry Pis

## ⚠️ Things to Consider

**Password Security:**
- Passwords stored in `config.yml` are **not encrypted**. They are saved in plain text.
- This tool is designed for development environments with Raspberry Pis, typically using default passwords like "raspberry".
- If you plan to use this tool with production Linux machines or systems with sensitive credentials, be aware that there is no encryption on the YAML configuration file.
- For better security in production environments, consider using SSH key-based authentication instead (use the `--key` parameter when adding a Pi).

## 🤖 AI Disclosure

AI was used to help write this code, specifically the tool [Cursor](https://cursor.com), which assisted with development, documentation, and code organization.

