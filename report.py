"""Reporting module for Port Scanner."""

import os
import csv
from datetime import datetime


class ReportGenerator:
    """Generates TXT and CSV reports for scan results."""

    def __init__(self, target, resolved_ip, results, start_timestamp):
        self.target = target
        self.resolved_ip = resolved_ip
        self.results = results
        self.start_timestamp = start_timestamp
        self.generated_at = datetime.now()

    def save_csv(self, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Port Scanner Report"])
            writer.writerow([f"Target", self.target])
            writer.writerow([f"Resolved IP", self.resolved_ip])
            writer.writerow([f"Generated At", self.generated_at.isoformat(sep=" ")])
            writer.writerow([])
            writer.writerow(["Port", "Status", "Service"])
            for entry in self.results:
                writer.writerow([entry["port"], entry["status"], entry["service"]])

    def save_txt(self, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, mode="w", encoding="utf-8") as txtfile:
            txtfile.write("Port Scanner Report\n")
            txtfile.write("========================\n")
            txtfile.write(f"Target: {self.target}\n")
            txtfile.write(f"Resolved IP: {self.resolved_ip}\n")
            txtfile.write(f"Generated At: {self.generated_at.isoformat(sep=' ')}\n\n")
            txtfile.write("Port\tStatus\tService\n")
            txtfile.write("----\t------\t-------\n")
            for entry in self.results:
                txtfile.write(f"{entry['port']}\t{entry['status']}\t{entry['service']}\n")
