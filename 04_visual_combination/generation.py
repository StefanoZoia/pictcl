import requests
import generation_config as cfg
import os
import json
import time
import base64
from openai import OpenAI

# functions for text-to-image generation

def save_image(binary_img, image_path):
    # Writing the content to a new file
    with open(image_path, 'xb') as file:
        file.write(binary_img)
        # Logging completion message
        print(f'Generated image saved to {image_path}.')

def pollinations_generate_image(prompt):

    width = cfg.WIDTH
    height = cfg.HEIGHT
    seed = cfg.SEED
    model = cfg.T2I_MODEL

    image_url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&seed={seed}&model={model}"

    limit = 10  # max n of retries
    delay = 5   # n of seconds to wait between retries
    retried = 0
    while retried < limit:
        if retried > 0:
            time.sleep(delay)

        # Fetching the image from the URL
        response = requests.get(image_url)
        if response:
            return response.content
        else:
            retried += 1
            print(f'>>>> Warning - error in image generation: {response.status_code} {response.reason} - failed attempt {retried}/{limit}')
    
    raise Exception("Unable to get a generated image")

def openai_generate_image(prompt):
    client = OpenAI()

    width = cfg.WIDTH
    height = cfg.HEIGHT
    model = cfg.T2I_MODEL

    limit = 10  # max n of retries
    delay = 5   # n of seconds to wait between retries
    retried = 0
    while retried < limit:
        if retried > 0:
            time.sleep(delay)
        try:
            img = client.images.generate(
                model=model,
                prompt=prompt,
                n=1,    # number of images to generate
                size=f"{width}x{height}",
                output_format="jpeg"
            )

            image_bytes = base64.b64decode(img.data[0].b64_json)
            return image_bytes
        except Exception as e:
            retried += 1
            print(f'>>>> Warning - error in image generation: {e} - failed attempt {retried}/{limit}')
    
    raise Exception("Unable to get a generated image")

def generate_image(prompt):
    if cfg.T2I_API == "OpenAI":
        return openai_generate_image(prompt)
    elif cfg.T2I_API == "Pollinations":
        return pollinations_generate_image(prompt)
    else:
        raise NotImplementedError(f"Invalid API specified: {cfg.T2I_API}")

# functions for text-to-text generation

def save_textual_data(data, filepath):
    # Writing the content to a new file
    if isinstance(data, (dict, list)):
        data = json.dumps(data) 
    if data:
        with open(filepath, 'x', encoding='utf-8') as file:
            file.write(data)

def pollinations_generate_text(messages):
    payload = {
        "model": cfg.TEXT_MODEL,
        "messages": messages
    }

    limit=10
    delay=1
    retried = 0
    while retried < limit:
        if retried > 0:
            time.sleep(delay)

        response = requests.post("https://text.pollinations.ai/openai", json=payload)

        if response:
            return response.json()['choices'][0]['message']['content']
        else:
            retried += 1
            print(f'>>>> Warning - error in text generation: {response.status_code} - failed attempt {retried}/{limit}')
    
    raise Exception("Unable to get a response from LLM")

def openai_generate_text(messages):
    client = OpenAI()

    limit = 10  # max n of retries
    delay = 1   # n of seconds to wait between retries
    retried = 0
    while retried < limit:
        if retried > 0:
            time.sleep(delay)
        try:
            response = client.responses.create(
                model=cfg.TEXT_MODEL,
                input=messages
            )
            return response.output_text
        except Exception as e:
            retried += 1
            print(f'>>>> Warning - error in text generation: {e} - failed attempt {retried}/{limit}')
    
    raise Exception("Unable to get a response from LLM")

def generate_text(messages):
    if cfg.TEXT_API == "OpenAI":
        return openai_generate_text(messages)
    elif cfg.TEXT_API == "Pollinations":
        return pollinations_generate_text(messages)
    else:
        raise NotImplementedError(f"Invalid API specified: {cfg.TEXT_API}")
    

