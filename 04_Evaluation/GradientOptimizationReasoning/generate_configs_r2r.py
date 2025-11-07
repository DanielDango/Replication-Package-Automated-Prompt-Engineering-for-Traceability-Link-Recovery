from generate_config import build_evaluation_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------

CONFIG_DIR = "configs/req2req"
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

gpt_models = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]
ollama_models = ["llama3.1:8b-instruct-fp16", "codellama:13b"]

classifier_modes = ["reasoning"]

def generate_all():
    all_models = gpt_models + ollama_models

    for dataset in datasets:
        for model in all_models:
            for classifier_mode in classifier_modes:
                # Overrides for prompt_optimizer and classifier
                overrides = {
                    "classifier": {
                        "name": f"{classifier_mode}_{get_model_provider(model)}",
                        "args": {
                            "model": model,
                        },
                    }
                }

                cfg = build_evaluation_config(dataset, overrides=overrides)
                if get_model_provider(model) == "ollama":
                    model_provider = "ollama"
                elif get_model_provider(model) == "openai":
                    model_provider = "gpt"
                filename = (
                    f"{dataset}_{classifier_mode}_{model_provider}_{model}.json"
                )
                save_config(cfg, dataset, model, filename, CONFIG_DIR)


if __name__ == "__main__":
    generate_all()