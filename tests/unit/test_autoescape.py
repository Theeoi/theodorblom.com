import pytest


@pytest.mark.parametrize(
    "name, expected",
    [
        ("page.html.jinja", True),
        ("page.html", True),
        ("page.htm", True),
        ("page.xml", True),
        ("page.xhtml", True),
        ("image.svg", True),
        (None, True),
        ("document.txt", False),
        ("document.txt.jinja", False),
    ],
)
def test_autoescape_selection(test_client, name, expected):
    assert test_client.application.jinja_env.autoescape(name) is expected
