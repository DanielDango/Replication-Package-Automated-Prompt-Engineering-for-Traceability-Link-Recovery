import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, NamedTuple, Optional

import jinja2

# Constants
OPTIMIZATION_RESULT_FILE_FORMAT = "results-prompt-optimization"
AVERAGE_DATASET = "Avg"
WEIGHTED_AVERAGE_DATASET = "WeightedAvg"

KISS_PROMPT = """
            Question: Here are two parts of software development artifacts.

            {source_type}: '''{source_content}'''

            {target_type}: '''{target_content}'''
            Are they related?

            Answer with 'yes' or 'no'.
            """

COT_PROMPT = """
# task
Below are two artifacts from the same software system. Is there a traceability link between (1) and (2)?
# output format 
Give your reasoning and then answer with 'yes' or 'no' enclosed in <trace> </trace>.
# input format
(1) {source_type}: '''{source_content}''' 
(2) {target_type}: '''{target_content}'''.
"""

TOT_PROMPTS = [
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
    + " or your best guess solution. Give your reasoning enclosed in <think> </think>. The question is..."
]

TOT_QUESTION ="""
Question: Here are two parts of software development artifacts.

{source_type}: '''{source_content}'''

{target_type}: '''{target_content}'''
Are they related?

Answer with 'yes' or 'no'.
"""

MODEL_ABBREVIATIONS = {
    r"^codellama:\d+\w*$": "Codellama",
    r"^llama3.1:\d+b.*$": "Llama 3.1",
    r"^gpt-4o-mini-\d{4}-\d{2}-\d{2}$": "GPT-4o-mini",
    r"^gpt-4o-\d{4}-\d{2}-\d{2}$": "GPT-4o",
    r"^gpt-5-mini-\d{4}-\d{2}-\d{2}$": "GPT-5-mini",
}

PREFERRED_ORDER = ["kiss-original", "original", "simple", "iterative", "feedback"]


# Data structures using NamedTuple for immutability and clarity
class OptimizationData(NamedTuple):
    prompt_name: str
    optimizer_model: str
    optimized_prompt: str


class MetricsData(NamedTuple):
    precision: float
    recall: float
    f1: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1": round(self.f1, 3)
        }


# Utility functions for text processing
def normalize_prompt(prompt: str) -> str:
    """Normalize prompt text for comparison by removing markdown escapes and excess whitespace."""
    # Remove markdown escapes
    markdown_special_chars = r"\\`*_{}\[\]\(\)\#+\-\.\!|>"
    prompt = re.sub(rf"\\([{markdown_special_chars}])", r"\1", prompt)

    # Remove excess whitespace
    prompt = re.sub(r"\s+", " ", prompt)

    return prompt.strip()


def abbreviate_model_name(name: str) -> str:
    """Replace known model names with abbreviations based on patterns."""
    for pattern, abbr in MODEL_ABBREVIATIONS.items():
        if re.fullmatch(pattern, name):
            return abbr

    print(f"Warning: No abbreviation found for model '{name}'. Using full name.")
    return name


def create_prompt_sort_key(prompt_name: str) -> Tuple:
    """Generate sort key for prompt name based on preferred order and arguments."""
    p_lower = prompt_name.lower().strip()

    # Split prefix and argument part
    parts = p_lower.split("(", 1)
    prefix = parts[0].strip()
    args_str = parts[1].rstrip(")") if len(parts) > 1 else ""

    # Parse arguments into (key, int(value)) pairs
    args = []
    for key, val in re.findall(r"(\w+)\s*=\s*(\d+)", args_str):
        args.append((key, int(val)))

    # Generate sort key: preferred order first, then prefix, then args, then full name
    if prefix in PREFERRED_ORDER:
        return (0, PREFERRED_ORDER.index(prefix), tuple(args), p_lower)
    else:
        return (1, prefix, tuple(args), p_lower)


def create_dataset_sort_key(dataset_name: str) -> Tuple:
    """Generate sort key for dataset name (regular datasets first, then averages)."""
    if dataset_name == WEIGHTED_AVERAGE_DATASET:
        return (2, dataset_name)  # Last
    elif dataset_name == AVERAGE_DATASET:
        return (1, dataset_name)  # Second to last
    else:
        return (0, dataset_name)  # Regular datasets first


