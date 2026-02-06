import random
import json
import csv
import os
import inflect
inflect_engine = inflect.engine()

# load random value from config file
def load_random_value(config_path, config_file):
    file_path = os.path.join(config_path, config_file)
    with open(file_path, 'r') as file:
        data = json.load(file)
        skill = random.choice(list(data['skill'].keys()))
        description = data['skill'][skill]
        if not description:
            description = data['description']
        category = data['category']
    return skill, description, category

# load random combination of degree k
def load_configs_new(k, config_path, specified_skill=None, object_prob=0.25):
    if specified_skill:
        assert(k==1)
    config_files = [f for f in os.listdir(config_path) if f.endswith('.json') and f != 'object.json']

    # decide object number
    num_objects = 1
    if not specified_skill:
        for i in range(k):
            if random.random() < object_prob:
                num_objects += 1
    
    k_other = k + 1 - num_objects
    if specified_skill is not None:
        random_config_files = [specified_skill + '.json']
    else:
        random_config_files = random.choices(config_files, k=k_other)

    max_count = lambda x: max([x.count(i) for i in set(x)]) if len(x) > 0 else 0

    while max_count(random_config_files) > num_objects or random_config_files.count('styles.json') > 1:
        random_config_files = random.choices(config_files, k=k_other)


    skills = []
    descriptions = []
    categories = []
    initial_json = {'objects': []}
    # generate object
    for i in range(num_objects):
        skill, description, category = load_random_value(config_path, 'object.json')
        # make sure skill is not repeated
        while skill in skills:
            skill, description, category = load_random_value(config_path, 'object.json')
        skill_pl = inflect_engine.plural(skill)
        description = description.format(skill=skill, skills=skill_pl)
        initial_json['objects'].append({'id': i+1, 'item': skill})
        skills.append(skill)
        descriptions.append(description)
        categories.append(category)
    
    sequential = True if specified_skill else False
    for i in range(k_other):
        skill, description, category = load_random_value(config_path, random_config_files[i])
        if category == 'style':
            initial_json['style'] = skill
            description = description.format(skill=skill)
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)
        elif category == 'spatial':
            if 'relation' not in initial_json:
                initial_json['relation'] = []
            initial_json['relation'].append({'name': skill, 'description': description, 'ObjectA_id': '?', 'ObjectB_id': '?'})
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)
        else:
            idx = random.choice(range(num_objects))
            while category in initial_json['objects'][idx]:
                idx = random.choice(range(num_objects))
            initial_json['objects'][idx][category] = skill
            object_single = initial_json['objects'][idx]['item']
            object_plural = inflect_engine.plural(object_single)
            description = description.format(skill=skill, object=object_single, objects=object_plural)
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)

    return skills, descriptions, categories, initial_json# load random combination of degree k


# load specified value from config file
def load_specified_value(config_path, config_file, item):
    file_path = os.path.join(config_path, config_file)
    with open(file_path, 'r') as file:
        data = json.load(file)
        description = data['skill'][item]
        if not description:
            description = data['description']
        category = data['category']
    return item, description, category

# load a specified sample
def load_specifed_config(config_path, sample):
    skills = []
    descriptions = []
    categories = []
    initial_json = {'objects': []}

    # generate objects
    i = 0
    for obj in sample["objects"]:
        i+=1
        skill, description, category = load_specified_value(config_path, 'object.json', obj)
        skill_pl = inflect_engine.plural(skill)
        description = description.format(skill=skill, skills=skill_pl)
        initial_json['objects'].append({'id': i, 'item': skill})
        skills.append(skill)
        descriptions.append(description)
        categories.append(category)
    
    for feature in sample["features"]:
        skill, description, category = load_specified_value(config_path, feature["config_file"], feature["name"])
        if category == 'style':
            initial_json['style'] = skill
            description = description.format(skill=skill)
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)
        elif category == 'spatial':
            if 'relation' not in initial_json:
                initial_json['relation'] = []
            initial_json['relation'].append({'name': skill, 'description': description, 'ObjectA_id': '?', 'ObjectB_id': '?'})
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)
        else:
            idx = feature["obj_idx"]
            initial_json['objects'][idx][category] = skill
            object_single = initial_json['objects'][idx]['item']
            object_plural = inflect_engine.plural(object_single)
            description = description.format(skill=skill, object=object_single, objects=object_plural)
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)

    return skills, descriptions, categories, initial_json


