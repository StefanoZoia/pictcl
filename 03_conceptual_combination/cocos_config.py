# Configuration file for the Conceptual Combination module

# path to the prototyped corpus file
CORPUS_FILE = '../02_prototype_generation/output/prototyped.tsv'

# specify the columns to read as head and modifier
HEAD_COLUMN = 0
MODIFIER_COLUMN = 1

# path to the directory containing the description of typical properties
TYPICAL_PROP_DIR = '../02_prototype_generation/output/prototypes'
# path to the directory containing the description of rigid properties
RIGID_PROP_DIR = None
#RIGID_PROP_DIR = '../02_prototype_generation/demo-output/rigid'

# path to the directory where the combinations are saved
COCOS_DIR = 'output'

# max number of typical properties in the combined concept
MAX_ATTRS = 6