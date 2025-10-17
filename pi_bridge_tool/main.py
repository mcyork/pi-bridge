import argparse
import getpass
import paramiko
import yaml
import os
import sys
import time
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class PiBridge:
    def __init__(self, host, user="pi", password=None, key_filename=None):
        self.host = host
        self.user = user
        self.password = password
        self.key_filename = key_filename
        self.client = None
        self.sftp = None

    def connect(self, timeout=5):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                self.host,
                username=self.user,
                password=self.password,
                key_filename=self.key_filename,
                timeout=timeout,
            )
            self.sftp = self.client.open_sftp()
            return True
        except paramiko.ssh_exception.BadHostKeyException as e:
            # Re-raise the exception to be handled by the caller
            raise e
        except Exception:
            return False

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    def run(self, command):
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

    def run_stream(self, command):
        """
        Run a command and stream the output in real-time.
        This is useful for long-running commands like deployment scripts.
        """
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")

        stdin, stdout, stderr = self.client.exec_command(command)

        # Set non-blocking mode
        stdout.channel.setblocking(0)
        stderr.channel.setblocking(0)

        # Stream output in real-time
        while True:
            # Check if command is still running
            if stdout.channel.exit_status_ready():
                break

            # Read stdout
            if stdout.channel.recv_ready():
                output = stdout.channel.recv(1024).decode("utf-8", errors="ignore")
                if output:
                    print(output, end="", flush=True)

            # Read stderr
            if stderr.channel.recv_stderr_ready():
                error = stderr.channel.recv_stderr(1024).decode(
                    "utf-8", errors="ignore"
                )
                if error:
                    print(f"ERROR: {error}", end="", flush=True, file=sys.stderr)

            # Small delay to prevent busy waiting
            time.sleep(0.1)

        # Get final exit status
        exit_status = stdout.channel.recv_exit_status()

        # Read any remaining output
        remaining_stdout = stdout.read().decode("utf-8", errors="ignore")
        remaining_stderr = stderr.read().decode("utf-8", errors="ignore")

        if remaining_stdout:
            print(remaining_stdout, end="", flush=True)
        if remaining_stderr:
            print(f"ERROR: {remaining_stderr}", end="", flush=True, file=sys.stderr)

        return exit_status

    def read(self, path):
        if not self.sftp:
            raise RuntimeError("Not connected. Call connect() first.")
        with self.sftp.open(path, "r") as f:
            return f.read().decode()

    def write(self, path, content):
        if not self.sftp:
            raise RuntimeError("Not connected. Call connect() first.")
        with self.sftp.open(path, "w") as f:
            f.write(content)

    def upload_file(self, local_path, remote_path):
        if not self.sftp:
            raise RuntimeError("Not connected. Call connect() first.")
        self.sftp.put(local_path, remote_path)


def detect_pi_from_symlink():
    """
    Detect which Pi to use based on the symlink name.
    Returns the Pi identifier (e.g., 'pi1', 'keybird') or None if not a symlink.
    """
    try:
        # Get the actual script path (resolving symlinks)
        script_path = os.path.realpath(sys.argv[0])
        script_name = os.path.basename(script_path)

        # Get the symlink name (what the user actually called)
        symlink_name = os.path.basename(sys.argv[0])

        # If they're different, we're running from a symlink
        # The symlink name is the Pi identifier
        if script_name != symlink_name and script_name == "pi-shell":
            return symlink_name

        return None
    except Exception:
        return None


def get_config_path(args):
    if args.config:
        return Path(args.config)
    # Default config path in user's home directory
    # This ensures each user has their own config, even with system-wide installation
    return Path.home() / ".config" / "pi-shell" / "config.yml"


