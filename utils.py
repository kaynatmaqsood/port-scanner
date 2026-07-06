import socket


def resolve_target(target):
    """Resolve a hostname or return an IP address."""
    try:
        return socket.gethostbyname(target)
    except socket.gaierror as exc:
        raise ValueError(f"Unable to resolve target '{target}': {exc}")


def is_valid_port_range(start_port, end_port):
    """Validate a TCP port range."""
    if start_port < 1 or end_port > 65535 or start_port > end_port:
        return False
    return True


def format_elapsed_time(seconds):
    """Format elapsed time in seconds."""
    return f"{seconds:.2f}s"
