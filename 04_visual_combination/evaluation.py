import requests
import generation_config as cfg
import os
import json
import time
from generation import generate_text, read_or_generate, save_textual_data, build_query_for_prompt
import base64
from openai import OpenAI

def pollinations_analyze_image(prompt, base64_image, max_tokens):
    payload = {
        "model": cfg.TEXT_MODEL,
        "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    "max_tokens": max_tokens
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

def openai_analyze_image(prompt, base64_image, max_tokens):
    client = OpenAI()

    limit = 10  # max n of retries
    delay = 1   # n of seconds to wait between retries
    retried = 0
    while retried < limit:
        if retried > 0:
            time.sleep(delay)
        try:
            print(prompt)
            response = client.responses.create(
                model=cfg.TEXT_MODEL,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                #max_output_tokens = max_tokens
            )
            print(response.output_text)
            return response.output_text
        except Exception as e:
            retried += 1
            print(f'>>>> Warning - error in text generation: {e} - failed attempt {retried}/{limit}')
    
    raise Exception("Unable to get a response from LLM")

def analyze_image(prompt, base64_image, max_tokens):
    if cfg.TEXT_API == "OpenAI":
        return openai_analyze_image(prompt, base64_image, max_tokens)
    elif cfg.TEXT_API == "Pollinations":
        return pollinations_analyze_image(prompt, base64_image, max_tokens)
    else:
        raise NotImplementedError(f"Invalid API specified: {cfg.TEXT_API}")
    


# generate questions to evaluate an image
def generate_questions(img_info):
    n = len(img_info["skills"])

    query_for_prompt = build_query_for_prompt(img_info)

    if "json_descr" in img_info:
        question_generation = f"A student just draw a picture based on your description. Can you help me verify whether the student did a good job? Specifically, I want to know if the image follows your description and also follows the properties I mentioned earlier. You should ask me one yes or no question for each property, and I will tell you if they are satisfied. For example, for properties like \"the image contains one or more {img_info["skills"][0]}\", the corresponding question should be \"Does the image contain {img_info["skills"][0]}?\". Respond only the {n} questions, one for each property, in the same order of the properties, and each on a new line."
    else:
        question_generation = f"A student just draw a picture based on your description. Can you help me verify whether the student did a good job? Specifically, I want to know if the image follows your description and also follows the propertied I mentioned earlier. You should ask me one yes or no question for each property, and I will tell you if they are satisfied. Because the wording of your desciption might be slightly different different from the properties, please stick to the wording of your desciption when you ask the questions. For example, you should avoid using the word \"object\", and the first question should be \"Does the image contain {img_info["skills"][0]}?\". Note the properties do not have information duplication, please make sure the questions do not have information duplication as well. Respond only the {n} questions, one for each property, in the same order of the properties, and each on a new line."
    messages = [
        {"role": "user", "content": query_for_prompt},
        {"role": "assistant", "content": img_info["t2i_prompt"]},
        {"role": "user", "content": question_generation}
    ]
    questions = generate_text(messages)
    print("=====")
    print("questions: \n" + questions)
    print("=====")
    
    return questions.split('\n')

# encode image to be evaluated
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
# evaluate an image against a single question
def check_in_image(img_path, question):
    base64_image = encode_image(image_path=img_path)
    prompt = f"{question} Respond \"Yes\" or \"No\"."
    answer = analyze_image(prompt, base64_image, max_tokens=16)
    if "Yes" in answer:
        return 1
    else:
        return 0

# evaluate an image acoording to all its questions
def evaluate_image(img_info):
    scores = list()

    for question in img_info['questions']:
        print("Q:", question)
        score = check_in_image(img_info['image_path'], question)
        print("A:", score)
        scores.append(score)

    assert(len(scores) == len(img_info['questions']))
    img_info['scores'] = scores

    return img_info


def main():
    os.makedirs(cfg.QUESTIONS_DIR, exist_ok=True)
    os.makedirs(cfg.SCORE_DIR, exist_ok=True)

    count_images = 0
    count_all_correct = 0
    count_questions = 0
    total_score = 0

    # for each generated image
    for filename in os.listdir(cfg.IMAGE_DIR):

        image_name = filename.split(".")[0]
        print(f'Working on image {image_name}.')

        ref_config_path = f"{cfg.REF_CONFIG_DIR}/{image_name}.json"
        prompt_path = f"{cfg.PROMPT_DIR}/{image_name}.txt"

        # load image configuration data
        img_info = None
        with open(ref_config_path, encoding="utf-8") as f:
            img_info = json.loads(f.read())
        # load T2I prompt used for image generation
        with open(prompt_path, encoding="utf-8") as f:
            img_info["t2i_prompt"] = f.read()

        questions_path = f"{f"{cfg.QUESTIONS_DIR}/{image_name}.json"}"

        # read or generate the questions
        questions = read_or_generate(questions_path, generate_questions, img_info, save_textual_data)
        questions = [q for q in questions if q.strip()]
        img_info["questions"] = questions
        img_info["image_path"] = f"{cfg.IMAGE_DIR}/{filename}"
        print(f"Questions saved in {questions_path}.")

        score_path = f"{cfg.SCORE_DIR}/{image_name}.json"

        img_info = read_or_generate(score_path, evaluate_image, img_info, save_textual_data)
        print(f"Final img info with scores saved in {score_path}.")

        count_images += 1
        count_questions += len(questions)

        # compute image score from individual question scores
        image_score = sum(img_info["scores"])
        total_score += image_score
        if image_score == len(questions):
            count_all_correct += 1
        
    # compute overall score of the generated images 
    proportion_all_correct = count_all_correct / count_images
    average_score_per_image = total_score / count_questions
    print(f"Evaluated images: {count_images}")
    print(f"Proportion of perfect-scoring images: {proportion_all_correct:.2%}")
    print(f"Average score per image: {average_score_per_image:.2%}")





if __name__ == "__main__": main()