def load_config(config_path):
    cfg_file = Path(config_path)
    if not cfg_file.exists():
        # Create an empty config if it doesn't exist
        empty_config = {}
        save_config(config_path, empty_config)
        print(f"Created empty config file at {config_path}")
        print(f"Use 'pi-shell add' to add your first Pi.")
        return empty_config
    with open(cfg_file, "r") as f:
        return yaml.safe_load(f) or {}


def save_config(config_path, config):
    # Ensure config directory exists
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_pi_bridge_key_path():
    """Get the path to the pi-shell SSH key"""
    return Path.home() / ".ssh" / "pi-shell"


def generate_pi_bridge_key():
    """Generate SSH key pair for pi-shell using cryptography library"""
    key_path = get_pi_bridge_key_path()

    # Check if key already exists
    if key_path.exists():
        print(f"SSH key already exists at {key_path}")
        return str(key_path)

    # Ensure .ssh directory exists
    ssh_dir = key_path.parent
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    print(f"Generating SSH key pair for pi-shell...")

    # Generate ED25519 key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(key_path, "wb") as f:
        f.write(private_pem)
    key_path.chmod(0o600)

    # Save public key in OpenSSH format
    public_openssh = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    pub_key_path = Path(str(key_path) + ".pub")
    with open(pub_key_path, "wb") as f:
        f.write(public_openssh + b" pi-shell-tool\n")
    pub_key_path.chmod(0o644)

    print(f"✅ Generated SSH key pair:")
    print(f"   Private: {key_path}")
    print(f"   Public:  {pub_key_path}")

    return str(key_path)


def push_ssh_key_to_pi(host, user, password, key_path):
    """Push public key to Pi's authorized_keys using paramiko"""
    pub_key_path = Path(str(key_path) + ".pub")

    # Read the public key
    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()

    print(f"Pushing SSH key to {user}@{host}...")

    # Connect with password
    bridge = PiBridge(host=host, user=user, password=password)
    if not bridge.connect():
        print(f"❌ Could not connect to {host}", file=sys.stderr)
        return False

    try:
        # Create .ssh directory if it doesn't exist
        bridge.run("mkdir -p ~/.ssh")
        bridge.run("chmod 700 ~/.ssh")

        # Create authorized_keys if it doesn't exist
        bridge.run("touch ~/.ssh/authorized_keys")
        bridge.run("chmod 600 ~/.ssh/authorized_keys")

        # Check if key already exists to avoid duplicates
        out, _ = bridge.run(
            f'grep -F "{pub_key.split()[0]}" ~/.ssh/authorized_keys 2>/dev/null || echo "not_found"'
        )

        if "not_found" in out:
            # Append public key to authorized_keys
            bridge.run(f'echo "{pub_key}" >> ~/.ssh/authorized_keys')
            print(f"✅ SSH key added to {host}")
        else:
            print(f"ℹ️  SSH key already exists on {host}")

        return True
    except Exception as e:
        print(f"❌ Error pushing key: {e}", file=sys.stderr)
        return False
    finally:
        bridge.close()


