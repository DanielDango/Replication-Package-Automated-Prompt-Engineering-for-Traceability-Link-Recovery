import itertools
from generate_config import build_optimization_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------



CONFIG_DIR = "configs/optimization"
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

optimizer_modes = ["feedback"]
gpt_models = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]
ollama_models = ["llama3.1:8b-instruct-fp16"]
prompts = ["Question: Here are two parts of software development artifacts.\n\n            {source_type}: '''{source_content}'''\n\n            {target_type}: '''{target_content}'''\n            Are they related?\n\n            Answer with 'yes' or 'no'."]

#Lists for feedback params
max_iterations_list = [1, 5, 10]
feedback_size_list = [3, 3, 5]


def generate_all():
    all_models = gpt_models + ollama_models

    for dataset in datasets:
        for model in all_models:
            for optimizer_mode, prompt in itertools.product(
                    optimizer_modes, prompts
            ):
                for iterations, feedback_size in zip(max_iterations_list, feedback_size_list):
                    # Overrides for prompt_optimizer and classifier
                    overrides = {
                        "prompt_optimizer": {
                            "name": f"{optimizer_mode}_{get_model_provider(model)}",
                            "args": {
                                "prompt": prompt,
                                "model": model,
                                "maximum_iterations": iterations,
                                "feedback_size": feedback_size
                            },
                        },
                        "classifier": {
                            "name": f"simple_{get_model_provider(model)}",
                            "args": {
                                "model": model,
                            },
                        }
                    }

                    cfg = build_optimization_config(dataset, overrides=overrides)
                    if get_model_provider(model) == "ollama":
                        model_provider = "ollama"
                    elif get_model_provider(model) == "openai":
                        model_provider = "gpt"
                    filename = (
                        f"{dataset}_{optimizer_mode}_{model_provider}_{model}_0_mi{iterations}_fs{feedback_size}.json"
                    )
                    save_config(cfg, dataset, model, filename, CONFIG_DIR)


if __name__ == "__main__":
    generate_all()