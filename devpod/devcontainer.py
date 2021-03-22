import json
import os
import pathlib

def get_config(devc_dir):
    devc_config_path = os.path.join(devc_dir, "devcontainer.json")
    devc_config_json = ""
    with open(devc_config_path, "r") as devc_config_fp:
        for line in devc_config_fp.readlines():
            parts = line.strip().split("//")  # @TODO: Switch to more robust method (that handles quoted or escaped comment symbols).
            cleaned_data = parts[0].strip()
            if cleaned_data:
                devc_config_json += cleaned_data + "\n"
    devc_config = json.loads(devc_config_json)
    return devc_config