def load_all_configs(config_path, specified_skill=None):
    config_files = [f for f in os.listdir(config_path) if f.endswith('.json')]

    skills, descriptions, categories = [], [], []

    for config_file in config_files:
        file_path = os.path.join(config_path, config_file)
        with open(file_path, 'r') as file:
            data = json.load(file)
            for skill in data['skill'].keys():
                description = data['skill'][skill]
                if not description:
                    description = data['description']#.format(skill=skill)
                skills.append(skill)
                descriptions.append(description)
                categories.append(data['category'])
    
    return skills, descriptions, categories

# builds a csv with all concepts in pairs (used to extract relations from conceptnet)
def all_configs_in_pairs(config_path):
    concepts, descriptions, categories = load_all_configs(config_path)
    with open("output/conceptmix_all.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#concept 1", "#concept 2"])
        for i in range(0, len(concepts)+1, 2):
            c1 = concepts[i]
            c2 = concepts[i+1] if len(concepts) > i+1 else concepts[0]
            writer.writerow([c1, c2])

def load_random_pair(config_path, specified_skill = None):
    config_files = [f for f in os.listdir(config_path) if f.endswith('.json') and f != 'object.json']
    if specified_skill is None:
        specified_skill = random.choice(config_files)
    
    skill1, description1, category1 = load_random_value(config_path, "object.json")
    skill2, description2, category2 = load_random_value(config_path, specified_skill)

    return(skill1, skill2)

# loads n ConceptMix configurations with k=1
def load_random_pairs(config_path, n):
    all_pairs = list()

    with open("output/conceptmix_pairs.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#object", "#concept_2"])
        
        for i in range(n):
            skills, descr, cat, json_descr = load_configs_new(k=1, config_path=config_path, object_prob=0)
            writer.writerow(skills)

            image_info = {"skills": skills,
                          "descriptions": descr,
                          "categories": cat,
                          "json_descr": json_descr}
            all_pairs.append(image_info)
            
    with open("output/conceptmix_pairs.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(all_pairs))
        
# loads specific ConceptMix configurations as specified in a file
def load_specified_pairs(config_path, samples_file):
    specified_pairs = None
    with open(samples_file, "r", encoding="utf-8") as outfile:
        specified_pairs = json.load(outfile)

    all_pairs = list()
    with open("output/control_pairs.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#object", "#concept_2"])
        
        for sample in specified_pairs:
            skills, descr, cat, json_descr = load_specifed_config(config_path=config_path, sample=sample)
            writer.writerow(skills)

            image_info = {"skills": skills,
                          "descriptions": descr,
                          "categories": cat,
                          "json_descr": json_descr}
            all_pairs.append(image_info)
            
    with open("output/control_pairs.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(all_pairs))

# loads n ConceptMix object-object configurations with k=1
def load_object_pairs(config_path, n):
    # avoid objects that are not represented in ConceptMix
    AVOID = {"oak tree", "pine tree", "teddy bear", "dirt road"}
    all_pairs = list()
    selected_skills = set()

    while len(all_pairs) < n:
        skills, descr, cat, json_descr = load_configs_new(k=1, config_path=config_path, object_prob=1)
        
        image_info = {"skills": skills,
                    "descriptions": [f'the image contains a combination between "{skills[0]}" and "{skills[1]}"'],
                    "categories": cat,
                    "json_descr": json_descr}
        
        if len(set(skills).intersection(AVOID)) == 0 and not (
                        f"{skills[0]}_{skills[1]}" in selected_skills) and not (
                        f"{skills[1]}_{skills[0]}" in selected_skills):
            selected_skills.add(f"{skills[0]}_{skills[1]}")
            all_pairs.append(image_info)

    with open("output/obj_obj_pair.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#object1", "#object2"])
        for pair in all_pairs:
            writer.writerow(pair["skills"])
            
    with open("output/obj_obj_pair.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(all_pairs))

def main():
    path_to_concepts = "data/ConceptMix"
    load_specified_pairs(path_to_concepts, "data/control_images.json")

if __name__ == "__main__": main()