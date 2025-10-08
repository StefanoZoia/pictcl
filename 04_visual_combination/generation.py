import requests
import generation_config as cfg
import os
import json

def download_image(head, modifier, features):
    prompt = cfg.PROMPT_TEMPLATE.format(head=head, modifier=modifier, features=features)
    #print(prompt)

    width = cfg.WIDTH
    height = cfg.HEIGHT
    seed = cfg.SEED
    model = cfg.MODEL

    image_url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&seed={seed}&model={model}"

    image_name = f"{head}_{modifier}_cocos.jpeg"
    image_path = os.path.join(cfg.OUTPUT_DIR, image_name)

    # Writing the content to a new file
    with open(image_path, 'xb') as file:
        # Fetching the image from the URL
        response = requests.get(image_url)
        file.write(response.content)
    # Logging completion message
    print(f'Download of {image_path} Completed')


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
            
        # build string of features
        features = list(combination_result.keys())
        features.remove('@scenario_probability')
        features = ", ".join(features)
        features = features.replace("-", " ").replace("_", " ")

        # generate image
        download_image(head, modifier, features)


if __name__ == "__main__": main()