# use LLM to refine the image configuration json
def refine_info(img_info):
    initial_json = img_info["json_descr"]

    refine_json_prompt = 'I am trying to create an image containing exactly the following things in a JSON format:\n' + json.dumps(initial_json) + '\n' + 'Could you check if there is "?" left in the JSON? If so, could you fill in the missing part? Make sure it makes sense when you fill the missing part. Do not fill in anything else unless it is indicated by "?". You may add additional objects, but only in the following two cases:\n * It is needed to fill in any "?" (Note when you fill "?", you should use existing objects first. If you still choose to add an object, explain why the existing objects cannot fulfill the need.); or \n * If there is an attribute specified in the JSON that contains relative information (e.g. "size") and there is no other object for reference. (The reason for adding an object for this case is because one cannot tell whether an object is huge without any other object in the image, but we are fine if there is no such attribute mentioned in the JSON. Note other existing object in JSON can be used for reference, and the reference object does not need to be the same object. If you still choose to add an object, explain why the existing objects cannot fulfill the need.)\nDO NOT add any object if none of the above situation is strictly satisifed, and DO NOT try to improve the image in other ways. If you choose to add an object, make sure it fits in the image naturally. Please only add the necessary objects, and the added objects should only have "id" and "item" specified, and should be appended to "objects".'
    messages = [
        {"role": "user", "content": refine_json_prompt}
    ]

    full_response = generate_text(messages)
    
    json_only_prompt = 'Could you respond only the JSON?'
    messages = [
        {"role": "user", "content": refine_json_prompt},
        {"role": "assistant", "content": full_response},
        {"role": "user", "content": json_only_prompt}
    ]

    json_response = generate_text(messages)
    # print(json_response)
    # check if it starts with ```json and ends with ```, remove if so
    if json_response.startswith('```json'):
        json_response = json_response[7:]
    if json_response.endswith('```'):
        json_response = json_response[:-3]
    try:
        refined_json = json.loads(json_response)
    except:
        print("json_response:", json_response)
        raise ValueError("The refined config is not a valid JSON format")

    # check if id is 1, 2, 3, ...
    for i, object in enumerate(refined_json['objects']):
        assert(int(object['id']) == i + 1)
    '''extra_skills = []
    extra_descriptions = []
    extra_categories = []
    for object in refined_json['objects'][num_objects:]:
        extra_skills.append(object['item'])
        extra_descriptions.append(f"the image contain one {object['item']}.")
        extra_categories.append('object')'''
    
    img_info["json_descr"] = refined_json

    # update the description of the relations
    if 'relation' in refined_json:
        for relation in refined_json['relation']:
            objectA = refined_json['objects'][int(relation['ObjectA_id'])-1]['item']
            objectB = refined_json['objects'][int(relation['ObjectB_id'])-1]['item']
            if objectA == objectB:
                objectB = "another " + objectB
            description = relation['description'].format(ObjectA=objectA, ObjectB=objectB)
            index = img_info["skills"].index(relation['name'])
            assert img_info["categories"][index] == 'spatial'
            img_info["descriptions"][index] = description
    
    return img_info

def build_query_for_prompt(img_info):
    query_for_prompt = "Make up a human-annotated description of an image that describe the following properties (meaning you can infer these properties from the description):\n" 
    for description in img_info["descriptions"]:
        query_for_prompt += f"* {description}\n"
    query_for_prompt += "As a reference, I constructed a JSON containing all the information from the properties and some additional information that you should incorperate into your description:\n```json" + json.dumps(img_info["json_descr"]) + "```\n"
    if "features" in img_info:
        query_for_prompt += f"If relevant, you can consider the following properties to enrich the prompt and make it more naturalistic: {", ".join(img_info["features"])}"
    query_for_prompt += "Describe the image in an objective and unbiased way. Keep the description clear and unambiguous, synthesize the objects in a clever and clean way, so people can roughly picture the scene from your description. DO NOT introduce unnecessary objects and unnecessary description of the objects beyond the given properties and JSON. If there is an interaction between two objects, make sure the two objects are distinguishable. Avoid any descriptions involving group of objects, or ambiguous number of objects like \"at least one\", \"one or more\", or \"several\". Do not add subjective judgments about the image, it should be as factual as possible. Do not use fluffy, poetic language, or any words beyond elementary school level. Respond \"WRONG\" and explain if the properties have obvious issues or conflicts, or if it is hard to realize them in an image. Otherwise, respond only with the caption itself. "
    return query_for_prompt

# use LLM to generate a prompt for image generation
def generate_t2i_prompt(img_info):

    query_for_prompt = build_query_for_prompt(img_info)
    #print(query_for_prompt)

    messages = [
        {"role": "user", "content": query_for_prompt}
    ]
    sentence = generate_text(messages)
    if sentence.startswith("WRONG"):
        print(f"Prompt generation returned:\n{sentence}")
        return None
    
    verification = "Could you read your caption again and verify if it makes sense in a very loose sense (e.g., a person cannot be triangle shaped, but a cloud can be square-shaped and a tree can be rectangle-shaped)? If yes, respond with the exact same caption. If not, respond with \"WRONG\" and explain why."
    messages = [
        {"role": "user", "content": query_for_prompt},
        {"role": "assistant", "content": sentence},
        {"role": "user", "content": verification}
    ]
    t2i_prompt = generate_text(messages)

    if t2i_prompt.startswith("WRONG"):
        print(f"Prompt generation returned:\n{t2i_prompt}")
        return None
    
    return t2i_prompt

