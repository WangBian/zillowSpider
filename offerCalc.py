import numpy as np


def offer(home_type, sales_price, interest_rate, rent, property_tax):
    # set expected cash flow to be 100 per month
    expected_cash_flow = 100

    # starting offer to be the same as sales_price
    offer = sales_price

    actual_cahs_flow = rent - \
        total_expense(home_type, offer, interest_rate, rent, property_tax)

    while actual_cahs_flow < expected_cash_flow:
        offer = offer - 100
        actual_cahs_flow = rent - \
            total_expense(home_type, offer, interest_rate, rent, property_tax)

    return offer


def total_expense(home_type, sales_price, interest_rate, rent, property_tax):
    propert_tax = property_tax / 12

    # assume HOA for condo is 250
    if home_type == 'CONDO':
        hoa = 250
    else:
        hoa = 0

    # monthly P&I payment
    monthly_pmt = mortgage_calc(sales_price, interest_rate)

    # assume lawn care for single family is 40
    if home_type == 'SINGLE_FAMILY':
        lawn_care = 40
    else:
        lawn_care = 0

    # assume insurance
    insurance = 50

    # vacancy
    vacancy = rent * 0.05

    # assume maintenance is 7% of rent
    maintenance = rent * 0.07

    # cap expenditure
    cap_exp = rent * 0.07

    # management
    management = 100

    # total_expense
    total_expense = propert_tax + hoa + monthly_pmt + lawn_care + \
        insurance + vacancy + maintenance + cap_exp + management

    return total_expense


def mortgage_calc(sales_price, interest_rate):
    # assume 20% down always
    down_pmt = sales_price * 0.2
    loan_amt = sales_price - down_pmt

    # use convetional 30-year fixed loan
    loan_term = 30
    monthly_rate = interest_rate / 100 / 12

    monthly_pmt = loan_amt * monthly_rate / \
        (1 - 1 / (1 + monthly_rate) ** (loan_term * 12))
    return monthly_pmt


def cash_on_cash_return(sales_price):
    # assume closing cost to be 3000
    closing_cost = 3000
    down_pmt = sales_price * 0.2
    # assume cosmetic repair to be 3000
    repair_cost = 3000

    total_cash_investment = closing_cost + down_pmt + repair_cost

    return 0
