import csv
from scipy.stats import binomtest
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json
import os


def compute_binomtest(name, n_pictcl, n_baseline):

    n_imgs = n_pictcl + n_baseline

    print(f"\n{name}")
    print(f"Total pictcl: {n_pictcl}/{n_imgs} = {n_pictcl/n_imgs:.2%}")
    
    pictcl_test = binomtest(k=n_pictcl, n=n_imgs, p=0.5, alternative='greater')
    ci = binomtest(k=n_pictcl, n=n_imgs, p=0.5, alternative='two-sided').proportion_ci(confidence_level=0.9)
    print(f"One-sided binomial test p-value = {pictcl_test.pvalue}")
    print(f"Clopper-Pearson 90% two-sided CI: {ci}")




def plot_preference_results(results, splitname="unnamed", sort_by_proportion=True,
                            xlim=(0.3, 0.7), fig_size=None):
    """
    results: list of (name, n_pictcl, n_baseline) tuples
    """
    #fig, ax = plt.subplots()
    fig, ax = plt.subplots(figsize=fig_size)

    if sort_by_proportion:
        results = sorted(results, key = lambda r: r[1] / (r[1] + r[2]), reverse=True)

    for i, (name, n_pictcl, n_baseline) in enumerate(results):
        n = n_pictcl + n_baseline
        p = n_pictcl / n
        test = binomtest(k=n_pictcl, n=n, p=0.5, alternative='greater')
        ci = binomtest(k=n_pictcl, n=n, p=0.5, alternative='two-sided').proportion_ci(confidence_level=0.9)

        color = 'steelblue' if p > 0.5 else 'tomato'
        significant = test.pvalue < 0.05 or test.pvalue > 0.95

        ax.plot([ci.low, ci.high], [i, i], color=color, linewidth=2) #two-sided 90% CI plot
        ax.plot(p, i, 'o', color=color, markersize=8,
                markeredgecolor='black' if significant else 'none', markeredgewidth=1.5)
        
        ax.text(ci.low - 0.02, i, f"{n_pictcl/n:.2%}", va='center', ha='right',
                fontsize=8)
        ax.text(1.02, i, f"p={test.pvalue:.3f}  n={n}", va='center',
                fontsize=8, transform=ax.get_yaxis_transform())

    ax.axvline(0.5, color='gray', linestyle='--', linewidth=1, label='No preference')
    ax.set_yticks(range(len(results)))
    ax.set_yticklabels([r[0] for r in results])
    ax.set_xlabel(r'Proportion preferring $\mathregular{PiCT^{CL}}$')
    ax.set_ylim(len(results) - 0.5, -0.5)
    ax.set_xlim(xlim)
    ax.set_title(r'$\mathregular{PiCT^{CL}}$ vs. Baseline — Human Preference' +
                 (f" by {splitname}" if splitname != "overall" else ""))

    blue_patch = mpatches.Patch(color='steelblue', label=r'$\mathregular{PiCT^{CL}}$ preferred')
    red_patch = mpatches.Patch(color='tomato', label='Baseline preferred')
    #ax.legend(handles=[blue_patch, red_patch], loc='lower right')
    plt.tight_layout()
    plt.savefig(f"plots/human-eval-{splitname}.pdf")
    plt.show()




def read_sessions(filename):
    sessions = dict()

    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        reader.__next__()
        for row in reader:
            session_id = row[1]
            winner_image = row[4]
            winner_position = row[5]

            if session_id not in sessions:
                sessions[session_id] = list()

            sessions[session_id].append({"winner": winner_image, "position": winner_position})

    return sessions

def filter_trusted_sessions(all_sessions):

    trusted_sessions = dict()
    for s in all_sessions:
        answers = all_sessions[s]
        trusted = len(answers) >= 30
        
        for a in answers:
            if "/static/control_losers" in a["winner"]:
                trusted = False
        if trusted:
            trusted_sessions[s] = all_sessions[s]
            
    print(f"Trusted sessions: {len(trusted_sessions)}")
    return trusted_sessions