# JSON and file parsing functions
def extract_json_config(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON configuration from Markdown text."""
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            return None
    return None


def extract_dataset_name_from_config(config: Dict[str, Any]) -> str:
    """Extract dataset name from configuration dictionary and make it LaTeX command safe."""
    dataset_path = config.get("gold_standard_configuration", {}).get("path", "")
    match = re.search(r"/([A-Za-z0-9_-]+)/answer\.csv", dataset_path)

    if not match:
        return ""

    raw_name = match.group(1)

    # Convert to LaTeX-safe command name
    # 1. Replace numbers with their word equivalents
    number_map = {
        '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four',
        '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine'
    }

    latex_safe_name = raw_name

    # Replace numbers with words
    for digit, word in number_map.items():
        latex_safe_name = latex_safe_name.replace(digit, word)

    # Replace hyphens and underscores with nothing (or you could use camelCase)
    latex_safe_name = latex_safe_name.replace('-', '').replace('_', '')

    # Ensure first character is uppercase for LaTeX command convention
    if latex_safe_name:
        latex_safe_name = latex_safe_name[0].upper() + latex_safe_name[1:]

    return latex_safe_name


def extract_classifier_info_from_config(config: Dict[str, Any]) -> Tuple[str, str]:
    """Extract classifier model and prompt text from configuration."""
    classifier = config.get("classifier", {}).get("args", {})
    model = classifier.get("model", "")
    prompt_text = classifier.get("template", "").strip()
    return model, prompt_text


# Prompt optimization loading functions
def build_prompt_name_from_config(config: Dict[str, Any]) -> str:
    """Build prompt name from optimization configuration."""
    optimizer_name = config.get("prompt_optimizer", {}).get("name", "")
    prompt_name_base = re.sub(r"_.*", "", optimizer_name)

    args = config.get("prompt_optimizer", {}).get("args", {})
    extra_parts = []

    if args.get("maximum_iterations"):
        extra_parts.append(f"\\iter={args['maximum_iterations']}")
    if args.get("feedback_size"):
        extra_parts.append(f"\\feed={args['feedback_size']}")

    if extra_parts:
        return f"{prompt_name_base} ({', '.join(extra_parts)})"
    return prompt_name_base


def extract_optimized_prompt_from_text(text: str) -> str:
    """Extract optimized prompt text from markdown."""
    match = re.search(r"## Stats.*?Optimized Prompt:\s*```(.*?)```", text, re.S)
    return match.group(1).strip() if match else ""


def parse_optimization_file(md_file: Path) -> Optional[OptimizationData]:
    """Parse a single optimization markdown file."""
    try:
        text = md_file.read_text(encoding="utf-8")
        config = extract_json_config(text)

        if not config:
            return None

        prompt_name = build_prompt_name_from_config(config)
        optimizer_model = config.get("prompt_optimizer", {}).get("args", {}).get("model", "")
        optimized_prompt = extract_optimized_prompt_from_text(text)

        if not optimized_prompt:
            return None

        return OptimizationData(prompt_name, optimizer_model, optimized_prompt)

    except Exception as e:
        print(f"Error parsing optimization file {md_file}: {e}")
        return None


def load_prompt_optimizations(folder: str) -> List[OptimizationData]:
    """Load all prompt optimizations from markdown files in the folder."""
    optimizations = []

    for md_file in Path(folder).glob(f"{OPTIMIZATION_RESULT_FILE_FORMAT}*.md"):
        optimization = parse_optimization_file(md_file)
        if optimization:
            optimizations.append(optimization)

    return optimizations


# Dataset weight extraction functions
def extract_trace_links_count_from_text(text: str) -> Optional[int]:
    """Extract traceability links count from text."""
    match = re.search(r"#TraceLinks \(GS\):\s*(\d+)", text)
    return int(match.group(1)) if match else None


def extract_weight_from_file(md_file: Path) -> Optional[Tuple[str, int]]:
    """Extract dataset name and weight from a single file."""
    try:
        text = md_file.read_text(encoding="utf-8")
        config = extract_json_config(text)

        if not config:
            return None

        dataset_name = extract_dataset_name_from_config(config)
        if not dataset_name:
            return None

        weight = extract_trace_links_count_from_text(text)
        if weight is None:
            return None

        return dataset_name, weight

    except Exception as e:
        print(f"Error extracting weight from {md_file}: {e}")
        return None


def extract_dataset_weights(folder: str) -> Dict[str, int]:
    """Extract dataset weights from all markdown files in the folder."""
    weights = {}

    for md_file in Path(folder).glob("*.md"):
        if OPTIMIZATION_RESULT_FILE_FORMAT in md_file.name:
            continue

        weight_data = extract_weight_from_file(md_file)
        if weight_data:
            dataset_name, weight_value = weight_data
            weights[dataset_name] = weight_value

    return weights


# Metrics extraction functions
def extract_metrics_from_text(text: str) -> Optional[MetricsData]:
    """Extract precision, recall, and F1 metrics from text."""
    precision_match = re.search(r"Precision:\s*([\d.]+)", text)
    recall_match = re.search(r"Recall:\s*([\d.]+)", text)
    f1_match = re.search(r"F1:\s*([\d.]+)", text)

    if not (precision_match and recall_match and f1_match):
        return None

    return MetricsData(
        float(precision_match.group(1)),
        float(recall_match.group(1)),
        float(f1_match.group(1))
    )


def determine_all_prompt_names(model: str, prompt_text: str, optimizations: List[OptimizationData]) -> List[str]:
    """Determine ALL prompt names that match the given model and prompt text."""
    normalized_prompt = normalize_prompt(prompt_text)

    if normalize_prompt(KISS_PROMPT) == normalized_prompt:
        return ["KISS-Original"]
    if normalize_prompt(COT_PROMPT) == normalized_prompt:
        return ["COT-Original"]
    for i in range(len(TOT_PROMPTS)):
        if normalize_prompt(TOT_PROMPTS[i] + TOT_QUESTION) == normalized_prompt:
            return [f"ToT-Original-{i+1}"]
    matching_prompts = []
    for opt in optimizations:
        if (opt.optimizer_model == model and
                normalize_prompt(opt.optimized_prompt) == normalized_prompt):
            matching_prompts.append(opt.prompt_name)

    return matching_prompts if matching_prompts else ["unknown"]


def parse_result_file(md_file: Path, optimizations: List[OptimizationData]) -> List[Tuple[str, str, str, MetricsData]]:
    """Parse a single result markdown file and return ALL matching prompt entries."""
    try:
        text = md_file.read_text(encoding="utf-8")
        config = extract_json_config(text)

        if not config:
            return []

        dataset = extract_dataset_name_from_config(config)
        if not dataset:
            return []

        model, prompt_text = extract_classifier_info_from_config(config)
        prompt_names = determine_all_prompt_names(model, prompt_text, optimizations)
        metrics = extract_metrics_from_text(text)

        if not metrics:
            return []

        # Return one entry for each matching prompt name
        results = []
        for prompt_name in prompt_names:
            results.append((dataset, abbreviate_model_name(model), prompt_name, metrics))

        return results

    except Exception as e:
        print(f"Error parsing result file {md_file}: {e}")
        return []


def load_results_with_prompts(folder: str, optimizations: List[OptimizationData]) -> Dict[
    str, Dict[str, Dict[str, Dict[str, float]]]]:
    """Load all results from markdown files in the folder."""
    results = {}

    for md_file in Path(folder).glob("*.md"):
        if OPTIMIZATION_RESULT_FILE_FORMAT in md_file.name:
            continue

        result_entries = parse_result_file(md_file, optimizations)
        for dataset, model, prompt_name, metrics in result_entries:
            results.setdefault(dataset, {}).setdefault(model, {})[prompt_name] = metrics.to_dict()

    return results


# Average calculation functions
def get_all_models_from_results(results: Dict, datasets: set) -> set:
    """Get all unique models across datasets."""
    models = set()
    for dataset in datasets:
        models.update(results[dataset].keys())
    return models


def get_all_prompts_from_results(results: Dict, datasets: set) -> set:
    """Get all unique prompts across datasets."""
    prompts = set()
    for dataset in datasets:
        for model in results[dataset]:
            prompts.update(results[dataset][model].keys())
    return prompts


def calculate_regular_average(results: Dict, datasets: set, models: set, prompts: set) -> Dict:
    """Calculate regular average across datasets."""
    avg_data = {AVERAGE_DATASET: {}}

    for model in models:
        avg_data[AVERAGE_DATASET][model] = {}

        for prompt in prompts:
            metrics_sum = {}
            count = 0

            for dataset in datasets:
                if model in results[dataset] and prompt in results[dataset][model]:
                    metrics = results[dataset][model][prompt]
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            metrics_sum[metric_name] = metrics_sum.get(metric_name, 0.0) + value
                    count += 1

            if count > 0:
                avg_data[AVERAGE_DATASET][model][prompt] = {
                    metric_name: round(float(total / count), 3)
                    for metric_name, total in metrics_sum.items()
                }

    return avg_data


def calculate_weighted_average(results: Dict, datasets: set, models: set,
                               prompts: set, dataset_weights: Dict[str, int]) -> Dict:
    """Calculate weighted average across datasets."""
    weighted_avg_data = {WEIGHTED_AVERAGE_DATASET: {}}

    for model in models:
        weighted_avg_data[WEIGHTED_AVERAGE_DATASET][model] = {}

        for prompt in prompts:
            weighted_metrics_sum = {}
            total_weight = 0

            for dataset in datasets:
                if model in results[dataset] and prompt in results[dataset][model]:
                    metrics = results[dataset][model][prompt]
                    dataset_weight = dataset_weights.get(dataset, 1)

                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            weighted_metrics_sum[metric_name] = (
                                    weighted_metrics_sum.get(metric_name, 0.0) + (value * dataset_weight)
                            )

                    total_weight += dataset_weight

            if total_weight > 0:
                weighted_avg_data[WEIGHTED_AVERAGE_DATASET][model][prompt] = {
                    metric_name: round(float(total / total_weight), 3)
                    for metric_name, total in weighted_metrics_sum.items()
                }

    return weighted_avg_data


def add_averages_to_results(results: Dict, dataset_weights: Dict[str, int]) -> Dict:
    """Add average and weighted average datasets to results."""
    datasets = {d for d in results if d not in [AVERAGE_DATASET, WEIGHTED_AVERAGE_DATASET]}

    if len(datasets) <= 1:
        return results

    models = get_all_models_from_results(results, datasets)
    prompts = get_all_prompts_from_results(results, datasets)

    avg_data = calculate_regular_average(results, datasets, models, prompts)
    weighted_avg_data = calculate_weighted_average(results, datasets, models, prompts, dataset_weights)

    return {**results, **avg_data, **weighted_avg_data}


# LaTeX table generation functions
def setup_jinja_environment(template_file: str) -> jinja2.Environment:
    """Setup Jinja2 environment for template rendering."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(template_file))
    )
    env.trim_blocks = True
    env.lstrip_blocks = True
    return env


