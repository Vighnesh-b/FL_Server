from flask import Flask, request, jsonify,Response
from flask import send_file
import os
import time
import json
from datetime import datetime

app = Flask(__name__)

CLIENT_STATS_FILE = "client_stats.json"
UPLOAD_DIR = "uploaded_client_weights"
GLOBAL_MODEL_PATH = "global_models/global_latest.pth"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("global_models",exist_ok=True)

@app.route('/api/upload-client-weights', methods=['POST'])
def upload_client_weights():
    # Validate file
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file received"}), 400

    file = request.files["file"]

    client_id = request.form.get("client_id")
    dataset_size = request.form.get("dataset_size")
    cur_round = request.form.get("cur_round")

    # Validate fields
    if not client_id:
        return jsonify({"success": False, "error": "client_id not provided"}), 400

    if not cur_round:
        return jsonify({"success": False, "error": "cur_round not provided"}), 400

    dataset_size = int(dataset_size) if dataset_size else 0

    # Save weights with round info
    save_path = os.path.join(UPLOAD_DIR, f"{client_id}_round{cur_round}.pth")
    file.save(save_path)

    # Store metadata safely
    store_client_stats(cur_round, client_id, dataset_size)

    print(f"[SERVER] Saved client {client_id} R{cur_round} weights → {save_path}")

    return jsonify({
        "success": True,
        "message": "File uploaded successfully",
        "save_path": save_path
    }), 200


@app.route("/api/get-global-model", methods=["GET"])
def get_global_model():
    client_ip = request.remote_addr
    print(f"[REQUEST] {client_ip} is requesting the global model...")

    if not os.path.exists(GLOBAL_MODEL_PATH):
        print("[ERROR] Global model file not found!")
        return {"error": "No global model found on server"}, 404

    # Print stats
    size_mb = round(os.path.getsize(GLOBAL_MODEL_PATH) / (1024 * 1024), 2)
    print(f"Sending model ({size_mb} MB) to {client_ip}")

    # Start time
    start = time.time()

    # send_file auto-streams the file efficiently
    def generate():
        with open(GLOBAL_MODEL_PATH, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break
                yield chunk

    # When response completes (client finished download)
    def log_after(response):
        end = time.time()
        print(f"[COMPLETE] Finished sending model to {client_ip} in {end - start:.2f} sec")
        return response

    response = Response(generate(), mimetype="application/octet-stream")
    response.direct_passthrough = True
    response.call_on_close(lambda: log_after(response))
    return response

def store_client_stats(cur_round, client_id, dataset_size):

    if os.path.exists(CLIENT_STATS_FILE):
        with open(CLIENT_STATS_FILE, "r") as f:
            stats = json.load(f)
    else:
        stats = {}

    cur_round = str(cur_round)

    if cur_round not in stats:
        stats[cur_round] = []

    stats[cur_round].append(
        {
            "client_id": client_id,
            "dataset_size": dataset_size,
            "timestamp": str(datetime.now())
        }
    )

    with open(CLIENT_STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)



if __name__ == "__main__":
    app.run(port=8000)
