from decimal import Decimal, ROUND_HALF_UP


def hitung_pajak_dan_total(subtotal, tarif_pajak):
    subtotal = Decimal(str(subtotal))
    tarif = Decimal(str(tarif_pajak))

    pajak = (subtotal * tarif / Decimal("100")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    pajak = int(pajak)
    total = int(subtotal) + pajak

    return pajak, total