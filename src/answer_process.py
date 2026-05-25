import re

class AnswerProcessor:

    def extract_answer(self, answer: str, task: str = "CheckmateInOne") -> str:
        """
        Extracts the final answer from a string.
        - If <Answer>...</Answer> is present, extract its content.
        - Otherwise, look for \boxed{...} and extract that.
        """
        # Case 1: XML-style <Answer>...</Answer>
        if '<Answer>' in answer and '</Answer>' in answer:
            start = answer.find('<Answer>') + len('<Answer>')
            end = answer.find('</Answer>', start)
            return answer[start:end].strip()

        # Case 2: Try to extract from \boxed{...}
        boxed_match = re.search(r'\\boxed\{([^}]*)\}', answer)
        if boxed_match:
            return boxed_match.group(1).strip()
        
        if task == "CheckmateInOne" or task == "WordSorting":
            return answer.strip()

        # Case 3: No recognizable answer format
        return None

    def extract_move(self, text: str) -> str:
        """ This method is defined for CheckmateInOne task. 
        Extracts a chess move from the given text.
        The move is expected to be in the format of a standard chess notation,
        such as 'e4', 'Nf3', 'Bb5', etc.
        Args:
            text (str): The input text containing the chess move.
        Returns:
            str: The extracted chess move if found, otherwise the original text.
        """
        match = re.search(r'[A-Z][a-zA-Z0-9+#=]*$', text)
        return match.group(0) if match else text
    
    def extract_number(self, text: str) -> str:
        """ This method is defined for AIME2025 and AIME 2024 task."""
        match = re.search(r'\d+', text)
        if match:
            number = match.group()
            return number
        else:
            print(text)
            print("No number found.")
            return text
        
    def get_final_answer(self, result: str, task: str) -> str:
        """
        This method returns the final answer that will be stored in the process folder.
        First check if the result is null or not, if not, the method process it based on the task
        and return the final answer. If the result is null, it returns None as str.
        """
        if result is None:
            final_answer = "None"
        else:
            final_answer = self.extract_answer(result, task=task)
            if final_answer is None:
                print("No recognizable answer format")
            else:
                if task in ["AIME2024", "AIME2025"]:
                    final_answer = self.extract_number(final_answer)
                elif task == "CheckmateInOne":
                    final_answer = self.extract_move(final_answer)
        return final_answer
    
