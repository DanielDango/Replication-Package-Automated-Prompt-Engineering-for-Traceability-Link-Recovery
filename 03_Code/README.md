# LiSSA-RATLR: Optimization Extension

This is an extension of the LiSSA-RATLR project that adds an optional optimization step to improve prompts on datasets.

**Goal**: add an optional optimization step into the LiSSA framework to optimize prompts on datasets
<img src=".\LiSSA_RATLR\.github\images\approach_with_optimization.svg" alt="Approach with optimization" style="width: 100%;background-color:white;" /><br/>

**Addition** of new components for optimization in a plant uml class diagram
<img src=".\LiSSA_RATLR\.github\images\plant_uml.svg" alt="Plant UML class diagram of new components" style="width: 100%;background-color:white;" /><br/>
## Short Overview
### Breaking
- disabled TransitiveTraceCommand due to changes in gold standard files
- moved specific ElementeStore methods to Source/TargetElementStore
- removed file extension cutoff in postprocessors
### New Features
- New `optimize` CLI command to optimize prompts on datasets
- New configuration class `OptimizerConfiguration` for the optimization command
- New abstract class `AbstractPromptOptimizer` with multiple implementations for different optimization strategies
- New abstract class `AbstractScorer` with multiple implementations for different scoring strategies
- New abstract class `AbstractEvaluator` with multiple implementations for different evaluation strategies
- Added ability to overwrite the classification prompt from the configuration in the evaluation pipeline
- Added utility methods for cached llm calls in `ChatLanguageModelUtils`
- Added detailed optimization statistics generation in `Statistics`
### Improvements
- Refactored `EvaluateCommand` to load all files in subdirectories
- Refactored `ModuleConfiguration` to add an `argumentFromString` method to overwrite configuration arguments in the software for consistent statistics dumps
- Refactored `ElementStore` to split into separate Source and Target stores in order to mindlessly use methods only available for one of them
- Changed dataset gold standard files to be consistent with the element names by adding / removing file extensions
## Usage
The optimization can be run via CLI. The optimization configuration is provided via the `-c / --config` option:
```bash
java -jar target/ratlr-*-jar-with-dependencies.jar optimize -c example-configs/gradient-optimizer-config.json
```
The configuration can also be a directory containing multiple configurations. All of them will be optimized in sequence.
The available module arguments for each optimizer can be found in the result files.

The optimization can be chained with an evaluation via the `-e / --eval` option:
```bash
java -jar target/ratlr-*-jar-with-dependencies.jar optimize -c example-configs/gradient-optimizer-config.json -e example-configs/simple-config
```
If multiple evaluation configurations are provided, each of them will be evaluated with the optimized prompt.
If multiple optimization configurations are provided, each of them will be evaluated with each evaluation configuration.
In addition, a baseline evaluation is performed with the original prompt from the evaluation configuration. 
This way, the improvement through optimization can be measured with just one command.

### Optimization Strategies
Currently available optimizers are:
> Mock Optimization for Testing: `mock`
>
> Singular naive call to the LLM to improve the prompt: `simple`
>
> Repeated naive calls to the LLM to improve the prompt: `iterative`
>
> Iterative optimization with feedback of still misclassified examples: `feedback`
>
> Gradient Descent Based Automatic Prompt Optimization: `gradient`


### Example Configurations
Example configurations for optimization can be found in the `example-configs` directory.
Note that currently the metric and evaluators are only needed by the gradient optimizer.
The other optimizers do not use them, but they are still required by the configuration.
Mock implementations are provided for testing purposes.

## Detailed List of Changes
Below a detailed list of changes is provided.
### CLI
- MainCLI.java
    - Register optimization command
- TransitiveTraceCommand.java
    - throw unsupported operation exception due to changes in gold standard files
- EvaluateCommand.java
    - refactor loadConfigs method as public static method and load all files in the subdirs
- OptimizeCommand.java
    - new command to optimize prompts
    - -c config option
    - -e evaluate option to be chained after the optimization
    - supports multiple config / eval configurations
### Classifier
- add ClassificationTask record 
  - encapsule a pair of elements with their correct label
- Classifier.java
  - lower level of some info messages to debug
  - add additional classify method frontend for ClassificationTask
  - add abstract setClassificatioPrompt method
    - Usage restricted with architecture test
- PipelineClassifier.java
    - disable setClassificationPrompt method
### Configuration
- ModuleConfiguration.java
  - add argumentFromString method
  - overwrites the argument if already present
  - used after optimization to overwrite the prompt from the evaluation config for correct statistics dump
