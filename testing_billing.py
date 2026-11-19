import pytest
from billing import calculate_bill


# ----------------------------------
# 1. Example E1 - Single item
# ----------------------------------

def test_single_item_cash_payment():
    items = [
        {
            "sku": "TEE-301",
            "mrp": 499,
            "qty": 2,
            "gst_rate": 5
        }
    ]

    result = calculate_bill(
        items,
        tenders=[("CASH", 1000)]
    )

    assert result == {
        "gross": "998.00",
        "discount": "0.00",
        "taxable": "950.48",
        "cgst": "23.76",
        "sgst": "23.76",
        "net": "998.00",
        "round_off": "0.00",
        "payable": "998.00",
        "change": "2.00"
    }


# ----------------------------------
# 2. Example E2 - Line discount
# ----------------------------------

def test_line_discount_card_payment():
    items = [
        {
            "sku": "JEANS-201",
            "mrp": 1899,
            "qty": 1,
            "gst_rate": 12,
            "discount_pct": 10
        },
        {
            "sku": "TEE-301",
            "mrp": 499,
            "qty": 1,
            "gst_rate": 5
        }
    ]

    result = calculate_bill(
        items,
        tenders=[("CARD", 2208)]
    )

    assert result == {
        "gross": "2398.00",
        "discount": "189.90",
        "taxable": "2001.22",
        "cgst": "103.44",
        "sgst": "103.44",
        "net": "2208.10",
        "round_off": "-0.10",
        "payable": "2208.00",
        "change": "0.00"
    }


# ----------------------------------
# 3. Coupon discount
# ----------------------------------

def test_coupon_discount():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 0
        },
        {
            "sku": "ITEM-2",
            "mrp": 200,
            "qty": 1,
            "gst_rate": 0
        }
    ]

    result = calculate_bill(items, coupon=30)

    assert result["gross"] == "300.00"
    assert result["discount"] == "30.00"
    assert result["net"] == "270.00"


# ----------------------------------
# 4. Coupon cannot exceed bill
# ----------------------------------

def test_coupon_exceeds_bill():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 5
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(items, coupon=200)


# ----------------------------------
# 5. Mixed CASH and UPI payment
# ----------------------------------

def test_mixed_cash_upi_payment():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 998,
            "qty": 1,
            "gst_rate": 0
        }
    ]

    result = calculate_bill(
        items,
        tenders=[
            ("CASH", 500),
            ("UPI", 498)
        ]
    )

    assert result["payable"] == "998.00"
    assert result["change"] == "0.00"


# ----------------------------------
# 6. Payment less than payable
# ----------------------------------

def test_insufficient_payment():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 0
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(
            items,
            tenders=[("CASH", 50)]
        )


# ----------------------------------
# 7. Card + UPI cannot exceed payable
# ----------------------------------

def test_card_upi_exceeds_payable():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 0
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(
            items,
            tenders=[
                ("CARD", 60),
                ("UPI", 50)
            ]
        )


# ----------------------------------
# 8. Invalid quantity
# ----------------------------------

@pytest.mark.parametrize("qty", [0, -1, 1.5, True])
def test_invalid_quantity(qty):
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": qty,
            "gst_rate": 5
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(items)


# ----------------------------------
# 9. 100% line discount
# ----------------------------------

def test_hundred_percent_discount():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 5,
            "discount_pct": 100
        }
    ]

    result = calculate_bill(items)

    assert result["gross"] == "100.00"
    assert result["discount"] == "100.00"
    assert result["net"] == "0.00"
    assert result["payable"] == "0.00"


# ----------------------------------
# 10. Invalid discount percentage
# ----------------------------------

@pytest.mark.parametrize("discount", [-10, 101])
def test_invalid_discount(discount):
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 5,
            "discount_pct": discount
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(items)


# ----------------------------------
# 11. Negative MRP
# ----------------------------------

def test_negative_mrp():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": -100,
            "qty": 1,
            "gst_rate": 5
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(items)


# ----------------------------------
# 12. Invalid tender type
# ----------------------------------

def test_invalid_tender_type():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 0
        }
    ]

    with pytest.raises(ValueError):
        calculate_bill(
            items,
            tenders=[("CHEQUE", 100)]
        )


# ----------------------------------
# 13. No tenders provided
# ----------------------------------

def test_without_tenders():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 100,
            "qty": 1,
            "gst_rate": 5
        }
    ]

    result = calculate_bill(items)

    assert "change" not in result
    assert result["payable"] == "100.00"


# ----------------------------------
# 14. Empty items
# ----------------------------------

def test_empty_items():
    with pytest.raises(ValueError):
        calculate_bill([])


# ----------------------------------
# 15. Half-up rounding
# ----------------------------------

def test_half_up_rounding():
    items = [
        {
            "sku": "ITEM-1",
            "mrp": 10.125,
            "qty": 1,
            "gst_rate": 0
        }
    ]

    result = calculate_bill(items)

    assert result["gross"] == "10.13"
    assert result["payable"] == "10.00"