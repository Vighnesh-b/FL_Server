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
        self.root.geometry("650x500")

        # -------------------------
        #   Variables
        # -------------------------
        self.current_round = tk.IntVar(value=1)
        self.num_clients = tk.IntVar(value=0)

        # -------------------------
        #   UI LAYOUT
        # -------------------------

        tk.Label(root, text="Federated Server Dashboard", font=("Arial", 18)).pack(pady=10)

        frm = tk.Frame(root)
        frm.pack()

        tk.Label(frm, text="Current Round:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(frm, textvariable=self.current_round, font=("Arial", 12, "bold")).grid(row=0, column=1)

        tk.Label(frm, text="Client Updates Received:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5)
        tk.Label(frm, textvariable=self.num_clients, font=("Arial", 12, "bold")).grid(row=1, column=1)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Refresh Status", command=self.refresh_status).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Aggregate Now", command=self.aggregate_round).grid(row=0, column=1, padx=10)

        # Log Window
        tk.Label(root, text="Server Log:", font=("Arial", 12)).pack()
        self.log_box = tk.Text(root, height=10, width=70, state="disabled")
        self.log_box.pack(pady=5)

        self.log("Dashboard started.")

    # ----------------------------------------------------
    #   Logging function
    # ----------------------------------------------------
    def log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    # ----------------------------------------------------
    #   Refresh number of client updates this round
    # ----------------------------------------------------
    def refresh_status(self):
        round_num = str(self.current_round.get())

        if not os.path.exists(CLIENT_STATS_FILE):
            self.num_clients.set(0)
            self.log("No client_stats.json found.")
            return

        with open(CLIENT_STATS_FILE, "r") as f:
            stats = json.load(f)

        if round_num in stats:
            count = len(stats[round_num])
            self.num_clients.set(count)
            self.log(f"Round {round_num}: {count} client updates found.")
        else:
            self.num_clients.set(0)
            self.log(f"Round {round_num}: No updates found.")

    # ----------------------------------------------------
    #   Run Aggregation
    # ----------------------------------------------------
    def aggregate_round(self):
        round_num = self.current_round.get()

        self.log(f"Starting aggregation for Round {round_num}...")

        try:
            server = FederatedServer(
                model_fn=get_unetr,          # <-- Your model creation function
                cur_round=round_num,
                test_loader=None,               # optional
            )

            server.aggregate()

            self.log("Aggregation completed successfully!")
            messagebox.showinfo("Success", "Global model updated.")

            # Move to next round
            self.current_round.set(round_num + 1)
            self.num_clients.set(0)

        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))


# ---------------------------------------------------------
#   MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ServerDashboard(root)
    root.mainloop()
