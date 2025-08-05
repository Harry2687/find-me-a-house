import marimo

__generated_with = "0.14.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
    # Borrowing power calculator

    This notebook calculates the borrowing power of an individual given broad parameters.

    The logic is that monthly post tax income minus monthly expenses and monthly mortgage repayments at a benchmark rate should not be negative.

    Post tax income can be calculated [here](https://paycalculator.com.au/) (Australia).
    """
    )
    return


@app.cell
def _(mo):
    benchmark_annual_rate = mo.ui.number(start=0, step=0.01, value=11.5)
    loan_years = mo.ui.number(start=30, stop=35, step=1)
    income_monthly = mo.ui.number()
    expenses_monthly = mo.ui.number()
    return benchmark_annual_rate, expenses_monthly, income_monthly, loan_years


@app.cell
def _(benchmark_annual_rate, expenses_monthly, income_monthly, loan_years, mo):
    mo.md(
        f"""
    Benchmark interest rate (%): {benchmark_annual_rate}\n
    Mortgage term (years): {loan_years}\n
    Income (monthly, post tax): {income_monthly}\n
    Expenses (monthly): {expenses_monthly}
    """
    )
    return


@app.cell
def _(benchmark_annual_rate, expenses_monthly, income_monthly, loan_years):
    benchmark_monthly_rate = benchmark_annual_rate.value/(12*100)
    loan_months = loan_years.value*12

    if income_monthly.value is not None and expenses_monthly.value is not None:
        max_principal = (income_monthly.value - expenses_monthly.value)*((1 + benchmark_monthly_rate)**loan_months - 1)/(benchmark_monthly_rate*(1 + benchmark_monthly_rate)**loan_months)
    else:
        max_principal = 0
    return (max_principal,)


@app.cell
def _(max_principal, mo):
    mo.md(f"""The max borrowing power is ${round(max_principal, 2)}""")
    return


if __name__ == "__main__":
    app.run()
