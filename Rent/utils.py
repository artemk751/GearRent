def plural_uk(number, forms):
    number = abs(number)
    if 11 <= number % 100 <= 14:
        return forms[2]
    last_digit = number % 10
    if last_digit == 1:
        return forms[0]
    if 2 <= last_digit <= 4:
        return forms[1]
    return forms[2]


def products_count_text(count):
    word = plural_uk(count, ("товар", "товари", "товарів"))
    return f"{count} {word}"
