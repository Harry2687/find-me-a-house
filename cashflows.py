import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    return mo, pl


@app.cell
def _(mo):
    # Mortgage parameters
    principal = mo.ui.number(600000)
    annual_rate = mo.ui.number(start=0, step=0.01, value=6)
    loan_years = mo.ui.number(start=30, stop=35, step=1)
    repayment_frequency = mo.ui.dropdown(options=["weekly", "fortnightly", "monthly"], value="fortnightly")

    # Income parameters
    annual_income = mo.ui.number(74312)
    marginal_tax_rate = mo.ui.number(30)

    # Rental parameters
    annual_rental_income = mo.ui.number(0)
    annual_rental_expense = mo.ui.number(0)
    return (
        annual_income,
        annual_rate,
        annual_rental_expense,
        annual_rental_income,
        loan_years,
        marginal_tax_rate,
        principal,
        repayment_frequency,
    )


@app.cell(hide_code=True)
def _(
    annual_income,
    annual_rate,
    annual_rental_expense,
    annual_rental_income,
    loan_years,
    marginal_tax_rate,
    mo,
    principal,
    repayment_frequency,
):
    mo.md(
        f"""
    # Mortgage parameters
    Principal: {principal}\n
    Interest rate (%): {annual_rate}\n
    Mortgage term (years): {loan_years}\n
    Repayment frequency: {repayment_frequency}

    # Income parameters
    Income (annual, post tax): {annual_income}\n
    Marginal tax rate: {marginal_tax_rate}\n

    # Rental parameters
    Rental income: {annual_rental_income}\n
    Rental expense: {annual_rental_expense}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Calculate repayment values using [repayment formula](https://en.wikipedia.org/wiki/Mortgage_calculator#Monthly_payment_formula).""")
    return


@app.cell
def _(
    annual_income,
    annual_rate,
    annual_rental_expense,
    annual_rental_income,
    loan_years,
    principal,
    repayment_frequency,
):
    # Determine number of payments per year given repayment frequency
    match repayment_frequency.value:
        case "weekly":
            n_repayments = 52
        case "fortnightly":
            n_repayments = 26
        case "monthly":
            n_repayments = 12

    # Interest rate given the repayment frequency
    r = annual_rate.value/(100*n_repayments)

    # Total number of repayments given repayment frequency
    N = loan_years.value*n_repayments

    # Principal
    P = principal.value

    # Repayment value at repayment frequency
    if r != 0:
        c = (r*P)/(1-(1+r)**(-N))
    else:
        c = P/N

    # Income at repayment frequency
    income = annual_income.value/n_repayments

    # Rental income/expense at repayment frequency
    rental_income = annual_rental_income.value/n_repayments
    rental_expense = annual_rental_expense.value/n_repayments
    return N, P, c, income, r, rental_expense, rental_income


@app.cell
def _(
    N,
    P,
    c,
    income,
    marginal_tax_rate,
    pl,
    r,
    rental_expense,
    rental_income,
):
    data = pl.DataFrame(
        data={"period": range(0, N+1)}
    ).with_columns(
        pl.when(pl.col("period") == 0)
        .then(pl.lit(P))
        .otherwise(
            ((1+r)**pl.col("period")*P-(((1+r)**pl.col("period")-1)/r)*c).round(2)
        )
        .alias("principal_remaining")
    ).with_columns(
        -pl.col("principal_remaining")
        .diff()
        .round(2)
        .alias("principal_paid")
    ).with_columns(
        (c-pl.col("principal_paid"))
        .round(2)
        .alias("interest_paid")
    ).with_columns(
        pl.when(pl.col("period") == 0)
        .then(None)
        .otherwise(pl.lit(rental_income))
        .alias("rental_income"),
        pl.when(pl.col("period") == 0)
        .then(None)
        .otherwise(pl.lit(rental_expense))
        .alias("rental_expense")
    ).with_columns(
        pl.when(rental_income > 0)
        .then(pl.col("rental_income")-pl.col("interest_paid"))
        .otherwise(pl.when(pl.col("period") == 0).then(None).otherwise(pl.lit(0)))
        .round(2)
        .alias("net_income")
    ).with_columns(
        (-pl.col("net_income")*marginal_tax_rate.value/100)
        .round(2)
        .alias("tax")
    ).with_columns(
        pl.when(pl.col("period") == 0)
        .then(None)
        .otherwise(pl.lit(income))
        .round(2)
        .alias("income")
    ).with_columns(
        (
            pl.col("income")
            + pl.col("rental_income")
            - pl.col("principal_paid")
            - pl.col("interest_paid")
            - pl.col("rental_expense")
            + pl.col("tax")
        )
        .round(2)
        .alias("net_cashflow")
    ).with_columns(
        ((pl.col("income")-pl.col("net_cashflow"))*100/(pl.col("income")))
        .round(2)
        .alias("expense_ratio")
    )

    data
    return


if __name__ == "__main__":
    app.run()
