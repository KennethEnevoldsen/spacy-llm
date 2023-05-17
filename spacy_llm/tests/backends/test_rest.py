# mypy: ignore-errors
import copy

import pytest
import spacy

from ..compat import has_openai_key

PIPE_CFG = {
    "backend": {
        "@llm_backends": "spacy.REST.v1",
        "api": "OpenAI",
        "config": {"temperature": 0.3, "model": "gpt-3.5-turbo"},
    },
    "task": {"@llm_tasks": "spacy.NoOp.v1"},
}


def test_initialization():
    """Test initialization and simple run"""
    nlp = spacy.blank("en")
    cfg = copy.deepcopy(PIPE_CFG)
    cfg["backend"]["api"] = "NoOp"
    cfg["backend"]["config"] = {"model": "NoOp"}
    nlp.add_pipe("llm", config=cfg)
    nlp("This is a test.")


@pytest.mark.external
def test_rest_backend_error_handling():
    """Test error handling for default/minimal REST backend."""
    nlp = spacy.blank("en")
    with pytest.raises(ValueError) as err:
        nlp.add_pipe(
            "llm",
            config={
                "task": {"@llm_tasks": "spacy.NoOp.v1"},
                "backend": {"config": {"model": "x-gpt-3.5-turbo"}},
            },
        )
    assert "The specified model 'x-gpt-3.5-turbo' is not available." in str(err.value)


@pytest.mark.parametrize("model", ("gpt-3.5-turbo", "text-davinci-002"))
@pytest.mark.external
def test_openai(model: str):
    """Test OpenAI call to /chat/completions and /completions backend.
    model (str): Model to use.
    """
    nlp = spacy.blank("en")
    cfg = copy.deepcopy(PIPE_CFG)
    cfg["backend"]["config"]["model"] = model
    cfg["backend"]["config"]["url"] = (
        "https://api.openai.com/v1/chat/completions"
        if model == "gpt-3.5-turbo"
        else "https://api.openai.com/v1/completions"
    )
    nlp.add_pipe(
        "llm",
        config=cfg,
    )
    nlp("test")
    assert len(list(nlp.pipe(["test 1", "test 2"]))) == 2


@pytest.mark.skipif(has_openai_key is False, reason="OpenAI API key not available")
def test_model_backend_compatibility():
    """Tests whether incompatible model and backend are detected as expected."""
    nlp = spacy.blank("en")
    cfg = copy.deepcopy(PIPE_CFG)
    cfg["backend"]["config"]["model"] = "gpt-4"
    cfg["backend"]["config"]["url"] = "https://api.openai.com/v1/completions"
    with pytest.warns(
        UserWarning,
        match="Configured endpoint https://api.openai.com/v1/completions diverges from expected endpoint "
        "https://api.openai.com/v1/chat/completions for selected model 'gpt-4'. Please ensure that this endpoint "
        "supports your model.",
    ):
        nlp.add_pipe(
            "llm",
            config=cfg,
        )
