from .invoice import invoice_total, line_amount


def render(inv, rates):
    out = [f"{inv.number}  {inv.customer}  ({inv.currency})"]
    for line in inv.lines:
        conv = line_amount(line, inv, rates)
        out.append(f"  {line.description:<24}{line.amount:>10} {line.currency} -> {conv:>10} {inv.currency}")
    out.append(f"  {'TOTAL':<24}{'':>18}{invoice_total(inv, rates):>10} {inv.currency}")
    return "\n".join(out)
