import requests
import generation_config as cfg
import os
import json
import time

def save_image(response, image_path):
    # Writing the content to a new file
    with open(image_path, 'xb') as file:
        file.write(response.content)
        # Logging completion message
        print(f'Download of {image_path} Completed')


def generate_image(prompt):

    width = cfg.WIDTH
    height = cfg.HEIGHT
    seed = cfg.SEED
    model = cfg.MODEL

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
            return response
        else:
            retried += 1
            print(f'>>>> Warning - error in image generation: {response.status_code} {response.reason} - failed attempt {retried}/{limit}')
    
    raise Exception("Unable to get a generated image")
    

# use LLM to generate a prompt for image generation
def llm_prompt(head, modifier, features):
    
    features.remove('@scenario_probability')
    features = [f.replace("-", "not ", 1) if f[0] == "-" else f for f in features]
    features = ", ".join(features)
    features = features.replace("-", " ").replace("_", " ")

    instructions = None
    if cfg.USE_COCOS:
        instructions = f'''Make up a human-annotated description of an image that describe the following properties (meaning you can infer these properties from the description):
The image contains an invented object, that is obtained by the combination of "{head}" and "{modifier}".
As a reference, I constructed a list containing some relevant properties and some additional information that you should incorporate into your description: {features}.
Describe the image in an objective and unbiased way. Keep the description clear and unambiguous, and synthesize the objects in a clever and clean way, so people can roughly picture the scene from your description.
DO NOT introduce unnecessary objects and unnecessary descriptions of the objects beyond the given properties. Avoid any descriptions involving a group of objects, or an ambiguous number of objects like “at least one”, “one or more”, or “several”. Do not add subjective judgments about the image, it should be as factual as possible. Do not use fluffy, poetic language, or any words beyond the elementary school level.
Respond only with the caption itself.'''
    #Respond “WRONG” and explain if the properties have obvious issues or conflicts, or if it is hard to realize them in an image. Otherwise, respond only with the caption itself.
    else:
        instructions = f'''Make up a human-annotated description of an image that describe the following properties (meaning you can infer these properties from the description):
The image contains an invented object, that is obtained by the combination of "{head}" and "{modifier}".
Describe the image in an objective and unbiased way. Keep the description clear and unambiguous, and synthesize the objects in a clever and clean way, so people can roughly picture the scene from your description.
DO NOT introduce unnecessary objects and unnecessary descriptions of the objects beyond the given properties. Avoid any descriptions involving a group of objects, or an ambiguous number of objects like “at least one”, “one or more”, or “several”. Do not add subjective judgments about the image, it should be as factual as possible. Do not use fluffy, poetic language, or any words beyond the elementary school level.
Respond only with the caption itself.'''

    url = "https://apifreellm.com/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "message": instructions
    }

    limit = 4  # max n of retries
    delay = 5   # n of seconds to wait between retries
    retried = 0
    while retried < limit:
        if retried > 0:
            time.sleep(delay)

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("status") == "success":
            return result["response"]
        else:
            retried += 1
            print(f'>>>> Warning - error in prompt generation: {response.status_code} {result["error"]} - failed attempt {retried}/{limit}')

    raise Exception("Unable to get a prompt from LLM")

# generate a prompt for image generation using a fixed template
def template_prompt(head, modifier, features):
    features.remove('@scenario_probability')
    features = [f.replace("-", "not ", 1) if f[0] == "-" else f for f in features]
    features = ", ".join(features)
    features = features.replace("-", " ").replace("_", " ")
    prompt = cfg.PROMPT_TEMPLATE.format(head=head, modifier=modifier, features=features)
    return prompt

# wrapper for prompt generation
def generate_prompt(head, modifier, features, output_path):
    prompt = None
    if cfg.PROMPT_ORIGIN == 'llm':
        prompt = llm_prompt(head, modifier, features)
    elif cfg.PROMPT_ORIGIN == 'template':
        prompt = template_prompt(head, modifier, features)
    else:
        raise Exception(f"Wrong cofiguration of PROMPT_ORIGIN: {cfg.PROMPT_ORIGIN}")
    
    with open(output_path, "x", encoding="utf-8") as output_file:
        output_file.write(prompt)

    return prompt

def main():
    # for each combination file
    for filename in os.listdir(cfg.COCOS_DIR):
        file_path = os.path.join(cfg.COCOS_DIR, filename)

        head = None
        modifier = None
        combination_result = None
        
        with open(file_path) as f:
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
            
        features = list(combination_result.keys())

        # define image name
        image_name = f"{head}_{modifier}{"_cocos" if cfg.USE_COCOS else ""}_{cfg.PROMPT_ORIGIN}"
        image_path = os.path.join(cfg.OUTPUT_DIR, image_name+".jpeg")
        prompt_path = os.path.join(cfg.PROMPT_DIR, image_name+".txt")
        if os.path.exists(image_path):
            print(f"File exists: {image_path} - skipping generation")
        else:
            prompt = None
            if os.path.exists(prompt_path):
                with open(prompt_path, encoding="utf-8") as f:
                    prompt = f.read()
            else:
                # generate prompt for T2I
                prompt = generate_prompt(head, modifier, features, prompt_path)
            print(prompt)
            # generate image
            response = generate_image(prompt)
            save_image(response, image_path)


if __name__ == "__main__": main()