- OptimizerConfiguration.java
  - new configuration class for the optimization command
  - adds additional modules for optimization:
    - Optimizer
    - Scorer
    - Evaluator
  - mostly a duplicate of Configuration.java
### ElementStore
- ElementStore.java
  - split into Source and Target store classes
  - add size() method
- SourceElementStore.java
  - add getAllElements() method to return all elements in the store
  - add reduce method to get a reduced store with only the given amount of elements
- TargetElementStore.java
    - add getAllElements() method to return all elements in the store
    - add reduce method to get a reduced store with only the reachable elements from a source store
### New: Evaluator
- AbstractEvaluator.java 
  - factory method to create evaluator from configuration, delegate to specific implementations based on name
  - add call method that returns a list of doubles (Scores) for a list of prompts
    - requires Classifier, Scorer and List of ClassificationTasks
- MockEvaluator.java
  - for testing, always returns a list of 1.0 scores for each prompt
- BruteForceEvaluator.java
  - evaluates all prompts equally in a brute force manner
  - respects evaluation budget distributed equally to all prompts
  - returns mean score for each prompt
- UCBanditEvaluator.java
  - evaluates prompts based on the Upper Confidence Bound bandit algorithm
    - optimistically chooses prompts based on their current score and uncertainty bonus
    - default exploration parameter of 1.0
  - respects evaluation budget distributed based on UCB scores
  - returns mean score for each prompt

### Knowledge
- Tracelink.java
    - add compareTo method to order a list of tracelinks
    - add of(...) static factory method
### Postprocessor
- Changed Dataset gold standard files to be consistent with the element names by adding / removing file extensions
- IdProcessor.java
  - remove file extension cutoff
- ReqReqPostprocessor.java
    - remove file extension cutoff
### New: Prompt Optimizer
- AbstractPromptOptimizer.java
  - factory method to create optimizer from configuration, delegate to specific implementations based on name
    - compontents necessary for optimization (to be unified in the future):
      - Scorer
      - Evaluator
      - Classifier
      - ResultAggregator
      - TraceLinkPostprocessor
      - GoldStandard TraceLinks
  - provides abstract optimize method that returns the singular optimized prompt
    - requires source and target store
  - implements some utility methods for specific implementations
- MockOptimizer.java
  - for testing, always returns the original prompt
- SimpleOptimizer.java
  - single naive call to the LLM to improve the prompt
- IterativeOptimizer.java
    - repeated naive calls to the LLM to improve the prompt
    - number of iterations can be configured
- IterativeFeedbackOptimizer.java
    - extends IterativeOptimizer
    - iterative optimization with feedback of still misclassified examples
    - number of iterations can be configured
    - number of misclassified examples to provide as feedback can be configured
- AutomaticPromptOptimizer.java
  - extends IterativeFeedbackOptimizer
  - gradient descent based automatic prompt optimization
  - many configurable parameters for the optimization process
  - based on the paper "Automatic Prompt Optimization with “Gradient Descent” and Beam Search" by Pryzant et al. 2023
    - structure largely translated from their open source python code
    - still under modification and improvement to fit better into the LiSSA framework

### New: Scorer
- AbstractScorer.java
  - factory method to create metric from configuration, delegate to specific implementations based on name
  - add call method that returns a double score for a list of ClassificationTasks
    - requires Classifier and List of ClassificationTasks
  - each prompt is scored against all classification tasks
  - abstract computeScore method to be implemented by specific scorers
- BinaryScorer.java
  - scores based on binary classification -> 1.0 if traceability link is correctly classified, 0.0 otherwise
- MockScorer.java
  - for testing, always returns 1.0
### Utils
- ChatLanguageModelUtils.java
  - new Utility class for cached llm calls
  - add method to get multiple responses from a single prompt
  - add method to get a single response from a list of responses

### Main
- Optimization.java
  - Add new optimization pipeline
  - Largely duplicates Evaluation.java
- Evaluation.java
  - add ability to overwrite the classification prompt from the configuration
  - modify setup() to require String prompt argument
     - if prompt is not empty, overwrite the prompt from the configuration (hacky solution)
     - only used by Optimization to provide correct statistics dump
- Statistics.java
  - add generateOptimizationStatistics methods
  - add escapeMarkdown utility method for printing prompts
  - add configurationToString utility method to format configurations
### Tests
- ArchitectureTest.java
  - add test to restrict usage of setClassificationPrompt method
    - Only allowed in AbstractOptimizer and AbstractScorer implementations
  - add test to restrict usage of evaluation call with overwriting the preconfigured prompt
- add .txt extension to all answer.csv entries