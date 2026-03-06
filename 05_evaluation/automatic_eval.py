import os
import json
import numpy as np
from infer_ci import bootstrap_ci

BASELINE_IMAGE_DIR = "../04_visual_combination/output/images"
BASELINE_SCORE_DIR = "../04_visual_combination/output/scores"

COCOS_IMAGE_DIR = "../04_visual_combination/output/cocos_images"
COCOS_SCORE_DIR = "../04_visual_combination/output/cocos_scores"

USE_COCOS = False

# check that the call to LLM has already been done and return its result
def read_json_file(path):
    # read or generate the output of the llm
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.loads(f.read())
    else:
        #raise FileNotFoundError(f"Missing file at {path}: check your path and run auto_score.py first")
        print(f"Missing file at {path}: check your path and run auto_score.py first")
        return None

def list_images(path):
    return {
        f for f in os.listdir(path)
           if os.path.isfile(os.path.join(path, f))
           and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    }

def main():

    baseline_images = list_images(BASELINE_IMAGE_DIR)
    cocos_images = list_images(COCOS_IMAGE_DIR)

    full_mark_score = list()    #images having all correct answers
    concept_fraction_score = list()

    # for each generated image
    for filename in baseline_images:

        image_name = filename.split(".")[0]

        score_dir = COCOS_SCORE_DIR if (USE_COCOS and filename in cocos_images) else BASELINE_SCORE_DIR

        # load score
        score_path = f"{score_dir}/{image_name}.json"
        img_info = read_json_file(score_path)

        if img_info:
            # add image's individual question scores to the lists
            concept_fraction_score.extend(img_info["scores"])
            full_mark_score.append(np.min(img_info["scores"]))
        
    # compute overall scores with CI
    print(f"Evaluated images: {len(full_mark_score)}")
    print(f"Evaluation questions: {len(concept_fraction_score)}")

    ci = bootstrap_ci(
        y_true = np.ones(len(full_mark_score)),
        y_pred = full_mark_score,
        metric = lambda true, x : np.mean(x),
        confidence_level = 0.95,
        n_resamples = 10000,
        random_state = 322026
    )
    plus_minus = (ci[1][1] - ci[1][0]) / 2 
    print(f"Perfect-scoring images: {np.sum(full_mark_score):.4f} / {len(full_mark_score)}")
    print(f"Proportion of perfect-scoring images: {np.mean(full_mark_score):.4f} ±{plus_minus:.4f}")

    ci = bootstrap_ci(
        y_true = np.ones(len(concept_fraction_score)),
        y_pred = concept_fraction_score,
        metric = lambda true, x : np.mean(x),
        confidence_level = 0.95,
        n_resamples = 10000,
        random_state = 322026
    )
    plus_minus = (ci[1][1] - ci[1][0]) / 2 
    print(f"Perfect-scoring images: {np.sum(concept_fraction_score):.4f} / {len(concept_fraction_score)}")
    print(f"Average score per image: {np.mean(concept_fraction_score):.4f} ±{plus_minus:.4f}")



if __name__ == "__main__": main()