# prompt for object-object combinations
def ooc_query_for_prompt(img_info):
    query_for_prompt = f'Make up a human-annotated description of an image that shows a single invented object created by combining "{img_info["skills"][0]}" and "{img_info["skills"][1]}". The description must make it possible to identify both original objects from the combined form.\n'
    query_for_prompt += 'Describe the image in an objective and unbiased way. Keep the description clear and unambiguous, and synthesize the object in a clever and clean way, so people can roughly picture the scene from your description. DO NOT introduce unnecessary objects and unnecessary descriptions of the objects beyond the given properties. Avoid any descriptions involving a group of objects, or an ambiguous number of objects like "at least one", "one or more", or "several". Do not add subjective judgments about the image, it should be as factual as possible. Do not use fluffy, poetic language, or any words beyond the elementary school level. Respond only with the caption itself.\n'
    if "features" in img_info:
        query_for_prompt += f"If relevant, you can consider the following properties to enrich the prompt and make it more naturalistic: {", ".join(img_info["features"])}"

    return query_for_prompt

# use LLM to generate a prompt for (object-object combination) image generation
def ooc_t2i_prompt(img_info):

    query_for_prompt = ooc_query_for_prompt(img_info)
    #print(query_for_prompt)

    messages = [
        {"role": "user", "content": query_for_prompt}
    ]
    t2i_prompt = generate_text(messages)

    return t2i_prompt


# read the results of the conceptual combination
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

# check if the call to LLM has already been done and return its result
def read_or_generate(path, call_to_llm, data, save_result):
    # read or generate the output of the llm
    if os.path.exists(path):
        if path.endswith(".jpeg"):
            print(f"Image found at {path}")
            return
        else:
            with open(path, encoding="utf-8") as f:
                return json.loads(f.read()) if path.endswith(".json") else f.read()
    else:
        # call llm to generate the output
        result = call_to_llm(data)
        save_result(result, path)
        return result


def main():
    # load image info
    img_config_info = None
    with open(cfg.IMG_CONFIG_INFO, encoding="utf-8") as configfile:
        img_config_info = json.loads(configfile.read())

    os.makedirs(cfg.REF_CONFIG_DIR, exist_ok=True)
    os.makedirs(cfg.PROMPT_DIR, exist_ok=True)
    os.makedirs(cfg.IMAGE_DIR, exist_ok=True)

    for img in img_config_info:
        head = img["skills"][0]
        modifier = img["skills"][1]

        # define image name
        image_name = f"_{'ooc_' if cfg.IS_COMBINATION else ''}{head.replace(" ", "-")}_{modifier.replace(" ", "-")}"
        
        ref_config_path = f"{cfg.REF_CONFIG_DIR}/{image_name}.json"
        prompt_path = f"{cfg.PROMPT_DIR}/{image_name}.txt"
        image_path = f"{cfg.IMAGE_DIR}/{image_name}.jpeg"
        print(f'\nWorking on image {image_name}.')

        cocos_features = read_cocos_output(f'{cfg.COCOS_DIR}/{head}_{modifier}.txt')
        if cfg.USE_COCOS and cocos_features is None:
            print(f"skipping {image_name}: no Conceptal Combination results")

        else:
            # refine the json description (or keep the original for object-object combinations)
            refined_info = None
            if cfg.IS_COMBINATION:
                refined_info = read_or_generate(ref_config_path, lambda x : x, img, save_textual_data)
            else:
                refined_info = read_or_generate(ref_config_path, refine_info, img, save_textual_data)
            print(f'Refined json info saved in {ref_config_path}.')
            
            if cfg.USE_COCOS:
                refined_info["features"] = cocos_features

            # read or generate the prompt
            prompt = None
            if cfg.IS_COMBINATION:
                prompt = read_or_generate(prompt_path, ooc_t2i_prompt, refined_info, save_textual_data)
            else:
                prompt = read_or_generate(prompt_path, generate_t2i_prompt, refined_info, save_textual_data)

            if prompt is None:
                print("Skipping image generation.")
            else:
                print(f'T2I prompt saved to {prompt_path}.')

                # read or generate the image
                read_or_generate(image_path, generate_image, prompt, save_image)



if __name__ == "__main__": main()