def read_cocos_output(file_path):
    head = None
    modifier = None
    combination_result = None
    
    if not os.path.isfile(file_path):
        return None
    
    with open(file_path, encoding="utf-8") as f:
        input_lines = f.readlines()
        # remove comments and void lines
        input_lines = [x.strip() for x in input_lines 
                        if x.strip() != '' and x.strip()[0] != '#']
        
        for line in input_lines:
            line = [k.strip() for k in line.split(':', maxsplit=1)]

            # read the head
            if line[0] == 'Head Concept Name':
                head = line[1]

            # read the modifier
            if line[0] == 'Modifier Concept Name':
                modifier = line[1]
            
            # if the combination is successful, read the result
            if line[0] == 'Result':
                combination_result = json.loads(line[1])
        
    if combination_result is None:
        return None

    features = list(combination_result.keys())
    features.remove('@scenario_probability')
    features = [f.replace("-", "not ", 1) if f[0] == "-" else f for f in features]
    features = [f.replace("-", " ").replace("_", " ") for f in features]

    return features

def load_config_file(filename):
    jsonobj = None
    with open(filename, encoding="utf-8") as jsonconfig:
        jsonobj = json.load(jsonconfig)

    skill_to_category = dict()
    for skill in jsonobj["skill"]:
        skill_to_category[skill.replace(" ", "_")] = jsonobj["category"]
    return skill_to_category

def load_config_files(dirname):
    skill_to_category = dict()
    for filename in os.listdir(dirname):
        skill_to_category.update(load_config_file(dirname + "/" + filename))
    return skill_to_category

DIFFICULTY = {
    "green": "easy",
    "orange": "easy",
    "pink": "easy",
    "purple": "easy",
    "red": "easy",
    "yellow": "easy",
    "2": "easy",
    "3": "easy",
    "heart": "easy",
    "square": "easy",
    "triangle": "easy",
    "huge": "easy",
    "fluffy": "easy",
    "metallic": "easy",
    "behind": "easy",
    "in_front_of": "easy",
    "left": "easy",
    "top": "easy",
    "cartoon": "easy",
    "ink": "easy",
    "oil_painting": "easy",
    "photorealism": "easy",
    "pop_art": "easy",
    "surrealism": "easy",
    "watercolor": "easy",
    "black": "hard",
    "blue": "hard",
    "brown": "hard",
    "gray": "hard",
    "white": "hard",
    "4": "hard",
    "circle": "hard",
    "rectangle": "hard",
    "tiny": "hard",
    "glass": "hard",
    "above": "hard",
    "below": "hard",
    "bottom": "hard",
    "inside": "hard",
    "outside": "hard",
    "right": "hard",
    "abstract": "hard",
    "cubism": "hard",
    "expressionism": "hard",
    "graffiti": "hard",
    "impressionism": "hard",
    "manga": "hard",
    "pixel_art": "hard",
    "sketch": "hard"
}



def split_on_difficulty(trusted_sessions):
    difficulties = dict()

    for s in trusted_sessions:
        for curr_ans in trusted_sessions[s]:
            if "/static/control_" not in curr_ans["winner"]:
                image_name = curr_ans["winner"].split("/")[-1].replace(".jpeg", "").replace("ooc_", "")
                obj = image_name.split("_")[0]
                concept_2 = image_name.split("_", 1)[1]
                dif = DIFFICULTY[concept_2] if concept_2 in DIFFICULTY else "object"
                pictcl_wins = None
                if "/static/cocos_images" in curr_ans["winner"]:
                    pictcl_wins = True
                elif "/static/images" in curr_ans["winner"]:
                    pictcl_wins = False
                else:
                    print(curr_ans["winner"])
                    raise(Exception)
                
                if dif in difficulties:
                    if pictcl_wins:
                        difficulties[dif] = {"n_pictcl": difficulties[dif]["n_pictcl"] + 1,
                                        "n_baseline": difficulties[dif]["n_baseline"]}
                    else:
                        difficulties[dif] = {"n_pictcl": difficulties[dif]["n_pictcl"],
                                        "n_baseline": difficulties[dif]["n_baseline"] + 1}

                else:
                    difficulties[dif] = {"n_pictcl": 1 if pictcl_wins else 0,
                                    "n_baseline": 0 if pictcl_wins else 1}
                    
    res = list()     
    for dif in difficulties:
        compute_binomtest(dif, difficulties[dif]["n_pictcl"], difficulties[dif]["n_baseline"])
        res.append((dif, difficulties[dif]["n_pictcl"], difficulties[dif]["n_baseline"]))
    plot_preference_results(res, splitname="difficulty")

