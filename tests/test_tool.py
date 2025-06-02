from term_assistant.tools import Parameter, Tool


def foo_1() -> None:
    """A function without parameters."""


def foo_2(bar: str, baz: int = 42) -> None:
    """A function with parameters."""


def test_tool_properties() -> None:
    tool = Tool(foo_1, {}, "A message to user")
    assert tool.function.__name__ == foo_1.__name__
    assert tool.parameters == {}
    assert tool.message == "A message to user"


def test_tool_parameters() -> None:
    tool = Tool(
        foo_2,
        {
            "bar": Parameter("string", "A string"),
            "baz": Parameter("integer", "An integer", True),
        },
    )
    assert tool.parameters["bar"].type == "string"
    assert tool.parameters["bar"].description == "A string"
    assert not tool.parameters["bar"].optional
    assert tool.parameters["baz"].type == "integer"
    assert tool.parameters["baz"].description == "An integer"
    assert tool.parameters["baz"].optional


def test_openai_tool() -> None:
    tool = Tool(
        foo_2,
        {
            "bar": Parameter("str", "A string"),
            "baz": Parameter("int", "An integer", True),
        },
    )
    openai_tool = tool.openai_tool
    assert type(openai_tool) is dict
    assert openai_tool["function"].get("name", "") == foo_2.__name__
    assert (
        openai_tool["function"].get("description", "") == foo_2.__doc__.strip()
        if foo_2.__doc__
        else ""
    )
    params = openai_tool["function"].get("parameters", {})
    assert params != {}
    assert params["type"] == "object"
    properties = params["properties"]
    assert properties != {}
    assert type(properties) is dict
    assert properties["bar"]["type"] == "str"
