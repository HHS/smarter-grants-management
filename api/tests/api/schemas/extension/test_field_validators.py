import pytest
from marshmallow import ValidationError

from src.api.schemas.extension import validators
from src.api.schemas.extension.schema_validation_error import SchemaValidationError


def get_error_container(error: ValidationError):
    assert isinstance(error.messages, list)
    assert len(error.messages) == 1
    return error.messages[0]


def test_regexp_accepts_matching_value():
    validator = validators.Regexp(r"^abc$")

    assert validator("abc") == "abc"


def test_regexp_rejects_non_matching_value():
    validator = validators.Regexp(
        r"^abc$",
        error_message="Must match abc.",
    )

    with pytest.raises(ValidationError) as exc_info:
        validator("def")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.FORMAT
    assert error.message == "Must match abc."
    assert error.value == "def"
    assert error.metadata is None


@pytest.mark.parametrize(
    "validator,value",
    [
        (validators.Length(min=2), "ab"),
        (validators.Length(max=2), "ab"),
        (validators.Length(min=2, max=4), "abc"),
        (validators.Length(equal=3), "abc"),
    ],
)
def test_length_accepts_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value,error_type,expected_metadata",
    [
        (
            validators.Length(min=2),
            "a",
            SchemaValidationError.MIN_LENGTH,
            {"minimum": 2, "maximum": None, "equal": None},
        ),
        (
            validators.Length(max=2),
            "abc",
            SchemaValidationError.MAX_LENGTH,
            {"minimum": None, "maximum": 2, "equal": None},
        ),
        (
            validators.Length(min=2, max=4),
            "a",
            SchemaValidationError.MIN_OR_MAX_LENGTH,
            {"minimum": 2, "maximum": 4, "equal": None},
        ),
        (
            validators.Length(min=2, max=4),
            "abcde",
            SchemaValidationError.MIN_OR_MAX_LENGTH,
            {"minimum": 2, "maximum": 4, "equal": None},
        ),
        (
            validators.Length(equal=3),
            "ab",
            SchemaValidationError.EQUALS,
            {"minimum": None, "maximum": None, "equal": 3},
        ),
    ],
)
def test_length_rejects_invalid_values(
    validator,
    value,
    error_type,
    expected_metadata,
):
    with pytest.raises(ValidationError) as exc_info:
        validator(value)

    error = get_error_container(exc_info.value)
    assert error.key == error_type
    assert error.value == value
    assert error.metadata == expected_metadata


@pytest.mark.parametrize(
    "validator,value",
    [
        (validators.WordLimit(min=2), "one two"),
        (validators.WordLimit(max=2), "one two"),
        (validators.WordLimit(min=2, max=4), "one two three"),
        (validators.WordLimit(equal=3), "one two three"),
    ],
)
def test_word_limit_accepts_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value,error_type,expected_metadata",
    [
        (
            validators.WordLimit(min=2),
            "one",
            SchemaValidationError.MIN_WORDS,
            {"minimum": 2, "maximum": None, "equal": None},
        ),
        (
            validators.WordLimit(max=2),
            "one two three",
            SchemaValidationError.MAX_WORDS,
            {"minimum": None, "maximum": 2, "equal": None},
        ),
        (
            validators.WordLimit(min=2, max=4),
            "one",
            SchemaValidationError.MIN_OR_MAX_WORDS,
            {"minimum": 2, "maximum": 4, "equal": None},
        ),
        (
            validators.WordLimit(min=2, max=4),
            "one two three four five",
            SchemaValidationError.MIN_OR_MAX_WORDS,
            {"minimum": 2, "maximum": 4, "equal": None},
        ),
        (
            validators.WordLimit(equal=3),
            "one two",
            SchemaValidationError.EQUALS_WORDS,
            {"minimum": None, "maximum": None, "equal": 3},
        ),
    ],
)
def test_word_limit_rejects_invalid_values(
    validator,
    value,
    error_type,
    expected_metadata,
):
    with pytest.raises(ValidationError) as exc_info:
        validator(value)

    error = get_error_container(exc_info.value)
    assert error.key == error_type
    assert error.value == value
    assert error.metadata == expected_metadata


def test_email_accepts_valid_email():
    validator = validators.Email()

    assert validator("test@example.com") == "test@example.com"


def test_email_rejects_invalid_email():
    validator = validators.Email()

    with pytest.raises(ValidationError) as exc_info:
        validator("not-an-email")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.FORMAT
    assert error.message == "Not a valid email address."
    assert error.value == "not-an-email"
    assert error.metadata == {"type": "email"}


def test_url_accepts_valid_url():
    validator = validators.URL()

    assert validator("https://example.com") == "https://example.com"


def test_url_rejects_invalid_url():
    validator = validators.URL()

    with pytest.raises(ValidationError) as exc_info:
        validator("not-a-url")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.INVALID
    assert error.message == "Not a valid URL."
    assert error.value == "not-a-url"
    assert error.metadata is None


def test_one_of_accepts_valid_choice():
    validator = validators.OneOf(["a", "b", "c"])

    assert validator("b") == "b"


def test_one_of_rejects_invalid_choice():
    validator = validators.OneOf(["a", "b", "c"])

    with pytest.raises(ValidationError) as exc_info:
        validator("d")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.INVALID_CHOICE
    assert "a" in error.message
    assert "b" in error.message
    assert "c" in error.message
    assert error.value == "d"
    assert error.metadata == {"choices": ["a", "b", "c"]}


@pytest.mark.parametrize(
    "validator,value",
    [
        (validators.Range(min=1), 1),
        (validators.Range(max=10), 10),
        (validators.Range(min=1, max=10), 5),
    ],
)
def test_range_accepts_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value,error_type,expected_metadata",
    [
        (
            validators.Range(min=1),
            0,
            SchemaValidationError.MIN_VALUE,
            {
                "minimum": 1,
                "maximum": None,
                "minimum_inclusive": True,
                "maximum_inclusive": True,
            },
        ),
        (
            validators.Range(max=10),
            11,
            SchemaValidationError.MAX_VALUE,
            {
                "minimum": None,
                "maximum": 10,
                "minimum_inclusive": True,
                "maximum_inclusive": True,
            },
        ),
        (
            validators.Range(min=1, max=10),
            0,
            SchemaValidationError.MIN_OR_MAX_VALUE,
            {
                "minimum": 1,
                "maximum": 10,
                "minimum_inclusive": True,
                "maximum_inclusive": True,
            },
        ),
        (
            validators.Range(min=1, max=10),
            11,
            SchemaValidationError.MIN_OR_MAX_VALUE,
            {
                "minimum": 1,
                "maximum": 10,
                "minimum_inclusive": True,
                "maximum_inclusive": True,
            },
        ),
    ],
)
def test_range_rejects_invalid_values(
    validator,
    value,
    error_type,
    expected_metadata,
):
    with pytest.raises(ValidationError) as exc_info:
        validator(value)

    error = get_error_container(exc_info.value)
    assert error.key == error_type
    assert error.value == value
    assert error.metadata == expected_metadata
