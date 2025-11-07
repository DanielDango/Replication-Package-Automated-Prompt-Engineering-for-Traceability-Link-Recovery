import itertools
from generate_config import build_optimization_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------



CONFIG_DIR = "configs/optimization"
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

optimizer_modes = ["feedback"]
gpt_models = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]
prompts = ["Question: Here are two parts of software development artifacts.\n\n            {source_type}: '''{source_content}'''\n\n            {target_type}: '''{target_content}'''\n            Are they related?\n\n            Answer with 'yes' or 'no'."]

#Lists for feedback params
max_iterations_list = [1, 5, 3]
feedback_size_list = [3, 3, 1]


def generate_all():
    all_models = gpt_models

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
                                "optimization_template":
                                    """You are required to enhance and clarify the explanations of the categories in the prompt by 
                                    integrating illustrative examples and information implicitly referenced in the initial context.\n 
                                    The optimized prompt must follow these strict guidelines:\n 
                                    Maintain the Original Format: The formating in the optimized prompt must remain exactly the same as 
                                    in the sample prompt; no changes should be made to the formatings’ structure or order.\n 
                                    Expand Explanations: Enrich and expand the explanations of each category within the steps, 
                                    incorporating examples provided. Use these examples to enhance understanding and provide clarity\n 
                                    Incorporate Class Explanations: Specifically, integrate the detailed 'Class Explanations' of 
                                    categories from the first prompt into the optimized prompt. For each category, introduce implicit 
                                    clarifications based on relevant data extracted from the context\n 
                                    Enclose your optimized prompt 
                                    with<prompt></prompt>brackets.\n
                                    The original prompt is provided below:\n
                                    '''{original_prompt}""",
                                "maximum_iterations": iterations,
                                "feedback_size": feedback_size,
                                "model": model,
                            }
                        },
                        "classifier": {
                            "name": f"simple_{get_model_provider(model)}",
                            "args": {
                                "model": model,
                            }
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