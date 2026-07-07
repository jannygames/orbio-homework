from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from google.genai import types

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = BACKEND_ROOT / "products.json"


@lru_cache
def _load_products() -> list[dict[str, Any]]:
    with PRODUCTS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["products"]


def _effective_price(product: dict[str, Any]) -> float:
    discount = product.get("discount_percent", 0) or 0
    return round(product["price"] * (1 - discount / 100), 2)


def _summarize(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": product["id"],
        "name": product["name"],
        "brand": product["brand"],
        "category": product["category"],
        "price": product["price"],
        "discount_percent": product.get("discount_percent", 0),
        "effective_price": _effective_price(product),
        "in_stock": product["in_stock"],
        "rating": product["rating"],
    }


def _detail(product: dict[str, Any]) -> dict[str, Any]:
    return {**product, "effective_price": _effective_price(product)}


def _resolve_product(identifier: str) -> dict[str, Any] | None:
    products = _load_products()
    for product in products:
        if product["id"].lower() == identifier.lower():
            return product
    for product in products:
        if identifier.lower() in product["name"].lower():
            return product
    return None

def get_products(
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    in_stock: bool | None = None,
    on_discount: bool | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for product in _load_products():
        if category and product["category"].lower() != category.lower():
            continue

        effective_price = _effective_price(product)
        if max_price is not None and effective_price > max_price:
            continue
        if min_price is not None and effective_price < min_price:
            continue

        if in_stock is not None and product["in_stock"] != in_stock:
            continue

        if on_discount is not None:
            has_discount = (product.get("discount_percent", 0) or 0) > 0
            if has_discount != on_discount:
                continue

        if search:
            haystack = " ".join(
                [product["name"], product["brand"], product["category"], product["description"]]
            ).lower()
            if search.lower() not in haystack:
                continue

        results.append(_summarize(product))

    if sort_by == "price_asc":
        results.sort(key=lambda p: p["effective_price"])
    elif sort_by == "price_desc":
        results.sort(key=lambda p: p["effective_price"], reverse=True)
    elif sort_by == "rating_desc":
        results.sort(key=lambda p: p["rating"], reverse=True)

    total = len(results)
    if limit is not None and limit > 0:
        results = results[:limit]

    return {"count": total, "returned": len(results), "products": results}


def get_product_details(
    product_id: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    identifier = product_id or name
    if not identifier:
        return {"error": "Provide either product_id or name."}

    product = _resolve_product(identifier)
    if product is None:
        return {"error": f"No product found matching {identifier!r}."}
    return _detail(product)


def list_categories() -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for product in _load_products():
        by_category.setdefault(product["category"], []).append(product)

    categories = []
    for name, items in sorted(by_category.items()):
        prices = [_effective_price(p) for p in items]
        categories.append(
            {
                "category": name,
                "product_count": len(items),
                "in_stock_count": sum(1 for p in items if p["in_stock"]),
                "min_price": min(prices),
                "max_price": max(prices),
            }
        )
    return {"count": len(categories), "categories": categories}


def compare_products(identifiers: list[str]) -> dict[str, Any]:
    if not identifiers or len(identifiers) < 2:
        return {"error": "Provide at least two product ids or names to compare."}

    found: list[dict[str, Any]] = []
    not_found: list[str] = []
    for identifier in identifiers:
        product = _resolve_product(identifier)
        if product is None:
            not_found.append(identifier)
        else:
            found.append(_detail(product))

    return {"products": found, "not_found": not_found}


def recommend_products(
    max_price: float | None = None,
    category: str | None = None,
    in_stock_only: bool = True,
    limit: int = 3,
) -> dict[str, Any]:
    limit = max(1, min(limit, 10))
    candidates = get_products(
        category=category,
        max_price=max_price,
        in_stock=True if in_stock_only else None,
        sort_by="rating_desc",
    )["products"]
    candidates.sort(key=lambda p: (-p["rating"], p["effective_price"]))
    return {"count": len(candidates[:limit]), "recommendations": candidates[:limit]}

@dataclass(frozen=True)
class Tool:
    handler: Callable[..., dict[str, Any]]
    declaration: types.FunctionDeclaration

    @property
    def name(self) -> str:
        return self.declaration.name


_TOOLS: list[Tool] = [
    Tool(
        handler=get_products,
        declaration=types.FunctionDeclaration(
            name="get_products",
            description=(
                "Search and filter the product catalog. Use for questions like 'what "
                "products do you have', 'what is under 50 EUR', 'do you have headphones "
                "in stock', or 'what is on discount'. Returns a compact list of matching "
                "products."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category, e.g. 'electronics', 'kitchen', 'fitness', 'home', 'office'.",
                    },
                    "max_price": {"type": "number", "description": "Maximum effective price (after discount) in EUR."},
                    "min_price": {"type": "number", "description": "Minimum effective price (after discount) in EUR."},
                    "in_stock": {
                        "type": "boolean",
                        "description": "If true, only in-stock products; if false, only out-of-stock ones.",
                    },
                    "on_discount": {"type": "boolean", "description": "If true, only products currently on discount."},
                    "search": {
                        "type": "string",
                        "description": "Free-text search across name, brand, category and description.",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["price_asc", "price_desc", "rating_desc"],
                        "description": "Optional ordering of the results.",
                    },
                    "limit": {"type": "integer", "description": "Maximum number of products to return."},
                },
            },
        ),
    ),
    Tool(
        handler=get_product_details,
        declaration=types.FunctionDeclaration(
            name="get_product_details",
            description=(
                "Get the full details (price, specs, description) of a single product, by "
                "exact id or full/partial name. Use for precise questions about one "
                "product, e.g. 'how much does the Kindle Paperwhite cost?'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Exact product id, e.g. 'prod-006'."},
                    "name": {"type": "string", "description": "Full or partial product name, e.g. 'Kindle Paperwhite'."},
                },
            },
        ),
    ),
    Tool(
        handler=list_categories,
        declaration=types.FunctionDeclaration(
            name="list_categories",
            description=(
                "List all product categories with a count and price range for each. Use for "
                "open-ended questions like 'what kind of products do you sell?' or 'what "
                "categories do you have?'."
            ),
            parameters={"type": "object", "properties": {}},
        ),
    ),
    Tool(
        handler=compare_products,
        declaration=types.FunctionDeclaration(
            name="compare_products",
            description=(
                "Compare two or more products side by side (resolved by id or name). Use for "
                "questions like 'which is better, X or Y?' or 'compare A, B and C'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "identifiers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Two or more product ids or names to compare.",
                    },
                },
                "required": ["identifiers"],
            },
        ),
    ),
    Tool(
        handler=recommend_products,
        declaration=types.FunctionDeclaration(
            name="recommend_products",
            description=(
                "Recommend the best-rated products within an optional budget and/or category. "
                "Use for questions like 'what's a good gift under 100 EUR?' or 'recommend a "
                "kitchen gadget'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "max_price": {"type": "number", "description": "Optional maximum effective price in EUR."},
                    "category": {"type": "string", "description": "Optional category to restrict recommendations to."},
                    "in_stock_only": {
                        "type": "boolean",
                        "description": "Only recommend in-stock products (default true).",
                    },
                    "limit": {"type": "integer", "description": "How many recommendations to return (default 3)."},
                },
            },
        ),
    ),
]

TOOLS_BY_NAME: dict[str, Tool] = {tool.name: tool for tool in _TOOLS}


def get_tools() -> list[types.Tool]:
    return [types.Tool(function_declarations=[tool.declaration for tool in _TOOLS])]


def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    tool = TOOLS_BY_NAME.get(name)
    if tool is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return tool.handler(**args)
    except Exception as exc:
        return {"error": f"Tool execution failed: {exc}"}
