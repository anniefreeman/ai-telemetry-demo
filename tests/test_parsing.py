from sustainable_fashion_advisor.parsing import parse_materials


def test_parse_materials_supports_multiple_components():
    materials = parse_materials("55% Wool, 25% Recycled Polyester, 20% Nylon")

    assert [component.name for component in materials] == [
        "wool",
        "recycled polyester",
        "nylon",
    ]
    assert [component.percentage for component in materials] == [55.0, 25.0, 20.0]