def handle_add(args):
    config_path = get_config_path(args)
    config = load_config(config_path)
    if args.name in config:
        print(f"Warning: Pi '{args.name}' already exists. Overwriting.")

    # Handle --push-key flag
    key_to_use = args.key
    if args.push_key:
        # Generate or get existing pi-shell key
        key_to_use = generate_pi_bridge_key()

        # Need password to push the key
        password_for_push = args.password
        if not password_for_push:
            try:
                password_for_push = getpass.getpass(
                    f"Enter password for {args.user}@{args.host} (needed to push SSH key): "
                )
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(1)

        # Push the key to the Pi
        if push_ssh_key_to_pi(args.host, args.user, password_for_push, key_to_use):
            print(f"✅ Key-based authentication configured for {args.name}")
        else:
            print(
                f"⚠️  Failed to push key, falling back to password authentication",
                file=sys.stderr,
            )

    config[args.name] = {"host": args.host, "user": args.user}

    # Store key or password
    if key_to_use:
        # Store key path as relative to home directory for portability
        if key_to_use.startswith(str(Path.home())):
            # Replace /Users/username with ~ for portability
            key_to_use = key_to_use.replace(str(Path.home()), "~", 1)
        config[args.name]["key"] = key_to_use
        if not args.push_key:
            # User provided a custom key path
            print(f"Using SSH key: {key_to_use}")
    elif args.password:
        print("Warning: Saving password in plain text in config.yml.")
        config[args.name]["password"] = args.password

    save_config(config_path, config)
    print(f"Pi '{args.name}' added to {config_path}")

    # Create symlink to pi-shell command
    try:
        import shutil

        pi_bridge_path = shutil.which("pi-shell")
        if pi_bridge_path:
            symlink_dir = Path(pi_bridge_path).parent
            symlink_path = symlink_dir / args.name

            if os.path.lexists(symlink_path):
                print(
                    f"ℹ️  Symlink {args.name} already exists (possibly created by another user)"
                )
                print(f"   You can still use: {args.name} run <command>")
                print(
                    f"   Note: Each user's config determines which Pi '{args.name}' connects to"
                )
            else:
                os.symlink(pi_bridge_path, symlink_path)
                print(f"✅ Created symlink: {args.name} -> pi-shell")
                print(f"   You can now use: {args.name} run <command>")
        else:
            print(
                "Note: Could not create symlink (pi-shell command not found in PATH)"
            )
    except Exception as e:
        print(f"Note: Could not create symlink: {e}")


def handle_remove(args):
    config_path = get_config_path(args)
    config = load_config(config_path)
    if args.name not in config:
        print(f"Error: Pi '{args.name}' not found in config.")
        sys.exit(1)

    del config[args.name]
    save_config(config_path, config)
    print(f"Pi '{args.name}' removed from {config_path}")

    # Note: We don't delete symlinks to avoid breaking other users who may have the same name
    # Symlinks are tiny and harmless if unused
    print(f"Note: Symlink '{args.name}' (if it exists) was not removed")
    print(f"      (Preserving for potential use by other users or configs)")
    print(f"      To remove manually: rm $(which {args.name})")


def handle_list(args):
    config_path = get_config_path(args)
    config = load_config(config_path)
    default_pi = config.get("default")

    # Check if there are any Pis configured (excluding 'default' key)
    pi_list = {k: v for k, v in config.items() if k != "default"}

    if not pi_list:
        print("No Pis configured.")
        print(
            "Use 'pi-shell add <name> --host <host> --user <user> --password <password> [--push-key]' to add a Pi."
        )
        return

    print(
        f"{ 'Name':<10} { 'Host':<20} { 'User':<10} { 'Default':<10} {'Default Path':<30}"
    )
    print("=" * 80)

    for name, pi_config in pi_list.items():
        is_default = "Yes" if name == default_pi else ""
        host = pi_config.get("host", "N/A")
        user = pi_config.get("user", "N/A")
        default_path = pi_config.get("default_path", "N/A")
        print(f"{name:<10} {host:<20} {user:<10} {is_default:<10} {default_path:<30}")


def handle_set_default(args):
    config_path = get_config_path(args)
    config = load_config(config_path)
    if args.name not in config:
        print(f"Error: Pi '{args.name}' not found in config.")
        sys.exit(1)

    config["default"] = args.name
    save_config(config_path, config)
    print(f"Default Pi set to '{args.name}'")


def handle_set_path(args):
    config_path = get_config_path(args)
    config = load_config(config_path)
    if args.name not in config:
        print(f"Error: Pi '{args.name}' not found in config.")
        sys.exit(1)

    config[args.name]["default_path"] = args.path
    save_config(config_path, config)
    print(f"Default path for '{args.name}' set to '{args.path}'")


