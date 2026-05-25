import json
from tqdm import tqdm
from prompts.distil_prompt import meta_distiller_prompt
from prompts.task_generation import generation, iterate_generation
from src.llm_client import LLMClient
from src.util import update_api_key, Utils
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--task_name', type=str, default='gameof24')
parser.add_argument('--model_name', type=str, default='gpt-4o-mini')

args = parser.parse_args()

def load_jsonl_to_dict(filepath):
    result = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_dict = json.loads(line)
            result.update(line_dict)  # merge top-level keys into one dict
    return result

models = load_jsonl_to_dict("models/models.jsonl")

def get_openai_client(model_name: str = "gpt-4o-mini", temperature: float = 0.7) -> LLMClient:
    """
    Initialize and return an OpenAI client.
    """
    model = models.get(model_name)
    update_api_key(model)

    client = LLMClient(
        is_azure=model['is_azure'],
        api_key=model['api_key'],
        api_version= model['api_version'],
        endpoint=model['endpoint'],
        model_name=model['model_id'],
        temperature=temperature,
    )
    print("INFO:: OpenAI client initialized.")
    return client

MODEL = args.model_name
openai_client = get_openai_client(MODEL)

# Load JSONL data from the benchmarks folder
DATASET = args.task_name
data = []
with open(f'benchmarks/{DATASET}.jsonl', 'r') as f:
    for line in f:
        data.append(json.loads(line))

def problem_distillation(user_input: str):
        messages=[
                {"role": "system", "content": meta_distiller_prompt},
                {"role": "user", "content": user_input}
        ]
        try:
            distilled_information = openai_client(messages)
        except Exception as e:
            distilled_information = "Error processing distilled_information"
        return distilled_information

def buffer_retrieve(distilled_information, user_input):
    instantiation_instruct = """You are an expert in problem analysis and can apply previous problem-solving approaches to new issues. The user will provide a specific task description and a thought template. Your goal is to analyze the user's task and generate a specific solution based on the thought template. If the solution does not involve code, provide a final answer that is easy to extract from the text. 
It should be noted that all the python code should be within one code block, the answer should not include more than one code block! And strictly follow the thought-template to instantiate the python code but you should also adjust the input parameter according to the user input!
    """
    formated_input = f"""
Distilled information:
{distilled_information}
User Input:
{user_input}

Instantiated Solution:
Please analyze the above user task description and thought template, and generate a specific, detailed solution. Please provide a clear and extractable final answer within <Answer> Your Final Answer </Answer>.
        """
    messages=[
        {"role": "system", "content": instantiation_instruct},
        {"role": "user", "content": formated_input}
    ]
    try:
        result = openai_client(messages)
    except Exception as e:
        result = "Error processing buffer_retrieve"
    return result

utils = Utils()
    
with open(f"results/output/{MODEL}/{MODEL}_{DATASET}_distil.jsonl", "w") as result_file:
    for sample_id, sample in enumerate(tqdm(data)):
        responses, results, codes_str = dict(), dict(), dict()
        question = sample['input']
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": generation[DATASET].format(question=question)}
        ]
        try:
            response = openai_client(messages)
        except Exception as e:
            response = f"Error processing sample {sample_id}: {e}"
        responses['0'] = response
        results['0'] = ""
        codes_str['0'] = ""
        for i in range(5):
            user_input = iterate_generation[DATASET].format(question=question) + f" <Answer> {response} </Answer>. Review your previous answer and find problems with your answer. Based on the problems you found, improve your answer. If you think your answer is correct, you can just return the answer without any modification. Please provide your answer within <Answer> Your Final Answer Here </Answer>."
            distilled_information = problem_distillation(user_input=user_input)
            response = buffer_retrieve(distilled_information, user_input)
            result, code_str = utils.extract_and_execute_code(response)
            responses[str(i + 1)] = response
            results[str(i + 1)] = str(result)
            codes_str[str(i + 1)] = code_str
        output = {"input": question, "response": responses, "result": results, "code_str": codes_str}
        result_file.write(json.dumps(output) + "\n")
        result_file.flush()