def split_on_concept_category(trusted_sessions):
    skill_to_cat = load_config_files("../01_dataset_building/data/ConceptMix")
    categories = dict({"object excluded ooc":  {"n_pictcl": 0,
                                                "n_baseline": 0}})

    for s in trusted_sessions:
        for curr_ans in trusted_sessions[s]:
            if "/static/control_" not in curr_ans["winner"]:
                image_name = curr_ans["winner"].split("/")[-1].replace(".jpeg", "").replace("ooc_", "")
                obj = image_name.split("_")[0]
                concept_2 = image_name.split("_", 1)[1]
                cat = skill_to_cat[concept_2]
                pictcl_wins = None
                if "/static/cocos_images" in curr_ans["winner"]:
                    pictcl_wins = True
                elif "/static/images" in curr_ans["winner"]:
                    pictcl_wins = False
                else:
                    print(curr_ans["winner"])
                    raise(Exception)
                
                if cat in categories:
                    if pictcl_wins:
                        categories[cat] = {"n_pictcl": categories[cat]["n_pictcl"] + 1,
                                        "n_baseline": categories[cat]["n_baseline"]}
                    else:
                        categories[cat] = {"n_pictcl": categories[cat]["n_pictcl"],
                                        "n_baseline": categories[cat]["n_baseline"] + 1}

                else:
                    categories[cat] = {"n_pictcl": 1 if pictcl_wins else 0,
                                    "n_baseline": 0 if pictcl_wins else 1}
                    

                if cat == "object" and "ooc_" not in curr_ans["winner"]:
                    if pictcl_wins:
                        categories["object excluded ooc"] = {"n_pictcl": categories["object excluded ooc"]["n_pictcl"] + 1,
                                        "n_baseline": categories["object excluded ooc"]["n_baseline"]}
                    else:
                        categories["object excluded ooc"] = {"n_pictcl": categories["object excluded ooc"]["n_pictcl"],
                                        "n_baseline": categories["object excluded ooc"]["n_baseline"] + 1}

    res = list()    
    for cat in categories:
        compute_binomtest(cat, categories[cat]["n_pictcl"], categories[cat]["n_baseline"])
        res.append((cat, categories[cat]["n_pictcl"], categories[cat]["n_baseline"]))
    plot_preference_results(res, splitname="category")

def split_on_objects(trusted_sessions):
    objects = dict()

    for s in trusted_sessions:
        for curr_ans in trusted_sessions[s]:
            if "/static/control_" not in curr_ans["winner"]:
                image_name = curr_ans["winner"].split("/")[-1].replace(".jpeg", "").replace("ooc_", "")
                obj = image_name.split("_")[0]
                concept_2 = image_name.split("_")[1]
                pictcl_wins = None
                if "/static/cocos_images" in curr_ans["winner"]:
                    pictcl_wins = True
                elif "/static/images" in curr_ans["winner"]:
                    pictcl_wins = False
                else:
                    print(curr_ans["winner"])
                    raise(Exception)
                
                if obj in objects:
                    if pictcl_wins:
                        objects[obj] = {"n_pictcl": objects[obj]["n_pictcl"] + 1,
                                        "n_baseline": objects[obj]["n_baseline"]}
                    else:
                        objects[obj] = {"n_pictcl": objects[obj]["n_pictcl"],
                                        "n_baseline": objects[obj]["n_baseline"] + 1}

                else:
                    objects[obj] = {"n_pictcl": 1 if pictcl_wins else 0,
                                    "n_baseline": 0 if pictcl_wins else 1}
                    
    res = list()
    for obj in objects:
        compute_binomtest(obj, objects[obj]["n_pictcl"], objects[obj]["n_baseline"])
        res.append((obj, objects[obj]["n_pictcl"], objects[obj]["n_baseline"]))
    plot_preference_results(res, splitname="object", xlim=(0, 1), fig_size=(6.5,18))

