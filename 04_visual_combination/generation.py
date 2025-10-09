import requests
import generation_config as cfg
import os
import json
import time

def download_image(prompt, image_name):

    width = cfg.WIDTH
    height = cfg.HEIGHT
    seed = cfg.SEED
    model = cfg.MODEL

    image_url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&seed={seed}&model={model}"

    # Writing the content to a new file
    image_path = os.path.join(cfg.OUTPUT_DIR, image_name)
    with open(image_path, 'xb') as file:
        # Fetching the image from the URL
        response = requests.get(image_url)
        file.write(response.content)
    # Logging completion message
    print(f'Download of {image_path} Completed')
    

# use LLM to generate a prompt for image generation
def llm_prompt(head, modifier, features):
    
    features.remove('@scenario_probability')
    features = ", ".join(features)
    features = features.replace("-", " ").replace("_", " ")

    instructions = f'''Make up a human-annotated description of an image that describe the following properties (meaning you can infer these properties from the description):
The image contains an invented object, that is obtained by the combination of "{head}" and "{modifier}".
As a reference, I constructed a list containing some relevant properties and some additional information that you should incorporate into your description: {features}.
Describe the image in an objective and unbiased way. Keep the description clear and unambiguous, and synthesize the objects in a clever and clean way, so people can roughly picture the scene from your description.
DO NOT introduce unnecessary objects and unnecessary descriptions of the objects beyond the given properties. Avoid any descriptions involving a group of objects, or an ambiguous number of objects like “at least one”, “one or more”, or “several”. Do not add subjective judgments about the image, it should be as factual as possible. Do not use fluffy, poetic language, or any words beyond the elementary school level.
Respond only with the caption itself.'''
    '''
Respond “WRONG” and explain if the properties have obvious issues or conflicts, or if it is hard to realize them in an image. Otherwise, respond only with the caption itself.
'''
    url = "https://apifreellm.com/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "message": instructions
    }

    limit = 4  #max n of retries
    delay = 5   #n of seconds to wait between retries
    retried = 0
    while retried < limit:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("status") == "success":
            return result["response"]
        else:
            retried += 1
            print(f'>>>>WARNING: {result["error"]} - failed attempt {retried}/{limit}')
            time.sleep(delay)

    raise Exception("Unable to get a prompt from LLM")

# generate a prompt for image generation using a fixed template
def template_prompt(head, modifier, features):
    features.remove('@scenario_probability')
    features = ", ".join(features)
    features = features.replace("-", " ").replace("_", " ")
    prompt = cfg.PROMPT_TEMPLATE.format(head=head, modifier=modifier, features=features)
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

        # generate image
        prompt = llm_prompt(head, modifier, features)
        print(prompt)
        image_name = f"{head}_{modifier}_llm_cocos.jpeg"
        download_image(prompt, image_name)


if __name__ == "__main__": main()