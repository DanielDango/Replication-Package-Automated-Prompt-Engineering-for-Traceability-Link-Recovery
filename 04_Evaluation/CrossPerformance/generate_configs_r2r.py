from generate_config import build_evaluation_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------

CONFIG_DIR = "configs/req2req"
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

gpt_models = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06", "gpt-5-mini-2025-08-07"]

classifier_modes = ["simple"]

PROMPT = """
Question: We have two software development artifacts that may or may not be related in terms of their purpose, functionality, or requirements.

Source Artifact ({source_type}): '''{source_content}'''

Target Artifact ({target_type}): '''{target_content}'''

Please analyze the content of both artifacts and determine if they are related. For the purpose of this analysis, consider the following criteria:
1. **Purpose**: Do both artifacts serve a similar goal or objective within the software development process?
2. **Functionality**: Do both artifacts provide similar features or capabilities?
3. **Requirements**: Do both artifacts address the same requirements or constraints?

Based on these criteria, answer with 'yes' if they are related, or 'no' if they are not related.
"""

def generate_all():
    all_models = gpt_models

    for dataset in datasets:
        for model in all_models:
            for classifier_mode in classifier_modes:
                # Overrides for prompt_optimizer and classifier
                prompts = ["", PROMPT]
                for i in range(len(prompts)):
                    overrides = {
                        "classifier": {
                            "name": f"{classifier_mode}_{get_model_provider(model)}",
                            "args": {
                                "model": model
                            },
                        }
                    }
                    if prompts[i] != "":
                        overrides["classifier"]["args"]["template"] = prompts[i]

                    if model == "gpt-5-mini-2025-08-07":
                        overrides["classifier"]["args"]["temperature"] = "1.0"

                    cfg = build_evaluation_config(dataset, overrides=overrides)
                    if get_model_provider(model) == "ollama":
                        model_provider = "ollama"
                    elif get_model_provider(model) == "openai":
                        model_provider = "gpt"
                    filename = (
                        f"{dataset}_{classifier_mode}_{model_provider}_{model}_{i}.json"
                    )
                    save_config(cfg, dataset, model, filename, CONFIG_DIR)


if __name__ == "__main__":
    generate_all()