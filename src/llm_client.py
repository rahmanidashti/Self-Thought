from openai import OpenAI, AzureOpenAI
from retry import retry
from transformers import pipeline, AutoTokenizer
from azure.identity import ChainedTokenCredential, AzureCliCredential, ManagedIdentityCredential, get_bearer_token_provider
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

class LLMClient:

    def __init__(self, is_azure, api_key, api_version, endpoint, model_name, temperature):
        print(f"Initializing LLMClient with model: {model_name}, is_azure: {is_azure}, endpoint: {endpoint}")
        self.model_name = model_name
        self.temperature = temperature
        self.is_azure = is_azure

        if is_azure is True:
            if "trapi.research.microsoft.com" in endpoint:
                if get_bearer_token_provider is None:
                    raise ImportError(
                        "azure-identity is required for TRAPI AAD auth. Install with: pip install azure-identity"
                    )
                print("Detected TRAPI endpoint without api_key -> using AAD bearer token authentication.")
                scope = "api://trapi/.default"
                chained = ChainedTokenCredential(
                    AzureCliCredential(),
                    ManagedIdentityCredential(),
                )
                token_provider = get_bearer_token_provider(chained, scope)
                self.client = AzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=token_provider, api_version=api_version)
            elif "DeepSeek-R1" in endpoint:
                print(f"Using Deepseek endpoint with api_key")
                self.client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key), api_version=api_version)
            else:
                print(f"Using Azure OpenAI API key auth (api_version={api_version}).")
                self.client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)

        elif is_azure is False:
            print(f"Using OpenAI API with endpoint: {endpoint}")
            self.client = OpenAI(api_key=api_key, base_url=endpoint)
        elif is_azure is None:
            print(f"Using Hugging Face {model_name} for model inference.")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id 
            self.client = pipeline("text-generation", model=model_name, device_map="auto", pad_token_id=self.tokenizer.pad_token_id)
        else:
            raise ValueError("Invalid value for is_azure. It should be True, False, or None.")

    @retry(exceptions=(Exception,), tries=6, delay=1, backoff=2)
    def __call__(self, instruction):
        try:
            if self.is_azure is None:
                if self.model_name in ["SmolLM2-1.7B"]:
                    input_text=self.tokenizer.apply_chat_template(instruction, tokenize=False)
                    instruction = self.tokenizer.encode(input_text, return_tensors="pt").to("cuda")
                response = self.client(instruction, temperature=self.temperature, max_new_tokens=1024, return_full_text=False)
                return response[0]['generated_text']
            elif self.is_azure is True or self.is_azure is False:
                if self.model_name == "o3-mini":
                    response = self.client.chat.completions.create(
                        messages=instruction,
                        model=self.model_name
                    )
                elif "DeepSeek-R1" in self.model_name:
                    response = self.client.complete(
                        messages=instruction,
                        model=self.model_name
                    )
                else:
                    response = self.client.chat.completions.create(
                        messages=instruction,
                        model=self.model_name,
                        temperature=self.temperature,
                    )
                return response.choices[0].message.content
        except Exception as e:
            raise # Re-raise for retry