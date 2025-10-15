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

## 🚀 Quick Start

1.  **Configure a Pi:**
    ```bash
    ./pi_bridge add pi1 --host 192.168.1.10 --user pi --password raspberry
    ```
    This command saves the new Pi to `config.yml` and creates a `./pi1` symlink for easy access.

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

-   `add <name> --host <host> --user <user> --password <password>`: Add a new Pi. Creates a symlink.
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

# Add a new Pi named 'pi-hole'
./pi_bridge add pi-hole --host 192.168.1.20 --user admin --password raspberry

# Set it as the default
./pi_bridge set-default pi-hole
```

## ⚙️ Configuration (`config.yml`)

Device details are stored in `config.yml`. While you can edit it manually, it's recommended to use the `add` and `remove` commands.

```yaml
pi1:
  host: 192.168.1.10
  user: pi
  password: raspberry
pi-hole:
  host: 192.168.1.20
  user: admin
  password: raspberry
default: pi-hole
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

