import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import customtkinter as ctk
from scanner import PortScanner
from database import ScanDatabase
from report import ReportGenerator
from utils import format_elapsed_time, is_valid_port_range


class PortScannerApp:
    """Main application class for GUI and scan workflow."""

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("Port Scanner")
        self.root.geometry("920x680")
        self.root.minsize(900, 660)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.db = ScanDatabase()
        self.scanner = None
        self.scan_thread = None
        self.stop_event = threading.Event()
        self.scan_results = []
        self.scan_start_time = None

        self._build_ui()

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(master=self.root, corner_radius=12)
        self.main_frame.grid(sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(master=self.main_frame, fg_color="#1f1f2a")
        title_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        title_frame.grid_columnconfigure(1, weight=1)

        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        self.logo_image = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(60, 60))
        logo_label = ctk.CTkLabel(
            master=title_frame,
            image=self.logo_image,
            text="",
            width=60,
            height=60,
            corner_radius=12,
        )
        logo_label.grid(row=0, column=0, padx=12, pady=12)

        header_label = ctk.CTkLabel(
            master=title_frame,
            text="Port Scanner",
            font=ctk.CTkFont(size=28, weight="bold"),
            anchor="w",
        )
        header_label.grid(row=0, column=1, sticky="w", padx=(8, 12), pady=12)

        form_frame = ctk.CTkFrame(master=self.main_frame, fg_color="#1c1c24")
        form_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        form_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.target_input = ctk.CTkEntry(master=form_frame, placeholder_text="Target IP or Domain")
        self.start_port_input = ctk.CTkEntry(master=form_frame, placeholder_text="Start Port")
        self.end_port_input = ctk.CTkEntry(master=form_frame, placeholder_text="End Port")

        self.target_input.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=14)
        self.start_port_input.grid(row=0, column=2, sticky="ew", padx=10, pady=14)
        self.end_port_input.grid(row=0, column=3, sticky="ew", padx=10, pady=14)

        button_frame = ctk.CTkFrame(master=self.main_frame, fg_color="#1c1c24")
        button_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.start_button = ctk.CTkButton(master=button_frame, text="Start Scan", command=self.start_scan)
        self.stop_button = ctk.CTkButton(master=button_frame, text="Stop Scan", command=self.stop_scan, fg_color="#ff4d4d")
        self.clear_button = ctk.CTkButton(master=button_frame, text="Clear Results", command=self.clear_results)
        self.export_button = ctk.CTkButton(master=button_frame, text="Export Report", command=self.export_report)

        self.start_button.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        self.clear_button.grid(row=0, column=2, sticky="ew", padx=10, pady=10)
        self.export_button.grid(row=0, column=3, sticky="ew", padx=10, pady=10)

        progress_frame = ctk.CTkFrame(master=self.main_frame, fg_color="#1c1c24")
        progress_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        progress_frame.grid_columnconfigure((0, 1), weight=1)

        self.progress_bar = ctk.CTkProgressBar(master=progress_frame)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(12, 6))

        self.status_label = ctk.CTkLabel(master=progress_frame, text="Status: Ready")
        self.status_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 12))

        summary_frame = ctk.CTkFrame(master=self.main_frame, fg_color="#1f1f2a")
        summary_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))
        summary_frame.grid_columnconfigure((0, 1), weight=1)

        self.open_ports_label = ctk.CTkLabel(master=summary_frame, text="Open Ports: 0")
        self.time_taken_label = ctk.CTkLabel(master=summary_frame, text="Time Taken: 0.00s")

        self.open_ports_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.time_taken_label.grid(row=0, column=1, sticky="e", padx=10, pady=10)

        results_frame = ctk.CTkFrame(master=self.main_frame, fg_color="#1c1c24")
        results_frame.grid(row=5, column=0, sticky="nsew", padx=12, pady=(0, 12))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_table = ctk.CTkScrollableFrame(master=results_frame)
        self.results_table.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.results_table.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(master=self.results_table, fg_color="#2a2a35")
        header_row.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        header_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(master=header_row, text="Port", width=80, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=8, pady=8)
        ctk.CTkLabel(master=header_row, text="Status", width=140, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=8, pady=8)
        ctk.CTkLabel(master=header_row, text="Service", width=140, anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=8, pady=8)

        self.result_rows = []

    def _add_result_row(self, port, status, service_name):
        row_index = len(self.result_rows) + 1
        row_frame = ctk.CTkFrame(master=self.results_table, fg_color="#1d1d27")
        row_frame.grid(row=row_index, column=0, sticky="ew", padx=5, pady=3)
        row_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(master=row_frame, text=str(port), anchor="w").grid(row=0, column=0, padx=8, pady=8)
        ctk.CTkLabel(master=row_frame, text=status, anchor="w").grid(row=0, column=1, padx=8, pady=8)
        ctk.CTkLabel(master=row_frame, text=service_name, anchor="w").grid(row=0, column=2, padx=8, pady=8)

        self.result_rows.append(row_frame)

    def _update_status(self, message):
        self.status_label.configure(text=f"Status: {message}")
        self.root.update_idletasks()

    def _update_progress(self, value):
        self.progress_bar.set(value)
        self.root.update_idletasks()

    def _set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.start_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.export_button.configure(state=state)
        self.target_input.configure(state=state)
        self.start_port_input.configure(state=state)
        self.end_port_input.configure(state=state)
        self.stop_button.configure(state="normal" if not enabled else "disabled")

    def _reset_summary(self):
        self.open_ports_label.configure(text="Open Ports: 0")
        self.time_taken_label.configure(text="Time Taken: 0.00s")

    def clear_results(self):
        for row in self.result_rows:
            row.destroy()
        self.result_rows.clear()
        self.scan_results.clear()
        self._reset_summary()
        self._update_progress(0.0)
        self._update_status("Ready")

    def _validate_inputs(self):
        target = self.target_input.get().strip()
        start_port = self.start_port_input.get().strip()
        end_port = self.end_port_input.get().strip()

        if not target:
            raise ValueError("Please enter a target IP address or domain name.")

        if not start_port.isdigit() or not end_port.isdigit():
            raise ValueError("Start and end ports must be numeric values.")

        start_port = int(start_port)
        end_port = int(end_port)

        if not is_valid_port_range(start_port, end_port):
            raise ValueError("Please enter a valid port range between 1 and 65535.")

        return target, start_port, end_port

    def start_scan(self):
        try:
            target, start_port, end_port = self._validate_inputs()
        except ValueError as error:
            messagebox.showwarning("Validation Error", str(error))
            return

        self.clear_results()
        self._update_status("Scanning")
        self._set_controls_enabled(False)
        self.scan_start_time = time.time()
        self.stop_event.clear()

        self.scanner = PortScanner(target, start_port, end_port, self.stop_event)
        self.scan_thread = threading.Thread(target=self._run_scan, daemon=True)
        self.scan_thread.start()

    def _run_scan(self):
        try:
            for index, result in enumerate(self.scanner.scan()):
                if self.stop_event.is_set():
                    self._update_status("Stopped")
                    break

                self.scan_results.append(result)
                self._add_result_row(result["port"], result["status"], result["service"])
                self._update_progress((index + 1) / self.scanner.total_ports)

            duration = format_elapsed_time(time.time() - self.scan_start_time)
            open_ports = sum(1 for result in self.scan_results if result["status"] == "Open")
            self.open_ports_label.configure(text=f"Open Ports: {open_ports}")
            self.time_taken_label.configure(text=f"Time Taken: {duration}")

            if not self.stop_event.is_set():
                self._update_status("Completed")
                self._save_scan_record(duration)

        except Exception as exc:
            messagebox.showerror("Scan Error", f"An error occurred during scanning:\n{exc}")
            self._update_status("Ready")
        finally:
            self._set_controls_enabled(True)

    def stop_scan(self):
        self.stop_event.set()
        self._update_status("Stopping")

    def _save_scan_record(self, duration):
        try:
            target = self.scanner.target
            ip_address = self.scanner.resolved_ip
            timestamp = int(time.time())
            open_ports = [result["port"] for result in self.scan_results if result["status"] == "Open"]
            self.db.save_scan(target, ip_address, self.scan_results, duration, timestamp)
        except Exception:
            pass

    def export_report(self):
        if not self.scan_results:
            messagebox.showwarning("Export Warning", "No scan results are available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")],
            initialdir=os.path.abspath("reports"),
            title="Save scan report",
        )

        if not file_path:
            return

        try:
            generator = ReportGenerator(self.scanner.target, self.scanner.resolved_ip, self.scan_results, self.scan_start_time)
            if file_path.endswith(".csv"):
                generator.save_csv(file_path)
            else:
                generator.save_txt(file_path)
            messagebox.showinfo("Export Complete", f"Report successfully saved to:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("Export Error", f"Unable to generate the report:\n{exc}")

    def _on_close(self):
        self.stop_event.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
