from generate_config import build_evaluation_config, save_config, get_model_provider

# ----------------------
# Experiment parameters
# ----------------------

CONFIG_DIR = "configs/req2req"
datasets = ["GANNT", "ModisDataset", "WARC", "dronology", "CM1-NASA"]

gpt_models = ["gpt-4o-mini-2024-07-18", "gpt-4o-2024-08-06"]
ollama_models = ["llama3.1:8b-instruct-fp16", "codellama:13b"]

classifier_modes = ["simple"]

prompts = ["",

"Imagine three different experts are answering this question. All experts will write down 1 step of their"
+ " thinking, then share it with the group. Then all experts will go on to the next step, etc. If any"
+ " expert realises they're wrong at any point then they leave. Give your reasoning enclosed in <think>"
+ " </think>. The question is...",

"Simulate three brilliant, logical experts collaboratively answering a question. Each one verbosely "
+ "explains their thought process in real-time, considering the prior explanations of others and openly"
+ " acknowledging mistakes. At each step, whenever possible, each expert refines and builds upon the "
+ "thoughts of others, acknowledging their contributions. They continue until there is a definitive "
+ "answer to the question. Give your reasoning enclosed in <think> </think>. The question is...",

"Identify and behave as three different experts that are appropriate to answering this question. All "
+ "experts will write down the step and their thinking about the step, then share it with the group. "
+ "Then, all experts will go on to the next step, etc. At each step all experts will score their "
+ "peers response between 1 and 5, 1 meaning it is highly unlikely, and 5 meaning it is highly likely"
+ ". If any expert is judged to be wrong at any point then they leave. After all experts have "
+ "provided their analysis, you then analyze all 3 analyses and provide either the consensus solution"
+ " or your best guess solution. Give your reasoning enclosed in <think> </think>. The question is..."]

question ="""
Question: Here are two parts of software development artifacts.

{source_type}: '''{source_content}'''

{target_type}: '''{target_content}'''
Are they related?

Answer with 'yes' or 'no'.
"""

def generate_all():
    all_models = gpt_models + ollama_models

    for dataset in datasets:
        for model in all_models:
            for classifier_mode in classifier_modes:
                # Overrides for prompt_optimizer and classifier
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
                        overrides["classifier"]["args"]["template"] = prompts[i] + question


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