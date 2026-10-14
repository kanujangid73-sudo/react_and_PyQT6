import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal


class ScanWorker(QThread):
    # Signals to safely update the GUI thread
    progress_signal = pyqtSignal(int, int)  # (scanned_ports, total_ports)
    result_signal = pyqtSignal(dict)         # Port scan result dict
    finished_signal = pyqtSignal(str)        # Completion status message
    error_signal = pyqtSignal(str)           # Error message

    def __init__(self, target_host: str, start_port: int, end_port: int, max_threads: int = 50, timeout: float = 1.0):
        super().__init__()
        self.target_host = target_host
        self.start_port = start_port
        self.end_port = end_port
        self.max_threads = max_threads
        self.timeout = timeout
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def scan_port(self, ip: str, port: int) -> dict:
        if self._is_cancelled:
            return None

        result = {
            "port": port,
            "status": "Closed",
            "service": "Unknown",
            "banner": ""
        }

        # Resolve common service names
        try:
            result["service"] = socket.getservbyport(port, "tcp").upper()
        except OSError:
            result["service"] = "UNKNOWN"

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                conn = s.connect_ex((ip, port))
                if conn == 0:
                    result["status"] = "Open"
                    # Attempt lightweight banner grabbing
                    try:
                        s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                        banner = s.recv(1024).decode("utf-8", errors="ignore").strip()
                        result["banner"] = banner.split("\n")[0] if banner else "No Banner"
                    except Exception:
                        result["banner"] = "N/A"
        except Exception as e:
            result["status"] = "Error"

        return result

    def run(self):
        try:
            target_ip = socket.gethostbyname(self.target_host)
        except socket.gaierror:
            self.error_signal.emit(f"Could not resolve hostname: {self.target_host}")
            return

        ports = list(range(self.start_port, self.end_port + 1))
        total_ports = len(ports)
        scanned_count = 0

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_port = {executor.submit(self.scan_port, target_ip, p): p for p in ports}

            for future in as_completed(future_to_port):
                if self._is_cancelled:
                    break

                res = future.result()
                scanned_count += 1
                self.progress_signal.emit(scanned_count, total_ports)

                if res and res["status"] == "Open":
                    self.result_signal.emit(res)

        if self._is_cancelled:
            self.finished_signal.emit("Scan cancelled by user.")
        else:
            self.finished_signal.emit(f"Scan complete for {self.target_host} ({target_ip})")