def find_safe_images(trusted_sessions):
    safe_images = dict()
    unsafe_images = list()

    for s in trusted_sessions:
        for curr_ans in trusted_sessions[s]:
            if "/static/control_" not in curr_ans["winner"]:
                image_name = curr_ans["winner"].split("/")[-1].replace(".jpeg", "")
                pictcl_wins = None
                if "/static/cocos_images" in curr_ans["winner"]:
                    pictcl_wins = True
                elif "/static/images" in curr_ans["winner"]:
                    pictcl_wins = False
                else:
                    print(curr_ans["winner"])
                    raise(Exception)
                
                if image_name in safe_images:
                    if safe_images[image_name]["pictcl_preferred"] == pictcl_wins:
                        safe_images[image_name] = {"answers_number": safe_images[image_name]["answers_number"] + 1,
                                                   "pictcl_preferred": pictcl_wins}
                    else:
                        safe_images.pop(image_name)
                        unsafe_images.append(image_name)

                elif image_name not in unsafe_images:
                    safe_images[image_name] = {"answers_number": 1,
                                               "pictcl_preferred": pictcl_wins}
                    

    asc = {k: v for k, v in sorted(safe_images.items(), key=lambda item: item[1]["answers_number"], reverse=True)}
    print(asc)
    
def find_prompts_with_cocos_features(trusted_sessions):
    BASE_PROMPTS = "../04_visual_combination/intermediate/baseline_prompts"
    PROMPTS = "../04_visual_combination/intermediate/pictcl_prompts"
    COCOS = "../03_conceptual_combination/output"
    
    n_features_in_prompt = dict()
    new_features_in_prompt = dict()
    for file in os.listdir(PROMPTS):
        image_name = file.replace(".txt", "")
        obj = image_name.split("_")[0]
        concept_2 = image_name.split("_")[1]

        features = read_cocos_output(f"{COCOS}/{file.replace("ooc_", "")}")
        if features:
            with open(f"{PROMPTS}/{file}", encoding="utf-8") as promptfile:
                prompt = promptfile.read()
            with open(f"{BASE_PROMPTS}/{file}", encoding="utf-8") as promptfile:
                base_prompt = promptfile.read()

            count = 0
            count_new = 0
            # count how many features extracted by cocos appear in the prompt
            for feature in features:
                if feature in prompt:
                    count+=1
                    if feature not in base_prompt:
                        count_new+=1
            n_features_in_prompt[image_name] = count
            new_features_in_prompt[image_name] = count_new
    
    n_pictcl = dict()
    n_baseline = dict()
    for s in trusted_sessions:
        for curr_ans in trusted_sessions[s]:
            if "/static/control_" not in curr_ans["winner"]:
                image_name = curr_ans["winner"].split("/")[-1].replace(".jpeg", "")
                concepts = curr_ans["winner"].split("/")[-1].replace(".jpeg", "").replace("ooc_", "")
                obj = concepts.split("_")[0]
                concept_2 = concepts.split("_")[1]
                pictcl_wins = None
                if "/static/cocos_images" in curr_ans["winner"]:
                    pictcl_wins = True
                elif "/static/images" in curr_ans["winner"]:
                    pictcl_wins = False
                else:
                    print(curr_ans["winner"])
                    raise(Exception)
                
                if image_name not in n_pictcl:
                    n_pictcl[image_name] = 0
                if image_name not in n_baseline:
                    n_baseline[image_name] = 0
                
                if pictcl_wins:
                    n_pictcl[image_name] += 1
                else:
                    n_baseline[image_name] += 1


    for img in sorted(new_features_in_prompt.keys(), key=lambda x:new_features_in_prompt[x]):
        n_evals = n_pictcl[img] + n_baseline[img]
        perc_pictcl = n_pictcl[img] / n_evals
        print(f"{img:30} new_feats: {new_features_in_prompt[img]:2}, feats: {n_features_in_prompt[img]:2}, n_evals:{n_evals:3}, perc_pictcl: {perc_pictcl:.2%}")

    # plot preferences split by number of new features introduced in the prompt
    res = list()
    for n in range(max(new_features_in_prompt.values())):
        ncocos_n = 0
        nbaseline_n = 0
        for img in new_features_in_prompt.keys():
            if new_features_in_prompt[img] == n:
                ncocos_n += n_pictcl[img]
                nbaseline_n += n_baseline[img]

        compute_binomtest(f"{n} New Features", ncocos_n, nbaseline_n)
        res.append((f"{n} New Features", ncocos_n, nbaseline_n))

    plot_preference_results(res, splitname="n_new_features", sort_by_proportion=False)

    # plot preferences split by number of TCL features in the prompt
    res = list()
    for n in range(max(n_features_in_prompt.values())):
        ncocos_n = 0
        nbaseline_n = 0
        for img in n_features_in_prompt.keys():
            if n_features_in_prompt[img] == n:
                ncocos_n += n_pictcl[img]
                nbaseline_n += n_baseline[img]

        compute_binomtest(f"{n} Features", ncocos_n, nbaseline_n)
        res.append((f"{n} Features", ncocos_n, nbaseline_n))

    plot_preference_results(res, splitname="n_features", sort_by_proportion=False)

