import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from services import COMMON_SERVICES
from utils import resolve_target


class PortScanner:
    """Performs TCP port scanning with multithreading."""

    def __init__(self, target, start_port, end_port, stop_event, max_workers=120):
        self.target = target
        self.start_port = start_port
        self.end_port = end_port
        self.stop_event = stop_event
        self.max_workers = max_workers
        self.total_ports = end_port - start_port + 1
        self.resolved_ip = None

    def scan_port(self, port):
        """Scan a single TCP port and return its status."""
        if self.stop_event.is_set():
            return None

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                result = sock.connect_ex((self.resolved_ip, port))
                status = "Open" if result == 0 else "Closed"
                service = COMMON_SERVICES.get(port, "Unknown")
                return {"port": port, "status": status, "service": service}
        except Exception:
            return {"port": port, "status": "Closed", "service": COMMON_SERVICES.get(port, "Unknown")}

    def scan(self):
        """Run a threaded scan across the configured port range."""
        self.resolved_ip = resolve_target(self.target)
        ports = list(range(self.start_port, self.end_port + 1))

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(ports))) as executor:
            for result in executor.map(self.scan_port, ports):
                if self.stop_event.is_set():
                    break
                if result is not None:
                    yield result
