# Evaluation

## Usage
The evaluation setups here are designed to be used with the provided Makefile.
To run all evaluations, simply execute the following command in the terminal:
``` bash
make all
```

An overview of available make targets can be obtained by running:
``` bash
make help
```

The toplevel [\03_Code](..\03_Code) folder including the source code of this theis is expected to be in the same parent folder as this evaluation folder.
It will renew the jar file and run all optimizations and evaluate them on the same dataset and model. 
To run a specific evaluation, navigate to the respective subfolder and execute:
```bash
java \
-jar ratlr-*-jar-with-dependencies.jar optimize \
-c configs/optimization/$(MODEL)/($DATASET) \
-e configs/req2req/$(MODEL)/($DATASET)
```
Make sure to replace the variables with the desired values.
The invoked optimization pipeline will evaluate each optimization configuration with all evaluation configurations.
Like in the example usage above, folders can also be provided instead of specific configuration files.
All configurations inside the folder and all subfolders will be loaded and used.

## Evaluation Folders
Each subfolder is considered to be a separate evaluation.
It consists of the scripts to generate the configuration files for the optimization and evaluation runs.
Furthermore, related artifacts will be copied into each folder.
The state of each subfolder yields reproducible deterministic results by using the cached values and .jar file.

### Adding new Evaluations
To add a new evaluation a new subfolder has to be created.
Inside this folder two python scripts are expected:
- `generate_configs_optimization.py`: This script generates the configuration files for the optimization runs.
- `generate_configs_r2r.py`: This script generates the configuration files for the evaluations.
The scripts should both place valid configuration files in the `.\configs` subfolder.
They are expected to follow the same structure as the existing scripts in the other evaluation folders.
`configs\TYPE\MODEL\DATASET\my_config.json`
This structure will be assumed when running the optimization and evaluation pipeline through the attached Makefile.

### Output
The detailed outputs for each evaluation and optimization will be stored inside the respective subfolder.
Aggregated results will be stored as a table in the `.\results\tables` folder.
Furthermore, optimized prompts for the WARC dataset will be stored in the `.\results\prompts` folder.

## Configurations
TODO: How do envs work right now? Should they be added to each evaluation folder?

# Sources
- Datasets provided by: T. Hey, D. Fuchß, J. Keimand A. Koziolek, “Replication Package for "Requirements Traceability Link Recovery via Retrieval-Augmented Generation"”. Zenodo, Jan. 31, 2025. doi: 10.5281/zenodo.14779458.
- LiSSA code