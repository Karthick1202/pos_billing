from decimal import Decimal, ROUND_HALF_UP
from collections.abc import Mapping


def money(value):
    """Round an amount to 2 decimal places."""
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def calculate_bill(items, coupon=0, tenders=None):

    def to_decimal(value, field):
        try:
            result = Decimal(str(value))
        except Exception:
            raise ValueError(f"Invalid {field}")

        if not result.is_finite():
            raise ValueError(f"Invalid {field}")

        return result

    def validate_non_negative(value, field):
        if value < 0:
            raise ValueError(f"{field} cannot be negative")

    # Validate items
    if not isinstance(items, (list, tuple)) or not items:
        raise ValueError("Items must be a non-empty list")

    coupon = money(to_decimal(coupon, "coupon"))
    validate_non_negative(coupon, "Coupon")

    lines = []

    gross = Decimal("0.00")
    line_discount_total = Decimal("0.00")

    # Step 1: Calculate gross and line discounts
    for item in items:

        if not isinstance(item, Mapping):
            raise ValueError("Each item must be a dictionary")

        required = ["sku", "mrp", "qty", "gst_rate"]

        for field in required:
            if field not in item:
                raise ValueError(f"Missing field: {field}")

        sku = item["sku"]

        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("SKU must be a non-empty string")

        mrp = to_decimal(item["mrp"], "MRP")
        gst_rate = to_decimal(item["gst_rate"], "GST rate")
        discount_pct = to_decimal(
            item.get("discount_pct", 0),
            "Discount percentage"
        )

        qty = item["qty"]

        if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
            raise ValueError("Quantity must be a positive whole number")

        validate_non_negative(mrp, "MRP")
        validate_non_negative(gst_rate, "GST rate")

        if not Decimal("0") <= discount_pct <= Decimal("100"):
            raise ValueError("Discount must be between 0 and 100")

        line_gross = money(mrp * qty)

        line_discount = money(
            line_gross * discount_pct / Decimal("100")
        )

        line_amount = money(line_gross - line_discount)

        gross += line_gross
        line_discount_total += line_discount

        lines.append({
            "sku": sku,
            "gross": line_gross,
            "discount": line_discount,
            "amount": line_amount,
            "gst_rate": gst_rate
        })

    gross = money(gross)
    line_discount_total = money(line_discount_total)

    # Step 2: Validate coupon
    bill_after_discount = money(
        sum(line["amount"] for line in lines)
    )

    if coupon > bill_after_discount:
        raise ValueError("Coupon cannot exceed bill amount")

    # Step 3: Allocate coupon proportionally
    coupon_shares = []
    remaining_coupon = coupon

    for index, line in enumerate(lines):

        if index == len(lines) - 1:
            # Last line receives the remaining amount
            share = remaining_coupon

        elif bill_after_discount == 0:
            share = Decimal("0.00")

        else:
            share = money(
                coupon * line["amount"] / bill_after_discount
            )

        if share > line["amount"]:
            raise ValueError("Invalid coupon allocation")

        coupon_shares.append(share)
        remaining_coupon = money(remaining_coupon - share)

    # Step 4: Calculate taxable amount and GST
    taxable = Decimal("0.00")
    cgst = Decimal("0.00")
    sgst = Decimal("0.00")
    net = Decimal("0.00")

    for line, coupon_share in zip(lines, coupon_shares):

        line_net = money(line["amount"] - coupon_share)

        taxable_value = money(
            line_net / (
                Decimal("1") + line["gst_rate"] / Decimal("100")
            )
        )

        gst = money(line_net - taxable_value)

        line_cgst = money(gst / Decimal("2"))
        line_sgst = money(gst - line_cgst)

        taxable += taxable_value
        cgst += line_cgst
        sgst += line_sgst
        net += line_net

    taxable = money(taxable)
    cgst = money(cgst)
    sgst = money(sgst)
    net = money(net)

    # Step 5: Calculate payable and round-off
    payable = net.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    payable = money(payable)

    round_off = money(payable - net)

    # Step 6: Calculate total discount
    total_discount = money(line_discount_total + coupon)

    # Step 7: Prepare output
    result = {
        "gross": f"{gross:.2f}",
        "discount": f"{total_discount:.2f}",
        "taxable": f"{taxable:.2f}",
        "cgst": f"{cgst:.2f}",
        "sgst": f"{sgst:.2f}",
        "net": f"{net:.2f}",
        "round_off": f"{round_off:.2f}",
        "payable": f"{payable:.2f}"
    }

    # Step 8: Validate payment tenders
    if tenders is not None:

        if not isinstance(tenders, (list, tuple)):
            raise ValueError("Tenders must be a list")

        total_paid = Decimal("0.00")
        non_cash_paid = Decimal("0.00")
        cash_paid = Decimal("0.00")

        for tender in tenders:

            if not isinstance(tender, (list, tuple)) or len(tender) != 2:
                raise ValueError("Tender must contain type and amount")

            tender_type, amount = tender

            if not isinstance(tender_type, str):
                raise ValueError("Invalid tender type")

            tender_type = tender_type.upper()

            if tender_type not in ("CASH", "CARD", "UPI"):
                raise ValueError("Tender must be CASH, CARD or UPI")

            amount = money(to_decimal(amount, "tender amount"))
            validate_non_negative(amount, "Tender amount")

            total_paid += amount

            if tender_type == "CASH":
                cash_paid += amount
            else:
                non_cash_paid += amount

        total_paid = money(total_paid)
        non_cash_paid = money(non_cash_paid)
        cash_paid = money(cash_paid)

        if non_cash_paid > payable:
            raise ValueError("Card plus UPI cannot exceed payable")

        if total_paid < payable:
            raise ValueError("Total payment is less than payable")

        change = money(total_paid - payable)

        if change > cash_paid:
            raise ValueError("Change can only be given from cash")

        result["change"] = f"{change:.2f}"

    return result