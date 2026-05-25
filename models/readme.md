# Models
In this folder, we have a JSONL file that includes all the models.

In the `models.json` file, each entry shows a model that can be AzureOpenAI, open-source models API, and HuggingFace models, where they are indicated by different values for `is_azure` value:

- `is_azure: true`: Azure OpenAI API
- `is_azure: false`: Open-source API model
- `is_azure: null`: HuggingFace model

## Example Entry
Here are some examples:

### Azure OpenAI:
```
{"o3-mini": {"is_azure": true, "api_key": "#", "api_version": "2025-01-01-preview", "endpoint": "#", "model_id": "o3-mini"}}
```

For AzureOpenAI, we need to have `"is_azure": true`, `"api_key"`, `"api_version"`, `"endpoint"`, and `"model_id"`.

### Open-Source Model API:
```
{"llama-3-8b": {"is_azure": false, "api_key": "#", "api_version": "None", "endpoint": "#", "model_id": "region-llama31-8b"}}
```

For AzureOpenAI, we need to have `"is_azure": false`, `"api_key"`, `"endpoint"`, and `"model_id"`.