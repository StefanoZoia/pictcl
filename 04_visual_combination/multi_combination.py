import requests
import generation_config as cfg
import os
import json
import time
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# functions for text-to-image generation

def save_image(binary_img, image_path):
    # Writing the content to a new file
    with open(image_path, 'xb') as file:
        file.write(binary_img)
        # Logging completion message
        print(f'Generated image saved to {image_path}.')

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
    else:
        raise NotImplementedError(f"Invalid API specified: {cfg.TEXT_API}")
    


# prompt for multiple objects combination
def multi_query_for_prompt(img_info):
    query_for_prompt = f'Make up a human-annotated description of an image that shows a single invented object created by combining {img_info["starting_concepts"]}. The description must make it possible to identify the original objects from the combined form.\n'
    query_for_prompt += 'Describe the image in an objective and unbiased way. Keep the description clear and unambiguous, and synthesize the object in a clever and clean way, so people can roughly picture the scene from your description. DO NOT introduce unnecessary objects and unnecessary descriptions of the objects beyond the given properties. Avoid any descriptions involving a group of objects, or an ambiguous number of objects like "at least one", "one or more", or "several". Do not add subjective judgments about the image, it should be as factual as possible. Do not use fluffy, poetic language, or any words beyond the elementary school level. Respond only with the caption itself.\n'
    if "features" in img_info:
        query_for_prompt += f"If relevant, you can consider the following properties to enrich the prompt and make it more naturalistic: {", ".join(img_info["features"])}"

    return query_for_prompt

# use LLM to generate a prompt for (multiple objects combination) image generation
def multi_t2i_prompt(img_info):

    query_for_prompt = multi_query_for_prompt(img_info)
    #print(query_for_prompt)

    messages = [
        {"role": "user", "content": query_for_prompt}
    ]
    t2i_prompt = generate_text(messages)

    return t2i_prompt



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

    os.makedirs(cfg.PROMPT_DIR, exist_ok=True)
    os.makedirs(cfg.IMAGE_DIR, exist_ok=True)

    # chimera

    # define image name
    image_name = "chimera_base"
    
    prompt_path = f"{cfg.PROMPT_DIR}/{image_name}.txt"
    image_path = f"{cfg.IMAGE_DIR}/{image_name}.jpeg"
    print(f'\nWorking on image {image_name}.')

    info = {}

    info["starting_concepts"] = "a lion, a goat and a dragon"
    info["features"] = ["has tail", "has mane", "has horns", "has beards", "fire breathing", "fly", "aggressive"]

    # read or generate the prompt
    prompt = read_or_generate(prompt_path, multi_t2i_prompt, info, save_textual_data)

    if prompt is None:
        print("Skipping image generation.")
    else:
        print(f'T2I prompt saved to {prompt_path}.')

        # read or generate the image
        read_or_generate(image_path, generate_image, prompt, save_image)



if __name__ == "__main__": main()