def handle_status(args):
    config_path = get_config_path(args)
    config = load_config(config_path)

    pi_to_check = []
    if args.name:
        if args.name not in config:
            print(f"Error: Pi '{args.name}' not found in config.")
            sys.exit(1)
        pi_to_check.append(args.name)
    else:
        pi_to_check = [k for k in config.keys() if k != "default"]

    if not pi_to_check:
        print("No Pis configured.")
        print(
            "Use 'pi-shell add <name> --host <host> --user <user> --password <password> [--push-key]' to add a Pi."
        )
        return

    print(f"{ 'Name':<10} { 'Host':<20} { 'Hostname':<20} { 'Status':<10}")
    print("=" * 60)

    for name in pi_to_check:
        pi_config = config[name]
        host = pi_config.get("host")
        user = pi_config.get("user", "pi")
        password = pi_config.get("password")
        key = pi_config.get("key")

        # Expand ~ in key path for portability across users
        if key and key.startswith("~"):
            key = os.path.expanduser(key)

        remote_hostname = "N/A"
        status = "OFFLINE"

        if not host:
            print(
                f"{name:<10} {host or 'N/A':<20} {remote_hostname:<20} {'OFFLINE (No host)':<10}"
            )
            continue

        if not password and not key and os.getenv("PI_BRIDGE_NO_PROMPT") != "1":
            try:
                password = getpass.getpass(
                    f"Enter password for {user}@{host} (optional, for status check): "
                )
            except (EOFError, KeyboardInterrupt):
                password = None

        bridge = PiBridge(host=host, user=user, password=password, key_filename=key)

        try:
            if bridge.connect(timeout=3):
                status = "ONLINE"
                try:
                    out, err = bridge.run("hostname")
                    if out:
                        remote_hostname = out.strip()
                except Exception:
                    pass
        except paramiko.ssh_exception.BadHostKeyException:
            status = "BAD KEY"
        except Exception:
            pass  # Keep status as OFFLINE

        print(f"{name:<10} {host:<20} {remote_hostname:<20} {status:<10}")
        bridge.close()


