from babel.numbers import get_territory_currencies
import pycountry

country_currency = {}

for country in pycountry.countries:

    try:
        currency = get_territory_currencies(country.alpha_2)

        if currency:
            country_currency[country.alpha_2] = currency[0]

    except:
        pass

currency = country_currency