def get_sorted_datasets(results: Dict) -> List[str]:
    """Get sorted list of dataset names."""
    datasets = set(results.keys())
    return sorted(datasets, key=create_dataset_sort_key)


def get_sorted_models(results: Dict) -> List[str]:
    """Get sorted list of model names."""
    models = set()
    for dataset_results in results.values():
        models.update(dataset_results.keys())
    return sorted(models)


def get_sorted_prompts(results: Dict) -> List[str]:
    """Get sorted list of prompt names."""
    prompts = set()
    for dataset_results in results.values():
        for model_results in dataset_results.values():
            prompts.update(model_results.keys())
    return sorted(prompts, key=create_prompt_sort_key)


def get_table_from_dict(results: Dict, template_file: str, dataset_weights: Dict[str, int]) -> str:
    """
    Generate a LaTeX table from a dictionary containing results of various models and prompts across datasets.

    Args:
        results: Dictionary with dataset names as keys and nested dicts with model/prompt/metrics
        template_file: Path to the Jinja2 template file for rendering the LaTeX table
        dataset_weights: Dictionary mapping dataset names to their weights

    Returns:
        String containing the LaTeX code for a table summarizing the results
    """
    # Add averages to results
    results_with_avg = add_averages_to_results(results, dataset_weights)
    # Setup Jinja2 environment and render template
    env = setup_jinja_environment(template_file)
    template = env.get_template(os.path.basename(template_file))

    return template.render(
        datasets=get_sorted_datasets(results_with_avg),
        models=get_sorted_models(results_with_avg),
        prompts=get_sorted_prompts(results_with_avg),
        data=results_with_avg,
        date=datetime.today().strftime('%Y-%m-%d')
    )


def generate_table_from_folder(folder: str, template: str, output_tex_file: str):
    """
    Generate a LaTeX table from all markdown files in the folder and save to output file.

    Args:
        folder: The folder containing markdown files with results
        template: The Jinja2 template file for rendering the LaTeX table
        output_tex_file: The output file where the LaTeX table will be saved
    """
    # Load all necessary data
    dataset_weights = extract_dataset_weights(folder)
    optimizations = load_prompt_optimizations(folder)
    results = load_results_with_prompts(folder, optimizations)

    # Generate LaTeX table
    latex_table = get_table_from_dict(results, template, dataset_weights)

    # Save to file
    with open(output_tex_file, "w") as f:
        f.write(latex_table)


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 4:
        print("Usage: python table_generator.py <input_folder> <template_file> <output_tex_file>")
        sys.exit(1)

    generate_table_from_folder(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()