def handle_check_ssh(args):
    config_path = get_config_path(args)
    config = load_config(config_path)

    pi_to_check = [k for k in config.keys() if k != "default"]

    print(f"{ 'Name':<10} { 'Host':<20} { 'Status':<20}")
    print("=" * 50)

    for name in pi_to_check:
        pi_config = config[name]
        host = pi_config.get("host")
        user = pi_config.get("user", "pi")
        password = pi_config.get("password")
        key = pi_config.get("key")

        # Expand ~ in key path for portability across users
        if key and key.startswith("~"):
            key = os.path.expanduser(key)

        status = "OFFLINE"

        if not host:
            print(f"{name:<10} {host or 'N/A':<20} {'OFFLINE (No host)':<20}")
            continue

        bridge = PiBridge(host=host, user=user, password=password, key_filename=key)

        try:
            if bridge.connect(timeout=3):
                status = "OK"
                bridge.close()
        except paramiko.ssh_exception.BadHostKeyException:
            print(f"The host key for {name} ({host}) has changed.", file=sys.stderr)
            choice = input(
                "Would you like to remove the old key and trust the new one? (y/n) "
            ).lower()
            if choice == "y":
                try:
                    subprocess.run(["ssh-keygen", "-R", host], check=True)
                    print(f"Removed old host key for {host}.")
                    status = "KEY UPDATED"
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"Error removing host key: {e}", file=sys.stderr)
                    status = "KEY UPDATE FAILED"
            else:
                status = "BAD KEY (UNCHANGED)"
        except Exception as e:
            status = f"ERROR: {e}"

        print(f"{name:<10} {host:<20} {status:<20}")


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to interact with Raspberry Pi over SSH"
    )
    parser.add_argument(
        "--config", help=f"Path to config file (default: ../config.yml)"
    )

    subparsers = parser.add_subparsers(dest="action", required=True)

    # Core actions
    core_actions = ["run", "run-stream", "read", "write", "send"]
    for action in core_actions:
        p = subparsers.add_parser(
            action, help=f"{action.capitalize()} a command or file on the Pi"
        )
        if action == "send":
            p.add_argument("local_path", help="Local file to send")
            p.add_argument(
                "remote_path",
                nargs="?",
                help="Remote destination path (optional if default_path is set)",
            )
            p.add_argument(
                "--sudo",
                action="store_true",
                help="Use sudo to move the file to the final destination",
            )
            p.add_argument("--sudo-password", help="Sudo password for the remote user")
        else:
            p.add_argument("target", help="Command to run or file path")
            if action == "write":
                p.add_argument(
                    "extra",
                    nargs="?",
                    help="Content for write action (optional if reading from stdin)",
                )

        p.add_argument("--pi", help="Specific Pi to use (e.g., pi1)")
        p.add_argument("--host", help="Override Pi hostname or IP")
        p.add_argument("--user", help="Override SSH username")
        p.add_argument("--password", help="Override SSH password")
        p.add_argument("--key", help="Override path to SSH private key")

    # Management commands
    p_add = subparsers.add_parser("add", help="Add a new Pi to the configuration")
    p_add.add_argument("name", help="Name of the new Pi (e.g., pi3)")
    p_add.add_argument("--host", required=True, help="Hostname or IP address")
    p_add.add_argument("--user", required=True, help="SSH username")
    p_add.add_argument("--password", help="SSH password (will be stored in plain text)")
    p_add.add_argument("--key", help="Path to SSH private key")
    p_add.add_argument(
        "--push-key",
        action="store_true",
        help="Generate (if needed) and push pi-shell SSH key to the Pi for password-less authentication",
    )
    p_add.set_defaults(func=handle_add)

    p_remove = subparsers.add_parser(
        "remove", help="Remove a Pi from the configuration"
    )
    p_remove.add_argument("name", help="Name of the Pi to remove")
    p_remove.set_defaults(func=handle_remove)

    p_list = subparsers.add_parser("list", help="List all configured Pis")
    p_list.set_defaults(func=handle_list)

    p_set_default = subparsers.add_parser("set-default", help="Set the default Pi")
    p_set_default.add_argument("name", help="Name of the Pi to set as default")
    p_set_default.set_defaults(func=handle_set_default)

    p_set_path = subparsers.add_parser(
        "set-path", help="Set the default remote path for a Pi"
    )
    p_set_path.add_argument("name", help="Name of the Pi to configure")
    p_set_path.add_argument("path", help="The default remote path")
    p_set_path.set_defaults(func=handle_set_path)

    p_status = subparsers.add_parser(
        "status", help="Check the status of configured Pis"
    )
    p_status.add_argument("name", nargs="?", help="Name of a specific Pi to check")
    p_status.set_defaults(func=handle_status)

    p_check_ssh = subparsers.add_parser(
        "check-ssh", help="Check SSH host keys for all Pis"
    )
    p_check_ssh.set_defaults(func=handle_check_ssh)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
        sys.exit(0)

    config_path = get_config_path(args)
    cfg = load_config(config_path)

    pi_identifier = args.pi or detect_pi_from_symlink() or cfg.get("default")

    if not pi_identifier:
        print("Error: No Pi specified and no default is set.", file=sys.stderr)
        sys.exit(1)

    pi_config = cfg.get(pi_identifier, {})
    if not pi_config:
        print(
            f"Error: No configuration found for Pi '{pi_identifier}'", file=sys.stderr
        )
        sys.exit(1)

    host_info = pi_config.get("host", "unknown")
    print(f"Using Pi: {pi_identifier} ({host_info})", file=sys.stderr)

    host = args.host or pi_config.get("host")
    user = args.user or pi_config.get("user", "pi")
    password = args.password or pi_config.get("password")
    key = args.key or pi_config.get("key")

    # Expand ~ in key path for portability across users
    if key and key.startswith("~"):
        key = os.path.expanduser(key)

    if not host:
        print(f"Error: No host specified for Pi '{pi_identifier}'", file=sys.stderr)
        sys.exit(1)

    if (
        not password and not key and args.action != "send"
    ):  # For send, we might not need a password upfront
        try:
            if os.getenv("PI_BRIDGE_NO_PROMPT") != "1":
                password = getpass.getpass(f"Enter password for {user}@{host}: ")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.", file=sys.stderr)
            sys.exit(1)

    bridge = PiBridge(host=host, user=user, password=password, key_filename=key)

    try:
        if not bridge.connect():
            print(f"Error: Could not connect to {host}.", file=sys.stderr)
            sys.exit(1)

        if args.action == "run":
            out, err = bridge.run(args.target)
            if out:
                print(out, end="")
            if err:
                print(err, end="", file=sys.stderr)
        elif args.action == "run-stream":
            exit_status = bridge.run_stream(args.target)
            if exit_status != 0:
                sys.exit(exit_status)
        elif args.action == "read":
            print(bridge.read(args.target), end="")
        elif args.action == "write":
            if args.extra:
                # Use provided content
                bridge.write(args.target, args.extra)
            else:
                # Read from stdin
                content = sys.stdin.read()
                bridge.write(args.target, content)
            print(f"Written to {args.target}")
        elif args.action == "send":
            local_path = Path(args.local_path)
            if not local_path.exists():
                print(f"Error: Local path not found at {local_path}", file=sys.stderr)
                sys.exit(1)

            remote_path_str = args.remote_path
            if not remote_path_str:
                default_path = pi_config.get("default_path")
                if not default_path:
                    print(
                        f"Error: remote_path is required and no default_path is set for '{pi_identifier}'.",
                        file=sys.stderr,
                    )
                    print(
                        f"Use 'pi set-path {pi_identifier} /your/default/path' to configure it.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                # Preserve directory structure relative to current dir
                remote_path_str = os.path.join(default_path, args.local_path)

            remote_path = Path(remote_path_str)
            remote_dir = remote_path.parent

            # Ensure remote directory exists
            mkdir_cmd = f"mkdir -p {remote_dir}"
            if args.sudo:
                if args.sudo_password:
                    mkdir_cmd = f"echo '{args.sudo_password}' | sudo -S {mkdir_cmd}"
                else:
                    mkdir_cmd = f"sudo {mkdir_cmd}"

            out, err = bridge.run(mkdir_cmd)
            if err:
                print(f"Error creating remote directory: {err}", file=sys.stderr)
                sys.exit(1)

            # Upload and move file
            if args.sudo:
                temp_path = f"/tmp/{local_path.name}"
                print(f"Uploading {local_path.name} to {temp_path}...", file=sys.stderr)
                bridge.upload_file(str(local_path), temp_path)

                print(f"Moving file to {remote_path} with sudo...", file=sys.stderr)
                if args.sudo_password:
                    mv_command = f"echo '{args.sudo_password}' | sudo -S mv {temp_path} {str(remote_path)}"
                else:
                    mv_command = f"sudo mv {temp_path} {str(remote_path)}"

                out, err = bridge.run(mv_command)
                if err:
                    print(f"Error moving file: {err}", file=sys.stderr)
                else:
                    print("File sent successfully.", file=sys.stderr)
            else:
                print(
                    f"Uploading {local_path.name} to {remote_path}...", file=sys.stderr
                )
                bridge.upload_file(str(local_path), str(remote_path))
                print("Upload complete.", file=sys.stderr)

    except paramiko.ssh_exception.BadHostKeyException:
        print(f"Error: Host key for {host} is invalid!", file=sys.stderr)
        print("This might mean the Pi's OS has been reinstalled.", file=sys.stderr)
        print("You can run the 'check-ssh' command to fix this.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
