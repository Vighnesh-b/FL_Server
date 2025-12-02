import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from server import FederatedServer
from models.unetr_model import get_unetr

CLIENT_STATS_FILE = "client_stats.json"


class ServerDashboard:

    def __init__(self, root):
        self.root = root
        self.root.title("Federated Learning Server Dashboard")
        self.root.geometry("700x600")
        self.root.configure(bg="#f0f0f0")

        # -------------------------
        #   Variables
        # -------------------------
        self.current_round = tk.IntVar(value=self.get_current_round())
        self.num_clients = tk.IntVar(value=0)
        self.expected_clients = tk.IntVar(value=3)  # Set your expected number

        # -------------------------
        #   UI LAYOUT
        # -------------------------
        
        # Header
        header_frame = tk.Frame(root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🖥️ Federated Server Dashboard",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=20)

        # Main content
        content_frame = tk.Frame(root, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Status Frame
        status_frame = tk.LabelFrame(
            content_frame,
            text="Server Status",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            padx=20,
            pady=20
        )
        status_frame.pack(fill=tk.X, pady=(0, 20))

        info_grid = tk.Frame(status_frame, bg="#ffffff")
        info_grid.pack(fill=tk.X)

        # Current Round
        tk.Label(
            info_grid,
            text="Current Round:",
            font=("Arial", 12, "bold"),
            bg="#ffffff"
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        tk.Label(
            info_grid,
            textvariable=self.current_round,
            font=("Arial", 12),
            bg="#ffffff",
            fg="#27ae60"
        ).grid(row=0, column=1, sticky="w")

        # Client Updates Received
        tk.Label(
            info_grid,
            text="Client Updates Received:",
            font=("Arial", 12, "bold"),
            bg="#ffffff"
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.client_label = tk.Label(
            info_grid,
            text="0 / 0",
            font=("Arial", 12),
            bg="#ffffff",
            fg="#e74c3c"
        )
        self.client_label.grid(row=1, column=1, sticky="w")

        # Expected Clients
        tk.Label(
            info_grid,
            text="Expected Clients:",
            font=("Arial", 12, "bold"),
            bg="#ffffff"
        ).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.expected_entry = tk.Entry(
            info_grid,
            textvariable=self.expected_clients,
            font=("Arial", 12),
            width=10
        )
        self.expected_entry.grid(row=2, column=1, sticky="w")

        # Buttons Frame
        btn_frame = tk.Frame(content_frame, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(
            btn_frame,
            text="🔄 Refresh Status",
            command=self.refresh_status
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            btn_frame,
            text="⚡ Aggregate Now",
            command=self.aggregate_round
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(
            btn_frame,
            text="🔄 Initialize New Training (Round 0)",
            command=self.initialize_new_training
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Log Frame
        log_frame = tk.LabelFrame(
            content_frame,
            text="Server Log",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            padx=15,
            pady=15
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_box = tk.Text(
            log_frame,
            height=15,
            width=70,
            state="disabled",
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.log_box.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        status_bar = tk.Frame(root, bg="#34495e", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_bar,
            text="● Ready",
            font=("Arial", 9),
            bg="#34495e",
            fg="#2ecc71",
            anchor="w"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.log("Dashboard started.")
        self.refresh_status()

    # ----------------------------------------------------
    #   Get current round from client_stats.json
    # ----------------------------------------------------
    def get_current_round(self):
        """Read current round from client_stats.json"""
        if not os.path.exists(CLIENT_STATS_FILE):
            return 1
        
        try:
            with open(CLIENT_STATS_FILE, "r") as f:
                data = json.load(f)
            
            if not data:
                return 1
            
            # Get max round + 1 (next round to aggregate)
            rounds = [int(r) for r in data.keys()]
            return max(rounds) if rounds else 1
            
        except Exception as e:
            self.log(f"Error reading current round: {e}")
            return 1

    # ----------------------------------------------------
    #   Logging function
    # ----------------------------------------------------
    def log(self, msg):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def update_status(self, msg, color="#2ecc71"):
        self.status_label.config(text=f"● {msg}", fg=color)

    # ----------------------------------------------------
    #   Refresh number of client updates this round
    # ----------------------------------------------------
    def refresh_status(self):
        round_num = str(self.current_round.get())

        if not os.path.exists(CLIENT_STATS_FILE):
            self.num_clients.set(0)
            self.client_label.config(
                text=f"0 / {self.expected_clients.get()}",
                fg="#e74c3c"
            )
            self.log("No client_stats.json found.")
            return

        with open(CLIENT_STATS_FILE, "r") as f:
            stats = json.load(f)

        if round_num in stats:
            count = len(stats[round_num])
            self.num_clients.set(count)
            expected = self.expected_clients.get()
            
            color = "#27ae60" if count >= expected else "#f39c12"
            self.client_label.config(
                text=f"{count} / {expected}",
                fg=color
            )
            self.log(f"Round {round_num}: {count} client updates found.")
            
            if count >= expected:
                self.update_status("Ready to aggregate", "#27ae60")
            else:
                self.update_status(f"Waiting for clients ({count}/{expected})", "#f39c12")
        else:
            self.num_clients.set(0)
            self.client_label.config(
                text=f"0 / {self.expected_clients.get()}",
                fg="#e74c3c"
            )
            self.log(f"Round {round_num}: No updates found.")
            self.update_status("No client updates", "#e74c3c")

    # ----------------------------------------------------
    #   Initialize new training from Round 0
    # ----------------------------------------------------
    def initialize_new_training(self):
        result = messagebox.askyesno(
            "Initialize New Training",
            "This will create a fresh UNETR model and reset to Round 0.\n"
            "All previous training data will remain but a new training session will start.\n\n"
            "Continue?"
        )
        
        if not result:
            return
        
        self.log("=" * 50)
        self.log("Initializing new FL training session...")
        self.update_status("Initializing...", "#f39c12")
        
        try:
            # Create server with round 0 (will initialize fresh model)
            server = FederatedServer(
                model_fn=get_unetr,
                cur_round=0,
                test_loader=None
            )
            
            self.current_round.set(1)  # Clients will start from round 1
            self.num_clients.set(0)
            
            self.log("✓ Fresh UNETR model created and saved")
            self.log("✓ Server ready for Round 1")
            self.log("=" * 50)
            
            self.update_status("Initialized - Ready for Round 1", "#27ae60")
            messagebox.showinfo(
                "Success",
                "New training session initialized!\n"
                "Fresh UNETR model created.\n"
                "Clients can now connect for Round 1."
            )
            
            self.refresh_status()
            
        except Exception as e:
            self.log(f"✗ Error: {str(e)}")
            self.update_status("Initialization failed", "#e74c3c")
            messagebox.showerror("Error", str(e))

    # ----------------------------------------------------
    #   Run Aggregation
    # ----------------------------------------------------
    def aggregate_round(self):
        round_num = self.current_round.get()
        
        # Check if we have enough clients
        if self.num_clients.get() < self.expected_clients.get():
            result = messagebox.askyesno(
                "Insufficient Clients",
                f"Only {self.num_clients.get()} / {self.expected_clients.get()} clients have submitted.\n"
                "Aggregate anyway?"
            )
            if not result:
                return

        self.log(f"Starting aggregation for Round {round_num}...")
        self.update_status("Aggregating...", "#f39c12")

        try:
            server = FederatedServer(
                model_fn=get_unetr,
                cur_round=round_num,
                test_loader=None,
            )

            success = server.aggregate()
            
            if not success:
                self.log("✗ Aggregation failed - no valid client updates")
                self.update_status("Aggregation failed", "#e74c3c")
                messagebox.showerror("Error", "No valid client updates found for this round")
                return

            self.log("✓ Aggregation completed successfully!")
            self.update_status("Aggregation complete", "#27ae60")
            messagebox.showinfo("Success", f"Round {round_num} aggregation complete!")

            # Move to next round
            self.current_round.set(round_num + 1)
            self.num_clients.set(0)
            self.refresh_status()

        except Exception as e:
            self.log(f"✗ Error: {str(e)}")
            self.update_status("Error during aggregation", "#e74c3c")
            messagebox.showerror("Error", str(e))


# ---------------------------------------------------------
#   MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ServerDashboard(root)
    root.mainloop()