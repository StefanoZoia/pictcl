import json
import os
import csv
import inflect
inflect_engine = inflect.engine()

def read_json_file(path):
    with open(path, encoding="utf-8") as f:
        return json.loads(f.read())
    
def load_fixed_value(config_path, config_file, value):
    file_path = os.path.join(config_path, config_file)
    with open(file_path, 'r') as file:
        data = json.load(file)
        description = data['skill'][value]
        if not description:
            description = data['description']
        category = data['category']
    return value, description, category
    
def main_use_everything():
    all_pairs = list()

    with open("output/300_pairs.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#object", "#concept_2"])


        for descr in read_json_file("data/300_refined_config_k=1.json"):
            skills = []
            descriptions = []
            categories = []

            object_1 = descr["objects"][0]["item"]
            # retrieve data about the object
            config_path = "data/ConceptMix"
            skill, description, category = load_fixed_value(config_path, "object.json", object_1)
            skill_pl = inflect_engine.plural(skill)
            description = description.format(skill=skill, skills=skill_pl)

            skills.append(skill)
            descriptions.append(description)
            categories.append(category)

            config_file = None
            value = None
            if "relation" in descr:
                #TODO spatial + added object
                config_file = "spatial.json"
                value = descr["relation"][0]["name"]
            elif "style" in descr:
                # style
                config_file = "style.json"
                value = descr["style"]
            elif "color" in descr["objects"][0]:
                # color
                config_file = "color.json"
                value = descr["objects"][0]["color"]
                pass
            elif "number" in descr["objects"][0]:
                # number
                config_file = "number.json"
                value = descr["objects"][0]["number"]
            elif "shape" in descr["objects"][0]:
                # shape
                config_file = "shape.json"
                value = descr["objects"][0]["shape"]
            elif "size" in descr["objects"][0]:
                # size
                config_file = "size.json"
                value = descr["objects"][0]["size"]
                pass
            elif "texture" in descr["objects"][0]:
                # texture
                config_file = "texture.json"
                value = descr["objects"][0]["texture"]
            elif len(descr["objects"]) == 2:
                # object
                config_file = "object.json"
                value = descr["objects"][1]["item"]

            skill, description, category = load_fixed_value(config_path, config_file, value)

            # format description
            if category == "object":
                skill_pl = inflect_engine.plural(skill)
                description = description.format(skill=skill, skills=skill_pl)
            elif category == "color":
                #TODO: implement all cases
                pass

            skills.append(skill)
            descriptions.append(description)
            categories.append(category)

            # code from conceptmix_load.load_random_pairs
            writer.writerow(skills)

            image_info = {"skills": skills,
                        "descriptions": descriptions,
                        "categories": categories,
                        "json_descr": descr}
            all_pairs.append(image_info)
            
            with open(f"output/refined-jsons/{skills[0]}_{skills[1]}.json", "w", encoding="utf-8") as jsonfile:
                jsonfile.write(json.dumps(image_info))
                    
    with open("output/300_pairs.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(all_pairs))


def main_rebuild_descriptions():
    all_pairs = list()

    with open("output/300_pairs.tsv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t", lineterminator="\n")
        writer.writerow(["#object", "#concept_2"])


        for descr in read_json_file("data/300_refined_config_k=1.json"):
            skills = []
            descriptions = []
            categories = []
            initial_json = {'objects': []}

            object_1 = descr["objects"][0]["item"]
            # retrieve data about the object
            config_path = "data/ConceptMix"
            skill, description, category = load_fixed_value(config_path, "object.json", object_1)
            skill_pl = inflect_engine.plural(skill)
            description = description.format(skill=skill, skills=skill_pl)
            
            initial_json['objects'].append({'id': 1, 'item': skill})
            skills.append(skill)
            descriptions.append(description)
            categories.append(category)

            config_file = None
            value = None
            if "relation" in descr:
                #TODO spatial + added object
                config_file = "spatial.json"
                value = descr["relation"][0]["name"]
            elif "style" in descr:
                # style
                config_file = "style.json"
                value = descr["style"]
            elif "color" in descr["objects"][0]:
                # color
                config_file = "color.json"
                value = descr["objects"][0]["color"]
                pass
            elif "number" in descr["objects"][0]:
                # number
                config_file = "number.json"
                value = descr["objects"][0]["number"]
            elif "shape" in descr["objects"][0]:
                # shape
                config_file = "shape.json"
                value = descr["objects"][0]["shape"]
            elif "size" in descr["objects"][0]:
                # size
                config_file = "size.json"
                value = descr["objects"][0]["size"]
                pass
            elif "texture" in descr["objects"][0]:
                # texture
                config_file = "texture.json"
                value = descr["objects"][0]["texture"]
            elif len(descr["objects"]) == 2:
                # object
                config_file = "object.json"
                value = descr["objects"][1]["item"]

            skill, description, category = load_fixed_value(config_path, config_file, value)
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
            elif category == 'object':
                skill_pl = inflect_engine.plural(skill)
                description = description.format(skill=skill, skills=skill_pl)
                initial_json['objects'].append({'id': 2, 'item': skill})
                skills.append(skill)
                descriptions.append(description)
                categories.append(category)
            else:
                initial_json['objects'][0][category] = skill
                object_single = initial_json['objects'][0]['item']
                object_plural = inflect_engine.plural(object_single)
                description = description.format(skill=skill, object=object_single, objects=object_plural)
                skills.append(skill)
                descriptions.append(description)
                categories.append(category)


            writer.writerow(skills)

            image_info = {"skills": skills,
                          "descriptions": descriptions,
                          "categories": categories,
                          "json_descr": initial_json}
            all_pairs.append(image_info)

    with open("output/300_pairs.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(all_pairs))


if __name__ == "__main__":
    main_rebuild_descriptions()