from billing import calculate_bill


# Example E1: Single item
items1 = [
    {
        "sku": "TEE-301",
        "mrp": 499.00,
        "qty": 2,
        "gst_rate": 5
    }
]

result1 = calculate_bill(
    items1,
    tenders=[("CASH", 1000)]
)

print("E1 OUTPUT:")
print(result1)


# Example E2: Line discount + card
items2 = [
    {
        "sku": "JEANS-201",
        "mrp": 1899.00,
        "qty": 1,
        "gst_rate": 12,
        "discount_pct": 10
    },
    {
        "sku": "TEE-301",
        "mrp": 499.00,
        "qty": 1,
        "gst_rate": 5
    }
]

result2 = calculate_bill(
    items2,
    tenders=[("CARD", 2208)]
)

print("\nE2 OUTPUT:")
print(result2)