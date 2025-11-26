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

        os.makedirs(self.client_weights_dir, exist_ok=True)
        os.makedirs(self.global_model_dir, exist_ok=True)

    def save_global_model(self, round_num):
        # save round-specific
        path = os.path.join(self.global_model_dir, f"global_round_{round_num}.pth")
        torch.save(self.model.state_dict(), path)

        # save latest
        latest = os.path.join(self.global_model_dir, "global_latest.pth")
        torch.save(self.model.state_dict(), latest)

        print(f"[Server] Saved global model (Round {round_num})")

    def read_client_stats(self):
        with open("client_stats.json", "r") as f:
            data = json.load(f)
        return data.get(str(self.cur_round), [])

    def aggregate(self):
        client_data = self.read_client_stats()

        state_dicts = []
        dataset_sizes = []

        for entry in client_data:
            client_id = entry["client_id"]
            dataset_sizes.append(int(entry["dataset_size"]))

            weights_path = os.path.join(
                self.client_weights_dir, 
                f"{client_id}_round{self.cur_round}.pth"     # ensure same naming
            )

            state_dicts.append(torch.load(weights_path, map_location=self.device))

        # run FedAvg
        new_state = fed_avg(state_dicts, dataset_sizes)
        self.model.load_state_dict(new_state)

        self.save_global_model(self.cur_round)
