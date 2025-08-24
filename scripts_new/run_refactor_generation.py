import json

import os
import random
import base64
import requests
from argparse import ArgumentParser
from tqdm import tqdm

random.seed(42)

# OpenAI API Key
api_key = os.environ.get("OPENAI_API_CADA41")

headers = {
    "Authorization": f"Bearer {api_key}"
}

SYSTEM_PROMPT_REFACTOR = ("You are a software engineering expert specializing in Python. "
                          "Your company assigns you the task of refactoring a set of Python scripts. "
                          "Each script is a runnable text game about some daily/scientific scenarios where humans take "
                          "action by iteratively inputting actions from the command line, observing output text concerning "
                          "the change of the game state, and continuing until the given task is completed. "
                          "To refactor each script, you are provided with template scripts named <GameBasic.py> "
                          "that implement abstract classes & functions for objects, the game world, actions, score calculations, etc. "
                          "The target script to be refactored contains an exact implementation of a specific game. "
                          "You need first to <from GameBasic import *>, and rewrite all classes/functions by using & overriding "
                          "all templates imported from <GameBasic>. "
                          "Ensure that the refactored script retains exactly the same functionality as the original input script. "
                          "This involves reusing member functions from superclasses whenever possible, "
                          "overriding when extra functionalities need to be incorporated, "
                          "implementing all abstract functions, etc. "
                          "Also, try to keep all the comments with adjustments to the refactor to improve readability.  "
                          "You will have one example demonstrating how to write the refactored code and implement the target one following it.")

def prepare_demo_input(args, script_name):
    script_path = os.path.join(args.script_dir, script_name)
    with open(script_path, "r") as f:
        script_content = f.read()

    return f"Script to be refactored: <{script_name}>\n ```Python\n{script_content}\n```"


def prepare_demo_output(args, script_name):
    script_path = os.path.join(args.refactored_script_dir, script_name)
    with open(script_path, "r") as f:
        script_content = f.read()

    return f"Refactored script: <{script_name}>\n ```Python\n{script_content}\n```"


def prepare_template(args):
    template_path = os.path.join(args.refactored_script_dir, "GameBasic.py")
    with open(template_path, "r") as f:
        template_content = f.read()

    return f"Template script: <GameBasic.py>\n ```Python\n{template_content}\n```"

def prepare_target_input(args):
    script_path = os.path.join(args.script_dir, args.target_script_name)
    with open(script_path, "r") as f:
        script_content = f.read()

    return f"Script to be refactored: <{args.target_script_name}>\n ```Python\n{script_content}\n```"


def refactor(args):
    input_prompt = {
        "model": args.model_id,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_REFACTOR
            },
            {
                "role": "user",
                "content": []
            }
        ],
        "max_tokens": 4096
    }

    input_prompt['messages'][1]['content'].append({
        "type": "text",
        "text": prepare_template(args)
    })

    for script_name in args.demo_script_names:
        input_prompt['messages'][1]['content'].append({
            "type": "text",
            "text": prepare_demo_input(args, script_name)
        })
        input_prompt['messages'][1]['content'].append({
            "type": "text",
            "text": prepare_demo_output(args, script_name)
        })

    input_prompt['messages'][1]['content'].append({
        "type": "text",
        "text": prepare_target_input(args)
    })

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=input_prompt)
    print('response: ', response.json())  # ['choices'][0]['message']['content']
    response_text = response.json()['choices'][0]['message']['content'].strip("```").split("```Python")[1].strip("\n")
    with open(os.path.join(args.refactored_script_dir, args.target_script_name), 'w') as f:
        f.write(response_text)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--model_id", type=str, help="Model ID to use for generation")
    parser.add_argument("--script_dir", type=str, help="Path to the directory containing the scripts to be refactored")
    parser.add_argument("--refactored_script_dir", type=str, help="Path to the directory to save the refactored scripts")
    parser.add_argument("--demo_script_names", nargs='+', type=str, help="Names of the demo script to be refactored")
    parser.add_argument("--target_script_name", type=str, help="Name of the target script to be refactored")
    args = parser.parse_args()

    refactor(args)