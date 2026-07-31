# Configuration file for the T2I generation and evaluation module

# path to the directory containing the initial json description files
IMG_CONFIG_INFO = '../01_dataset_building/output/control_pairs.json'
# path to the directory containing the conceptual combinations
COCOS_DIR = '../03_conceptual_combination/output'
# set to True for object-object combination, False for normal ConceptMix image compositions
IS_COMBINATION = False
# if True, read and use the representation of the combined concepts by TCL
USE_TCL = True

# path to the directory where the refined jsons are saved
REF_CONFIG_DIR = 'intermediate/refined-jsons' #NOTE: independent by the use of cocos
# path to the directory where the generated prompts are saved
PROMPT_DIR = f'intermediate/{'pictcl_' if USE_TCL else 'baseline_'}prompts'
# path to the directory where the generated images are saved
IMAGE_DIR = f'output/{'pictcl_' if USE_TCL else 'baseline_'}images'

# path to the directory where the generated evaluation questions are saved
QUESTIONS_DIR = f'intermediate/{'pictcl_' if USE_TCL else 'baseline_'}questions'
# path to the directory where the generated evaluation scores are saved
SCORE_DIR = f'output/{'pictcl_' if USE_TCL else 'baseline_'}scores'

# text to text model used to refine the json and to generate the prompt
TEXT_API = 'OpenAI'  # APIs to use: 'Pollinations' or 'OpenAI'
TEXT_MODEL = 'gpt-5.2-2025-12-11'

# Image generation options
WIDTH = 1024
HEIGHT = 1024
SEED = 42   # only used by pollinations to generate reproducible images
T2I_API = TEXT_API  # APIs to use: 'Pollinations' or 'OpenAI'
T2I_MODEL = 'gpt-image-1'