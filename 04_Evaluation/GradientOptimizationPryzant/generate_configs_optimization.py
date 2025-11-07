import itertools
from generate_config import build_optimization_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

optimizer_modes = ["gradient"]
gpt_models = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]
gpt_models = ["gpt-4o-mini-2024-07-18"]
ollama_models = []  # e.g. ["llama3.1:8b-instruct-fp16"]

prompts = [
    "Question: Here are two parts of software development artifacts.\n\n"
    "            {source_type}: '''{source_content}'''\n\n"
    "            {target_type}: '''{target_content}'''\n"
    "            Are they related?\n\n"
    "            Answer with 'yes' or 'no'."
]

max_iterations_list = [1,2,3,4,5]

CONFIG_DIR = "configs/optimization"


def generate_all():
    # GPT + Ollama
    all_models = gpt_models + ollama_models

    for dataset in datasets:
        for model in all_models:
            for optimizer_mode, prompt, max_iter in itertools.product(
                    optimizer_modes, prompts, max_iterations_list
            ):
                # Overrides for prompt_optimizer and classifier
                overrides = {
                    "prompt_optimizer": {
                        "name": f"{optimizer_mode}_{get_model_provider(model)}",
                        "args": {
                            "prompt": prompt,
                            "maximum_iterations": max_iter,
                            "minibatch_size" : "20",
                            "model": model,
                        },
                    },
                    "classifier": {
                        "name": f"simple_{get_model_provider(model)}",
                        "args": {"model": model},
                    },
                    "metric": {
                        "name": "pointwise",
                        "args":   {}
                    },
                    "evaluator": {
                        "name": "ucb",
                        "args" : {
                            "samples_per_eval" : "16",
                            "eval_rounds" : "4",
                            "eval_prompts_per_round" : "1"
                        }
                    }
                }

                cfg = build_optimization_config(dataset, overrides=overrides)
                filename = (
                    f"{dataset}_{optimizer_mode}_{model}_mi{max_iter}.json"
                )
                save_config(cfg, dataset, model, filename, CONFIG_DIR)


if __name__ == "__main__":
    generate_all()
