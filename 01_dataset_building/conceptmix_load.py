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
def load_configs_new(chat_api, k, config_path, specified_skill=None, object_prob=0.25):
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
    initail_config = {'objects': []}
    # generate object
    for i in range(num_objects):
        skill, description, category = load_random_value(config_path, 'object.json')
        # make sure skill is not repeated
        while skill in skills:
            skill, description, category = load_random_value(config_path, 'object.json')
        skill_pl = inflect_engine.plural(skill)
        description = description.format(skill=skill, skills=skill_pl)
        initail_config['objects'].append({'id': i+1, 'item': skill})
        skills.append(skill)
        descriptions.append(description)
        categories.append(category)
    
    sequential = True if specified_skill else False
    for i in range(k_other):
        skill, description, category = load_random_value(config_path, random_config_files[i])
        if category == 'style':
            initail_config['style'] = skill
            description = description.format(skill=skill)
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)
        elif category == 'spatial':
            if 'relation' not in initail_config:
                initail_config['relation'] = []
            initail_config['relation'].append({'name': skill, 'description': description, 'ObjectA_id': '?', 'ObjectB_id': '?'})
        else:
            idx = random.choice(range(num_objects))
            while category in initail_config['objects'][idx]:
                idx = random.choice(range(num_objects))
            initail_config['objects'][idx][category] = skill
            object_single = initail_config['objects'][idx]['item']
            object_plural = inflect_engine.plural(object_single)
            description = description.format(skill=skill, object=object_single, objects=object_plural)
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)

    
    model = "gpt-4o-2024-05-13"
    refine_config_prompt = 'I am trying to create an image containing exactly the following things in a JSON format:\n' + json.dumps(initail_config) + '\n' + 'Could you check if there is "?" left in the JSON? If so, could you fill in the missing part? Make sure it makes sense when you fill the missing part. Do not fill in anything else unless it is indicated by "?". You may add additional objects, but only in the following two cases:\n * It is needed to fill in any "?" (Note when you fill "?", you should use existing objects first. If you still choose to add an object, explain why the existing objects cannot fulfill the need.); or \n * If there is an attribute specified in the JSON that contains relative information (e.g. "size") and there is no other object for reference. (The reason for adding an object for this case is because one cannot tell whether an object is huge without any other object in the image, but we are fine if there is no such attribute mentioned in the JSON. Note other existing object in JSON can be used for reference, and the reference object does not need to be the same object. If you still choose to add an object, explain why the existing objects cannot fulfill the need.)\nDO NOT add any object if none of the above situation is strictly satisifed, and DO NOT try to improve the image in other ways. If you choose to add an object, make sure it fits in the image naturally. Please only add the necessary objects, and the added objects should only have "id" and "item" specified, and should be appended to "objects".'
    completion = chat_api(
        model = model,
        messages = [
            {"role": "user", "content": refine_config_prompt}
        ]
    )
    full_response = completion.choices[0].message.content
    # print(refine_config_prompt)
    print(json.dumps(initail_config))
    print(full_response)
    json_only_prompt = 'Could you respond only the JSON?'
    completion = chat_api(
        model = model,
        messages = [
            {"role": "user", "content": refine_config_prompt},
            {"role": "assistant", "content": full_response},
            {"role": "user", "content": json_only_prompt}
        ]
    )
    json_response = completion.choices[0].message.content
    # print(json_response)
    # check if it starts with ```json and ends with ```, remove if so
    if json_response.startswith('```json'):
        json_response = json_response[7:]
    if json_response.endswith('```'):
        json_response = json_response[:-3]
    try:
        refined_config = json.loads(json_response)
    except:
        print("json_response:", json_response)
        raise ValueError("The refined config is not a valid JSON format")

    # check if id is 1, 2, 3, ...
    for i, object in enumerate(refined_config['objects']):
        assert(int(object['id']) == i + 1)
    extra_skills = []
    extra_descriptions = []
    extra_categories = []
    for object in refined_config['objects'][num_objects:]:
        extra_skills.append(object['item'])
        extra_descriptions.append(f"the image contain one {object['item']}.")
        extra_categories.append('object')
    if 'relation' in refined_config:
        for relation in refined_config['relation']:
            objectA = refined_config['objects'][int(relation['ObjectA_id'])-1]['item']
            objectB = refined_config['objects'][int(relation['ObjectB_id'])-1]['item']
            if objectA == objectB:
                objectB = "another " + objectB
            description = relation['description'].format(ObjectA=objectA, ObjectB=objectB)
            skills.append(relation['name'])
            descriptions.append(description)
            categories.append('spatial')

    return skills, descriptions, categories, refined_config


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
    with open("output/conceptmix.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#object", "#concept 2"])
        for i in range(n):
            c1, c2 = load_random_pair(config_path)
            writer.writerow([c1, c2])

def main():
    path_to_concepts = "data/ConceptMix"
    #all_configs_in_pairs(path_to_concepts)
    load_random_pairs(path_to_concepts, 5)


if __name__ == "__main__": main()