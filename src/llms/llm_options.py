from langchain_ollama import ChatOllama
from sarvam import SarvamChat


def get_llm_options():
    return ["zai", "nvidia", "mistral", "openai", "gemini", 'sarvam', 'minimax']


def get_llm(name: str | None = None):
    """
    Returns specific ollama or sarvam chat model, default = deepseek
    :param name: name of the model
    :param name:
    :return:
    """
    if name == "zai":
        return _get_chat_ollama_instance(
            model='glm-5:cloud',
        )
    elif name == "nvidia":
        return _get_chat_ollama_instance(
            model='nemotron-3-nano:30b-cloud',
        )
    elif name == "mistral":
        return _get_chat_ollama_instance(
            model='mistral-large-3:675b-cloud',
        )
    elif name == 'openai':
        return _get_chat_ollama_instance(
            model='gpt-oss:120b-cloud',
        )
    elif name == 'gemini':
        return _get_chat_ollama_instance(
            model='gemini-3-flash-preview:cloud',
        )
    elif name == 'sarvam':
        return SarvamChat(
            reasoning_effort="medium",
            temperature=0.3,
            max_retry=3,
            wiki_grounding=False,
            top_p=0.9
        )
    elif name == 'minimax':
        return _get_chat_ollama_instance('minimax-m2.5:cloud')
    else:
        return _get_chat_ollama_instance(
            model='deepseek-v3.2:cloud',
        )


def _get_chat_ollama_instance(model: str):
    import os
    assert os.getenv("OLLAMA_API_KEY") is not None
    return ChatOllama(
        model=model,
        base_url="https://ollama.com",  # Cloud endpoint
        client_kwargs={
            "headers": {"Authorization": "Bearer " + os.getenv("OLLAMA_API_KEY")},
            "timeout": 60.0  # Timeout in seconds
        }
    )