def compute_overall(trusted_sessions):
    i = 0
    count_pictcl = 0
    count_baseline = 0        
    count_ooc_pictcl = 0
    count_ooc_baseline = 0
    count_left = 0
    count_right = 0

    for s in trusted_sessions:
        for curr_ans in trusted_sessions[s]:
            i+=1
            if "/static/control_" not in curr_ans["winner"]:
                if "/static/cocos_images" in curr_ans["winner"]:
                    count_pictcl += 1
                    if "ooc_" in curr_ans["winner"]:
                        count_ooc_pictcl += 1
                elif "/static/images" in curr_ans["winner"]:
                    count_baseline += 1
                    if "ooc_" in curr_ans["winner"]:
                        count_ooc_baseline += 1
                else:
                    print(curr_ans["winner"])

                if "right" in curr_ans["position"]:
                    count_right += 1
                elif "left" in curr_ans["position"]:
                    count_left += 1
                else:
                    print(curr_ans["position"])



    #print(i)
    compute_binomtest("Overall", count_pictcl, count_baseline)
    compute_binomtest("Object combinations", count_ooc_pictcl, count_ooc_baseline)
    plot_preference_results([("Overall", count_pictcl, count_baseline),
                             ("Object combinations", count_ooc_pictcl, count_ooc_baseline)],
                            splitname="overall", sort_by_proportion=False, fig_size=(5,2))


def main():
    sessions = read_sessions("human_eval_results/evaluation-final.csv")
    trusted_sessions = filter_trusted_sessions(sessions)

    compute_overall(trusted_sessions)

    find_safe_images(trusted_sessions)
    
    split_on_difficulty(trusted_sessions)
    split_on_concept_category(trusted_sessions)
    split_on_objects(trusted_sessions)

    find_prompts_with_cocos_features(trusted_sessions)

if __name__ == "__main__":
    main()

