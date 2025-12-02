import torch
import os
import json
from utils.fed_utils import fed_avg

class FederatedServer:

    def __init__(self, model_fn, cur_round, test_loader, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model_fn(self.device)

        self.cur_round = cur_round
        self.test_loader = test_loader

        self.global_model_dir = "global_models"
        self.client_weights_dir = "uploaded_client_weights"
        self.client_stats_file = "client_stats.json"

        os.makedirs(self.client_weights_dir, exist_ok=True)
        os.makedirs(self.global_model_dir, exist_ok=True)
        
        # Initialize global model if starting from round 0
        if cur_round == 0:
            self.initialize_global_model()

    def initialize_global_model(self):
        print("[Server] Initializing fresh global model for Round 0...")
        
        # Model is already initialized in __init__, just save it
        latest_path = os.path.join(self.global_model_dir, "global_latest.pth")
        round_path = os.path.join(self.global_model_dir, "global_round_0.pth")
        
        torch.save(self.model.state_dict(), latest_path)
        torch.save(self.model.state_dict(), round_path)
        
        print(f"[Server] Fresh model saved → {latest_path}")
        
        # Initialize client_stats.json if it doesn't exist
        if not os.path.exists(self.client_stats_file):
            with open(self.client_stats_file, "w") as f:
                json.dump({}, f, indent=4)
            print(f"[Server] Created {self.client_stats_file}")

    def save_global_model(self, round_num):
        # save round-specific
        path = os.path.join(self.global_model_dir, f"global_round_{round_num}.pth")
        torch.save(self.model.state_dict(), path)

        # save latest
        latest = os.path.join(self.global_model_dir, "global_latest.pth")
        torch.save(self.model.state_dict(), latest)

        print(f"[Server] Saved global model (Round {round_num})")

    def read_client_stats(self):
        if not os.path.exists(self.client_stats_file):
            return []
            
        with open(self.client_stats_file, "r") as f:
            data = json.load(f)
        return data.get(str(self.cur_round), [])
    
    @staticmethod
    def get_current_round_from_stats():
        client_stats_file = "client_stats.json"
        
        if not os.path.exists(client_stats_file):
            return 0
        
        try:
            with open(client_stats_file, "r") as f:
                data = json.load(f)
            
            if not data:
                return 0
            
            # Get the maximum round number
            rounds = [int(r) for r in data.keys()]
            return max(rounds) if rounds else 0
            
        except Exception as e:
            print(f"[Server] Error reading current round: {e}")
            return 0

    def aggregate(self):
        client_data = self.read_client_stats()
        
        if not client_data:
            print(f"[Server] No client updates found for Round {self.cur_round}")
            return False

        state_dicts = []
        dataset_sizes = []

        for entry in client_data:
            client_id = entry["client_id"]
            dataset_sizes.append(int(entry["dataset_size"]))

            weights_path = os.path.join(
                self.client_weights_dir, 
                f"{client_id}_round{self.cur_round}.pth"
            )
            
            if not os.path.exists(weights_path):
                print(f"[Server] Warning: Missing weights for {client_id}")
                continue

            state_dicts.append(torch.load(weights_path, map_location=self.device))

        if not state_dicts:
            print(f"[Server] No valid client weights found for Round {self.cur_round}")
            return False

        # run FedAvg
        new_state = fed_avg(state_dicts, dataset_sizes)
        self.model.load_state_dict(new_state)

        self.save_global_model(self.cur_round)
        return True