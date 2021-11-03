import pytest

from indico_toolkit.association import Positioning, positioning
from indico_toolkit.errors import ToolkitInputError


def generate_mapped_pred(
    bbTop=0,
    bbBot=10,
    bbLeft=0,
    bbRight=10,
    page_num=0,
    label="a",
):
    return {
        "bbTop": bbTop,
        "bbBot": bbBot,
        "bbLeft": bbLeft,
        "bbRight": bbRight,
        "label": label,
        "page_num": page_num,
    }


@pytest.mark.parametrize(
    "input, expected",
    # first pred is "above", second is "below"
    [
        ((generate_mapped_pred(page_num=1), generate_mapped_pred(page_num=0)), False),
        ((generate_mapped_pred(page_num=0), generate_mapped_pred(page_num=1)), False),
        (
            (
                generate_mapped_pred(),
                generate_mapped_pred(11, 20),
            ),
            True,
        ),
        (
            (
                generate_mapped_pred(),
                generate_mapped_pred(11, 20, 11, 13),
            ),
            False,
        ),
        (
            (
                generate_mapped_pred(),
                generate_mapped_pred(11, 20, 5, 13),
            ),
            True,
        ),
        (
            (
                generate_mapped_pred(bbLeft=20, bbRight=30),
                generate_mapped_pred(11, 20, 5, 13),
            ),
            False,
        ),
        (
            (
                generate_mapped_pred(10, 20),
                generate_mapped_pred(),
            ),
            False,
        ),
    ],
)
def test_positioned_above_same_page_true(input, expected):
    print(input)
    positioning = Positioning()
    is_above = positioning.positioned_above(input[0], input[1], must_be_same_page=True)
    assert is_above == expected


@pytest.mark.parametrize(
    "input, expected",
    # first pred is "above", second is "below"
    [
        ((generate_mapped_pred(page_num=1), generate_mapped_pred()), False),
        ((generate_mapped_pred(), generate_mapped_pred(page_num=1)), True),
        (
            (
                generate_mapped_pred(bbLeft=20, bbRight=30),
                generate_mapped_pred(page_num=1),
            ),
            False,
        ),
    ],
)
def test_positioned_above_same_page_false(input, expected):
    positioning = Positioning()
    is_above = positioning.positioned_above(input[0], input[1], must_be_same_page=False)
    assert is_above == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred()), True),
        ((generate_mapped_pred(), generate_mapped_pred(20, 30)), False),
        ((generate_mapped_pred(15, 21), generate_mapped_pred(20, 30)), True),
        ((generate_mapped_pred(29, 31), generate_mapped_pred(20, 30)), True),
        ((generate_mapped_pred(30, 31), generate_mapped_pred(20, 30)), False),
        ((generate_mapped_pred(29, 31), generate_mapped_pred(20, 30)), True),
    ],
)
def test_yaxis_overlap(input, expected):
    overlap = Positioning.yaxis_overlap(input[0], input[1])
    assert overlap == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred()), True),
        ((generate_mapped_pred(), generate_mapped_pred(5, 7)), True),
        ((generate_mapped_pred(), generate_mapped_pred(9, 15, 50, 60)), True),
        ((generate_mapped_pred(), generate_mapped_pred(11, 30)), False),
        ((generate_mapped_pred(10, 20), generate_mapped_pred(20, 30)), False),
        ((generate_mapped_pred(), generate_mapped_pred(page_num=2)), True),
    ],
)
def test_positioned_on_same_level(input, expected):
    position = Positioning()
    output = position.positioned_on_same_level(
        input[0], input[1], must_be_same_page=False
    )
    assert output == expected


def test_positioned_on_same_level_must_be_same_page():
    position = Positioning()
    output = position.positioned_on_same_level(
        generate_mapped_pred(), generate_mapped_pred(page_num=1)
    )
    assert output == False


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(), generate_mapped_pred(0, 10, 20, 30)), 10),
        ((generate_mapped_pred(), generate_mapped_pred(20, 30)), 10),
        ((generate_mapped_pred(100, 110, 20, 30), generate_mapped_pred()), 90.55),
    ],
)
def test_get_min_distance(input, expected):
    position = Positioning()
    distance = position.get_min_distance(input[0], input[1])
    assert round(distance, 2) == expected


def test_get_min_distance_page_exception():
    position = Positioning()
    with pytest.raises(ToolkitInputError):
        position.get_min_distance(
            generate_mapped_pred(), generate_mapped_pred(page_num=1)
        )


@pytest.mark.parametrize(
    "input, expected",
    [
        ((generate_mapped_pred(page_num=2), generate_mapped_pred(0, 10, 20, 30)), 2010),
        ((generate_mapped_pred(page_num=1), generate_mapped_pred(20, 30)), 1010),
    ],
)
def test_get_min_distance_different_pages(input, expected):
    position = Positioning()
    distance = position.get_min_distance(input[0], input[1], page_height=1000)
    assert round(distance, 2) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        (((10, 10), (10, 20)), 10),
        (((110, 30), (10, 10)), 101.98),
        (((100, 20), (10, 10)), 90.55),
    ],
)
def test_distance_between_points(input, expected):
    distance = Positioning._distance_between_points(input[0], input[1])
    assert round(distance, 2) == expected
