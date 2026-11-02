import pytest
from pydantic import ValidationError

from src.models import ContractChangeOutput


def valid():
    return {"sections_changed": ["Cláusula 3"], "topics_touched": ["Precio"], "summary_of_the_change": "MODIFICACIÓN: ..."}


def test_valid_output():
    out = ContractChangeOutput.model_validate(valid())
    assert out.sections_changed == ["Cláusula 3"]


def test_missing_field_fails():
    data = valid()
    del data["topics_touched"]
    with pytest.raises(ValidationError):
        ContractChangeOutput.model_validate(data)


def test_extra_field_is_rejected():
    with pytest.raises(ValidationError):
        ContractChangeOutput.model_validate({**valid(), "evaluation": 10})


def test_wrong_type_fails():
    with pytest.raises(ValidationError):
        ContractChangeOutput.model_validate({**valid(), "sections_changed": "Cláusula 3"})


def test_blank_items_and_empty_summary_fail():
    with pytest.raises(ValidationError):
        ContractChangeOutput.model_validate({**valid(), "topics_touched": ["  "]})
    with pytest.raises(ValidationError):
        ContractChangeOutput.model_validate({**valid(), "summary_of_the_change": "   "})


def test_duplicates_removed_and_strings_stripped():
    out = ContractChangeOutput.model_validate({**valid(), "sections_changed": [" A ", "A", "B"]})
    assert out.sections_changed == ["A", "B"]
