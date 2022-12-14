import json
import time
from pprint import pprint
import arbitrage

ENDPOINT_PUBLIC_POLONIUX = "https://poloniex.com/public?command=returnTicker"
TRIANGULAR_PAIRS_FILE = "triangular_pairs.json"

"""Step 0: Gather all tradable coins"""
def step_0():
    coin_json = arbitrage.get_coin_tickers(ENDPOINT_PUBLIC_POLONIUX)
    tradable_coins = arbitrage.get_tradable_coins(coin_json)
    return tradable_coins

"""Step 1: Identify all triangular match for pairs"""
def step_1(coin_list):
    # structured list of all the tradable arbitrage pairs
    triangular_pairs = arbitrage.get_structure_triangular_pairs(coin_list)
    # write list to file
    with open(TRIANGULAR_PAIRS_FILE, "w") as f:
        json.dump(triangular_pairs, f)

    print("[*] File creation successfull")

"""
    Step 2: Calculate surface rate
    Find arbitrage oportunities
"""
def step_2():
    with open(TRIANGULAR_PAIRS_FILE, "r") as json_file:
        structured_pairs = json.load(json_file)
        #pprint(structured_pairs)

    prices_json = arbitrage.get_coin_tickers(ENDPOINT_PUBLIC_POLONIUX)

    for tpair in structured_pairs:
        prices_dict = arbitrage.get_price_for_tpair(tpair, prices_json)
        trade_posibility = arbitrage.calculate_surface_rates(tpair, prices_dict)
        if len(trade_posibility) > 0:
            print(trade_posibility["contract1"], trade_posibility["contract2"], trade_posibility["contract2"], trade_posibility["profit_loss_perc"])
            real_rate_arb = arbitrage.get_depth_from_orderbook(trade_posibility)
            if real_rate_arb["profit_loss"] > 0:
                pprint(real_rate_arb)

if __name__ == "__main__":
    #tradable_coins = step_0()
    #step_1(tradable_coins)
    while True:
        step_2()
        time.sleep(10)

    #depth = arbitrage.get_depth_from_orderbook()

    print("[*] Program executed successfully")