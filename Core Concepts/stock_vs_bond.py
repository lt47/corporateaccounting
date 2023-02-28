import inflation_rates
import interest_rates


def preferred_asset(interest_rate: float, inflation_rate: float) -> str:
    # Inflation is said to be high when above 2%
    rate_limit = 2.25
    """Bonds are preferred to stock only when inflation is
    low and interest rates are high."""
    if inflation_rate < rate_limit and interest_rate > rate_limit:
        return "Bonds"
    else:
        return "Stocks"


def main():
    # Check what investment choice is better in Canada
    print(
        f"In Canada, {preferred_asset(interest_rates.get_interest_rate('BOC'), inflation_rates.get_inflation_rate('Canada'))} are currently the preferred asset type.")
    # Check what investment choice is better in America
    print(
        f"In the USA, {preferred_asset(interest_rates.get_interest_rate('FED'), inflation_rates.get_inflation_rate('United States'))} are currently the preferred asset type.")


if __name__ == '__main__':
    main()
