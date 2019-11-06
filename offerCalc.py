import numpy as np


def offer(rent):
    return 0


def expense():
    return 0


def cap_exp():
    return 0


def mortgage_calc(sales_price, interest_rate):
    # assume 20% down always
    down_pmt = float(sales_price * 0.2)
    loan_amt = sales_price - down_pmt

    # use convetional 30-year fixed loan
    loan_term = 30
    monthly_rate = interest_rate / 100 / 12

    monthly_pmt = loan_amt * monthly_rate / \
        (1 - 1/ (1 + monthly_rate) ** (loan_term * 12))
    return monthly_pmt
