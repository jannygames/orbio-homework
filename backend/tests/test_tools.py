from app.services.product_tools import (
    TOOLS_BY_NAME,
    compare_products,
    execute_tool,
    get_product_details,
    get_products,
    get_tools,
    list_categories,
    recommend_products,
)


def test_get_products_returns_all_by_default():
    result = get_products()

    assert result["count"] > 0
    assert result["count"] == len(result["products"])


def test_get_products_filters_by_max_price():
    result = get_products(max_price=50)

    assert result["count"] > 0
    assert all(p["effective_price"] <= 50 for p in result["products"])


def test_get_products_filters_by_category():
    result = get_products(category="electronics")

    assert result["count"] > 0
    assert all(p["category"] == "electronics" for p in result["products"])


def test_get_products_filters_by_in_stock():
    result = get_products(in_stock=False)

    assert result["count"] > 0
    assert all(p["in_stock"] is False for p in result["products"])


def test_get_products_filters_by_discount():
    result = get_products(on_discount=True)

    assert result["count"] > 0
    assert all(p["discount_percent"] > 0 for p in result["products"])


def test_get_products_search_finds_headphones():
    result = get_products(search="headphones")

    assert result["count"] >= 1
    assert any("headphone" in p["description"].lower() or "headphone" in p["name"].lower() for p in _raw(result))


def _raw(result):
    return [get_product_details(product_id=p["id"]) for p in result["products"]]


def test_get_product_details_by_name():
    result = get_product_details(name="Kindle Paperwhite")

    assert result["id"] == "prod-006"
    assert "price" in result
    assert "specs" in result


def test_get_product_details_by_id():
    result = get_product_details(product_id="prod-006")

    assert result["name"].startswith("Kindle")


def test_get_product_details_not_found():
    result = get_product_details(product_id="does-not-exist")

    assert "error" in result


def test_execute_tool_unknown_tool_returns_error_not_raise():
    result = execute_tool("not_a_real_tool", {})

    assert "error" in result


def test_execute_tool_bad_args_returns_error_not_raise():
    result = execute_tool("get_products", {"unexpected_kwarg": 1})

    assert "error" in result


def test_get_products_sort_and_limit():
    result = get_products(sort_by="price_asc", limit=3)

    assert result["returned"] == 3
    assert result["count"] > 3
    prices = [p["effective_price"] for p in result["products"]]
    assert prices == sorted(prices)


def test_list_categories_returns_counts_and_price_range():
    result = list_categories()

    assert result["count"] >= 1
    for category in result["categories"]:
        assert category["product_count"] >= 1
        assert category["min_price"] <= category["max_price"]


def test_compare_products_side_by_side():
    result = compare_products(["Kindle Paperwhite", "Sony WH-1000XM5"])

    assert len(result["products"]) == 2
    assert result["not_found"] == []


def test_compare_products_requires_at_least_two():
    result = compare_products(["Kindle Paperwhite"])

    assert "error" in result


def test_compare_products_reports_unknown():
    result = compare_products(["Kindle Paperwhite", "Nonexistent Gadget"])

    assert len(result["products"]) == 1
    assert result["not_found"] == ["Nonexistent Gadget"]


def test_recommend_products_ranks_by_rating_within_budget():
    result = recommend_products(max_price=100, limit=3)

    recs = result["recommendations"]
    assert 1 <= len(recs) <= 3
    ratings = [p["rating"] for p in recs]
    assert ratings == sorted(ratings, reverse=True)
    assert all(p["effective_price"] <= 100 for p in recs)
    assert all(p["in_stock"] for p in recs)


def test_registry_matches_declarations():
    declared = {fd.name for tool in get_tools() for fd in tool.function_declarations}
    assert declared == set(TOOLS_BY_NAME.keys())
