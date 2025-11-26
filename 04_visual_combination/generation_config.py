# Configuration file for the Conceptual Combination module

# path to the directory containing the conceptual combinations
COCOS_DIR = '../03_conceptual_combination/output'

# path to the directory where the generated prompts are saved
PROMPT_DIR = 'prompts-conceptmix'

# path to the directory where the generated images are saved
OUTPUT_DIR = 'output-conceptmix'

# select how to generate the template. Possible values: "llm" or "template"
PROMPT_ORIGIN = 'template'

# if False, the representation of the combined concepts is ignored
USE_COCOS = True

# template of the prompt to query the generative model
PROMPT_TEMPLATE = 'Combine the concepts "{head}" and "{modifier}" to generate something new.'
if USE_COCOS:
    PROMPT_TEMPLATE += ' Consider the following features: {features}.'

# Image generation options
WIDTH = 500
HEIGHT = 500
SEED = 42
MODEL = 'flux' # Using 'flux' as default if model is not provided