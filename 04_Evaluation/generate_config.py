import os
import json
import inspect
import re
from typing import Dict, Any, Optional
# ----------------------
# Helpers
# ----------------------
def get_model_provider(model: str) -> str:
    """
    Returns the provider name based on the model string.
    """
    if model.startswith("gpt-"):
        return "openai"
    elif "llama" in model or "ollama" in model:
        return "ollama"
    else:
        return "unknown"



# ----------------------
# Default fixed parts
# ----------------------
FIXED_MODULES = {
    "gold_standard_configuration": {
        "path": "./datasets/{domain}/{dataset}/answer.csv",
        "hasHeader": "true"
    },
    "source_artifact_provider": {
        "name": "text",
        "args": {
            "artifact_type": "requirement",
            "path": "./datasets/{domain}/{dataset}/high"
        }
    },
    "target_artifact_provider": {
        "name": "text",
        "args": {
            "artifact_type": "requirement",
            "path": "./datasets/{domain}/{dataset}/low"
        }
    },
}

# ----------------------
# Default configurable modules
# ----------------------
EVALUATION_MODULES = {
    "source_preprocessor": {"name": "artifact", "args": {}},
    "target_preprocessor": {"name": "artifact", "args": {}},
    "embedding_creator": {
        "name": "openai",
        "args": {"model": "text-embedding-3-large"}
    },
    "source_store": {"name": "custom", "args": {}},
    "target_store": {
        "name": "cosine_similarity",
        "args": {"max_results": 4}
    },
    "result_aggregator": {"name": "any_connection", "args": {}},
    "tracelinkid_postprocessor": {"name": "identity", "args": {}},
    "classifier": {"name": "mock", "args": {}},
}

OPTIMIZER_MODULES = {
    "prompt_optimizer": {"name": "mock", "args": {}},
    "evaluator": {"name": "mock", "args": {}},
    "metric": {"name": "mock", "args": {}}
}


def build_evaluation_config(dataset: str, domain: str = "req2req", overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a single config for a dataset.

    Args:
        dataset: dataset name (string)
        domain: domain name (default: req2req)
        overrides: dictionary of module overrides, e.g.
            {
              "prompt_optimizer": {"name": "iterative", "args": {"version": 3, "speed": True}}
            }
    """
    config = {
        "cache_dir": f"./cache/{dataset}"
    }

    # Fixed modules (expand with dataset/domain)
    for key, val in FIXED_MODULES.items():
        config[key] = json.loads(json.dumps(val).replace("{dataset}", dataset).replace("{domain}", domain))

    # Configurable modules
    modules = EVALUATION_MODULES.copy()
    if overrides:
        for key, val in overrides.items():
            modules[key] = val

    config.update(modules)
    return config

def build_optimization_config(dataset: str, domain: str = "req2req", overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a single config for a dataset with optimization modules.

    Args:
        dataset: dataset name (string)
        domain: domain name (default: req2req)
        overrides: dictionary of module overrides, e.g.
            {
              "prompt_optimizer": {"name": "iterative", "args": {"version": 3, "speed": True}}
            }
    """
    config = build_evaluation_config(dataset, domain, overrides)

    # Add optimizer modules
    modules = OPTIMIZER_MODULES.copy()
    if overrides:
        for key, val in overrides.items():
            modules[key] = val

    config.update(modules)
    return config

def save_config(config: Dict[str, Any], dataset: str, model: str, filename: str, basedir: str = None):
    """
    Save a config dict to file.

    - If basedir is provided, it is interpreted relative to the caller's file.
    - CONFIG_DIR is appended automatically.
    """
    # Determine caller's directory
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    caller_dir = os.path.dirname(os.path.abspath(caller_file))

    # Resolve basedir relative to caller
    if basedir:
        basedir = os.path.abspath(os.path.join(caller_dir, basedir))
    else:
        basedir = caller_dir

    # Construct full path: basedir + CONFIG_DIR + model + dataset
    dataset_dir = os.path.join(basedir, sanitize_filename(model), sanitize_filename(dataset))
    os.makedirs(dataset_dir, exist_ok=True)

    path = os.path.join(dataset_dir, sanitize_filename(filename))
    with open(path, "w+") as f:
        json.dump(config, f, indent=2)
    return path

def sanitize_filename(name: str) -> str:
    """
    Replace illegal filename characters with underscores.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name)