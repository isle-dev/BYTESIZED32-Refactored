from functools import lru_cache
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, ChainedTokenCredential, AzureCliCredential, ManagedIdentityCredential, get_bearer_token_provider
import re


@lru_cache(maxsize=None)
def get_llm_client(model_name=None):
    # Default to gpt-4o if no model is specified
    ep = model_name or "gpt-4o"
    
    # Only support gpt-4o and gpt-5
    if ep not in ["gpt-4o", "gpt-5"]:
        raise ValueError(f"Unsupported model: {ep}. Only 'gpt-4o' and 'gpt-5' are supported.")
    
    scope = "api://trapi/.default"
    credential = get_bearer_token_provider(
        ChainedTokenCredential(
            DefaultAzureCredential(),
            ManagedIdentityCredential(),
            AzureCliCredential(),
        ),
        scope,
    )

    if ep == "gpt-5":
        model_name = 'gpt-5'  # Ensure this is a valid model name
        model_version = '2025-08-07'  # Ensure this is a valid model version
        instance = 'msrne/shared' # See https://aka.ms/trapi/models for the instance name, remove /openai (library adds it implicitly)     
        api_version = '2024-12-01-preview'  # Ensure this is a valid API version see: https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation#latest-ga-api-release
    elif ep == "gpt-4o":
        model_name = 'gpt-4o'  # Ensure this is a valid model name
        model_version = '2024-11-20'  # Ensure this is a valid model version
        instance = 'msrne/shared' # See https://aka.ms/trapi/models for the instance name, remove /openai (library adds it implicitly)     
        api_version = '2024-10-21'  # Ensure this is a valid API version see: https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation#latest-ga-api-release


    deployment_name = re.sub(r'[^a-zA-Z0-9-_]', '', f'{model_name}_{model_version}')  # If your Endpoint doesn't have harmonized deployment names, you can use the deployment name directly: see: https://aka.ms/trapi/models
    endpoint = f'https://trapi.research.microsoft.com/{instance}'

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=credential,
        api_version=api_version,
    )

    # Note: With TRAPI "shared" instances, deployments are harmonized, so callers can pass
    # model="gpt-4o" or model="gpt-5" directly. The computed deployment_name is only needed
    # for non-harmonized endpoints; we keep it here for reference but do not return it.
    return client
