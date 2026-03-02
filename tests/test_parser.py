from app.services.parser import Parser


def test_parse_sale_amount_then_item():
    parsed = Parser.parse_sale("500 bread")
    assert parsed is not None
    assert parsed.amount == 500
    assert parsed.item == "bread"
    assert parsed.quantity == 1


def test_parse_sale_quantity_prefix():
    parsed = Parser.parse_sale("3x 500 bread")
    assert parsed is not None
    assert parsed.amount == 1500
    assert parsed.item == "bread"
    assert parsed.quantity == 3


def test_parse_sale_item_then_amount():
    parsed = Parser.parse_sale("bread 500")
    assert parsed is not None
    assert parsed.amount == 500
    assert parsed.item == "bread"
    assert parsed.quantity == 1


def test_parse_expense_amount_category():
    amount, category = Parser.parse_expense("500 supplies")
    assert amount == 500
    assert category == "supplies"


def test_parse_expense_category_amount():
    amount, category = Parser.parse_expense("supplies 500")
    assert amount == 500
    assert category == "supplies"
