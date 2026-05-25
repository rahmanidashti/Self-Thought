import json
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('--task', type=str, default='gameof24')
parser.add_argument('--model', type=str, default="o3-mini")
parser.add_argument('--method', type=str, default="baseline")

# load test data for the iteration
def get_iter_data(iteration_id):
    values = []
    for line in (open(test_path)):
        responses = json.loads(line)
        try:
            response = responses.get("result", {})
            value = response.get(iteration_id, None)
            values.append(value)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON on line {e}")
            values.append(None)
    print(f"INFO:: Test data for iter {iteration_id} loaded ...")
    return values

def has_four_numbers(equation):
    """
    Checks if the given equation contains exactly four numbers.

    Args:
        equation (str): A math equation as a string.

    Returns:
        bool: True if the equation has exactly four numbers, False otherwise.
    """
    numbers = re.findall(r'\d+(?:\.\d+)?', equation)
    return len(numbers) == 4

if __name__ == "__main__":
    args = parser.parse_args()

    benchmark_path_dict = {
        'gameof24':'benchmarks/gameof24.jsonl',
        'CheckmateInOne':'benchmarks/CheckmateInOne.jsonl',
        'WordSorting':'benchmarks/WordSorting.jsonl',
        'AIME2025':'benchmarks/AIME2025.jsonl',
        'AIME2024':'benchmarks/AIME2024.jsonl',
    }

    benchmark_path = benchmark_path_dict[args.task]
    correct = 0

    # load ground truth data
    truth = []
    for line in (open(benchmark_path)):
        answer = json.loads(line)['target']
        truth.append(answer)
    if args.model in ['qwen-7b', 'llama-70b'] and args.method in ['baseline', 'distil', 'thought']:
        save_file_path = f"results/eval/thought/{args.model}/{args.model}_{args.task}_{args.method}.jsonl"
        test_path = f"results/process/thought/{args.model}/{args.model}_{args.task}_{args.method}.jsonl"
    else:
        save_file_path = f"results/eval/{args.method}/{args.model}/{args.model}_{args.task}_{args.method}.jsonl"
        test_path = f"results/process/{args.method}/{args.model}/{args.model}_{args.task}_{args.method}.jsonl"

    with open(save_file_path, 'w') as fout:
        # load test result data

        previous_correct_ids = None
        previous_incorrect_ids = None

        for iter_id in range(6):
            correct = 0
            correct_ids = list()
            incorrect_ids = list()
            test = get_iter_data(iteration_id=str(iter_id))
            total = len(test)   
            for index, result in enumerate(test):
                if args.task == 'gameof24':
                    try:
                        result = result.split('=')[0]
                    except:
                        print(f"Error processing result: {result}")
                        incorrect_ids.append(index)
                        continue
                    result = result.strip()
                    try:
                        if has_four_numbers(equation=result):
                            if eval(result) == 24:
                                correct += 1
                                correct_ids.append(index)
                            else:
                                incorrect_ids.append(index)
                        else:
                            incorrect_ids.append(index)
                    except:
                        incorrect_ids.append(index)
                        continue
                else:
                    if truth[index] == result:
                        correct += 1
                        correct_ids.append(index)
                    else:
                        incorrect_ids.append(index)

            print(f'Iter: {iter_id}, Total number: {len(test)}, Correct number: {correct}, Accuracy: {correct/len(test):.2%}')
            accuracy = correct / total

            # ---- compute deltas if not the first iteration ----
            delta = None
            delta_i2c = None
            delta_c2i = None
            if previous_correct_ids is not None:
                prev_correct = set(previous_correct_ids)
                prev_incorrect = set(previous_incorrect_ids)
                curr_correct = set(correct_ids)
                curr_incorrect = set(incorrect_ids)

                delta = accuracy - (len(prev_correct) / total)
                delta_i2c = len(prev_incorrect & curr_correct) / total
                delta_c2i = len(prev_correct & curr_incorrect) / total
            
            # ---- prepare record ----
            acc = {"iter": iter_id, 
                   "total": len(test), 
                   "correct": correct, 
                   "accuracy": round(correct/len(test), 4),
                   "correct_ids": correct_ids,
                   "incorrect_ids": incorrect_ids,
                   "delta": None if delta is None else round(delta, 4),
                   "delta_i2c": None if delta_i2c is None else round(delta_i2c, 4),
                   "delta_c2i": None if delta_c2i is None else round(delta_c2i, 4)
            }
            fout.write(json.dumps(acc) + "\n")
            fout.flush()

            # ---- update previous iteration ----
            previous_correct_ids = correct_ids
            previous_incorrect_ids = incorrect_ids

    print(f"INFO:: Evaluation results saved ... \n")