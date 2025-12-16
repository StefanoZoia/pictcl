import random
import json
import csv
import os
import inflect
inflect_engine = inflect.engine()

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
            skills, descr, cat, json_descr = load_configs_new(k=1, config_path=config_path)
            writer.writerow(skills)

            image_info = {"skills": skills,
                          "descriptions": descr,
                          "categories": cat,
                          "json_descr": json_descr}
            all_pairs.append(image_info)
            
    with open("output/conceptmix_pairs.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(all_pairs))

def main():
    path_to_concepts = "data/ConceptMix"
    load_random_pairs(path_to_concepts, 5)

if __name__ == "__main__": main()