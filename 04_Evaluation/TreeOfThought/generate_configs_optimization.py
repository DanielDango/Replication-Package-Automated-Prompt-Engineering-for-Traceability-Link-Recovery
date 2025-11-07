import itertools
from generate_config import build_optimization_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

gpt_models = ["gpt-4o-mini-2024-07-18"]

CONFIG_DIR = "configs/optimization"


def generate_all():
    all_models = gpt_models
    for dataset in datasets:
        for model in all_models:
                cfg = build_optimization_config(dataset)
                filename = (
                    f"{dataset}_mock_{model}.json"
                )
                save_config(cfg, dataset, model, filename, CONFIG_DIR)


if __name__ == "__main__":
    generate_all()
