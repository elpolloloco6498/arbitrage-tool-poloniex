import requests
import json
from pprint import pprint

def get_coin_tickers(endpoint):
    req = requests.get(endpoint)
    return req.json()

def get_tradable_coins(data_json):
    tradable_coins = []
    for coin in data_json:
        frozen = int(data_json[coin]["isFrozen"])
        post_only = int(data_json[coin]["postOnly"])
        if not frozen and not post_only:
            tradable_coins.append(coin)
    return tradable_coins

def get_structure_triangular_pairs(coin_list):
    triangular_pairs = list()
    remove_duplicate_list = list()
    pair_list = coin_list[0:]

    for pair_a in pair_list:
        base_pair_a, quote_pair_a = pair_a.split("_")
        pair_a_box = [base_pair_a, quote_pair_a]
        for pair_b in pair_list:
            if pair_b != pair_a:
                base_pair_b, quote_pair_b = pair_b.split("_")
                pair_b_box = [base_pair_b, quote_pair_b]
                if base_pair_b in pair_a_box or quote_pair_b in pair_a_box:
                    for pair_c in pair_list:
                        if pair_c != pair_a and pair_c != pair_b:
                            base_pair_c, quote_pair_c = pair_c.split("_")
                            pair_a_b = [base_pair_a, quote_pair_a, base_pair_b, quote_pair_b]
                            if base_pair_c in pair_a_b and quote_pair_c in pair_a_b:
                                #print(f"{pair_a} {pair_b} {pair_c}")
                                pairs = [pair_a, pair_b, pair_c]
                                unique_pairs = ", ".join(sorted(pairs))
                                if unique_pairs not in remove_duplicate_list:
                                    remove_duplicate_list.append(unique_pairs)
                                    match_dict = {
                                        "a_base": base_pair_a,
                                        "b_base": base_pair_b,
                                        "c_base": base_pair_c,
                                        "a_quote": quote_pair_a,
                                        "b_quote": quote_pair_b,
                                        "c_quote": quote_pair_c,
                                        "pair_a": pair_a,
                                        "pair_b": pair_b,
                                        "pair_c": pair_c,
                                        "combined": unique_pairs
                                    }
                                    triangular_pairs.append(match_dict)
    return triangular_pairs

def get_price_for_tpair(tpair, price_json):
    # Extract pairs
    pair_a = tpair["pair_a"]
    pair_b = tpair["pair_b"]
    pair_c = tpair["pair_c"]

    # Extract prices information for given pairs
    pair_a_ask = float(price_json[pair_a]["lowestAsk"])
    pair_a_bid = float(price_json[pair_a]["highestBid"])
    pair_b_ask = float(price_json[pair_b]["lowestAsk"])
    pair_b_bid = float(price_json[pair_b]["highestBid"])
    pair_c_ask = float(price_json[pair_c]["lowestAsk"])
    pair_c_bid = float(price_json[pair_c]["highestBid"])

    # Output dictionary
    return {
        "pair_a_ask": pair_a_ask,
        "pair_a_bid": pair_a_bid,
        "pair_b_ask": pair_b_ask,
        "pair_b_bid": pair_b_bid,
        "pair_c_ask": pair_c_ask,
        "pair_c_bid": pair_c_bid,
    }

def calculate_surface_rates(tpair, prices_dict):
    # Set variables
    starting_amount = 1
    min_surface_rate = 0
    surface_dict = {}
    contract1 = ""
    contract2 = ""
    contract3 = ""
    direction_trade_1 = ""
    direction_trade_2 = ""
    direction_trade_3 = ""
    acquired_coin_t2 = 0
    acquired_coin_t3 = 0
    calculated = False

    # Extract pair variables
    a_base = tpair["a_base"]
    a_quote = tpair["a_quote"]
    b_base = tpair["b_base"]
    b_quote = tpair["b_quote"]
    c_base = tpair["c_base"]
    c_quote = tpair["c_quote"]
    pair_a = tpair["pair_a"]
    pair_b = tpair["pair_b"]
    pair_c = tpair["pair_c"]

    # Extract price information
    a_ask = prices_dict["pair_a_ask"]
    a_bid = prices_dict["pair_a_bid"]
    b_ask = prices_dict["pair_b_ask"]
    b_bid = prices_dict["pair_b_bid"]
    c_ask = prices_dict["pair_c_ask"]
    c_bid = prices_dict["pair_c_bid"]

    # Set directions and loop through
    direction_list = ["forward", "reverse"]
    for direction in direction_list:
        swap_1 = 0
        swap_2 = 0
        swap_3 = 0
        swap_1_rate = 0
        swap_2_rate = 0
        swap_3_rate = 0

        """
            If we are swapping the coin from the left (Base) to the right (Quote) then * 1 / Ask
            If we are swapping the coin from the right (Quote) to the left (Base) then * Bid
        """

        # Assume starting with a_base and swapping for a_quote
        if direction == "forward":
            swap_1 = a_base
            swap_2 = a_quote
            swap_1_rate = 1/a_ask
            direction_trade_1 = "baseToQuote"

        elif direction == "reverse":
            swap_1 = a_quote
            swap_2 = a_base
            swap_1_rate = a_bid
            direction_trade_1 = "quoteToBase"

        # Place first trade
        contract1 = pair_a
        acquired_coin_t1 = starting_amount * swap_1_rate
        #print(direction, pair_a, starting_amount, acquired_coin_t1)

        # Place second trade
        if direction == "forward":

            # a_quote (acquired) matches b_quote
            if a_quote == b_quote and not calculated:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_b
                direction_trade_2 = "quoteToBase"

                # b_base (acquired) matches c_base
                if b_base == c_base and not calculated:
                    swap_3_rate = 1/c_ask
                    swap_3 = c_quote
                    direction_trade_3 = "baseToQuote"

                # b_base (acquired) matches c_quote
                elif b_base == c_quote and not calculated:
                    swap_3_rate = c_bid
                    swap_3 = c_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_c
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            # a_quote (acquired) matches b_base
            elif a_quote == b_base and not calculated:
                swap_2_rate = 1/b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_b
                direction_trade_2 = "baseToQuote"

                # b_quote (acquired) matches c_base
                if b_quote == c_base and not calculated:
                    swap_3_rate = 1 / c_ask
                    swap_3 = c_quote
                    direction_trade_3 = "baseToQuote"

                # b_quote (acquired) matches c_quote
                elif b_quote == c_quote and not calculated:
                    swap_3_rate = c_bid
                    swap_3 = c_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_c
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            # a_quote (acquired) matches c_quote
            elif a_quote == c_quote and not calculated:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_c
                direction_trade_2 = "quoteToBase"

                # c_base (acquired) matches b_base
                if c_base == b_base and not calculated:
                    swap_3_rate = 1 / b_ask
                    swap_3 = b_quote
                    direction_trade_3 = "baseToQuote"

                # c_base (acquired) matches b_quote
                elif c_base == b_quote and not calculated:
                    swap_3_rate = b_bid
                    swap_3 = b_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_b
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            # a_quote (acquired) matches c_base
            elif a_quote == c_base and calculated == 0:
                swap_2_rate = 1/c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_c
                direction_trade_2 = "quoteToBase"

                # c_quote (acquired) matches b_base
                if c_quote == b_base and not calculated:
                    swap_3_rate = 1 / b_ask
                    swap_3 = b_quote
                    direction_trade_3 = "baseToQuote"

                # c_quote (acquired) matches b_quote
                elif c_quote == b_quote and not calculated:
                    swap_3_rate = b_bid
                    swap_3 = b_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_b
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        elif direction == "reverse":

            # a_base (acquired) matches b_quote
            if a_base == b_quote and not calculated:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_b
                direction_trade_2 = "quoteToBase"

                # b_base (acquired) matches c_base
                if b_base == c_base and not calculated:
                    swap_3_rate = 1 / c_ask
                    swap_3 = c_quote
                    direction_trade_3 = "baseToQuote"

                # b_base (acquired) matches c_quote
                elif b_base == c_quote and not calculated:
                    swap_3_rate = c_bid
                    swap_3 = c_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_c
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            # a_base (acquired) matches b_base
            elif a_base == b_base and not calculated:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_b
                direction_trade_2 = "baseToQuote"

                # b_quote (acquired) matches c_base
                if b_quote == c_base and not calculated:
                    swap_3_rate = 1 / c_ask
                    swap_3 = c_quote
                    direction_trade_3 = "baseToQuote"

                # b_quote (acquired) matches c_quote
                elif b_quote == c_quote and not calculated:
                    swap_3_rate = c_bid
                    swap_3 = c_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_c
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            # a_base (acquired) matches c_quote
            elif a_base == c_quote and not calculated:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_c
                direction_trade_2 = "quoteToBase"

                # c_base (acquired) matches b_base
                if c_base == b_base and not calculated:
                    swap_3_rate = 1 / b_ask
                    swap_3 = b_quote
                    direction_trade_3 = "baseToQuote"

                # c_base (acquired) matches b_quote
                elif c_base == b_quote and not calculated:
                    swap_3_rate = b_bid
                    swap_3 = b_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_b
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

            # a_base (acquired) matches c_base
            elif a_base == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                contract2 = pair_c
                direction_trade_2 = "quoteToBase"

                # c_quote (acquired) matches b_base
                if c_quote == b_base and not calculated:
                    swap_3_rate = 1 / b_ask
                    swap_3 = b_quote
                    direction_trade_3 = "baseToQuote"

                # c_quote (acquired) matches b_quote
                elif c_quote == b_quote and not calculated:
                    swap_3_rate = b_bid
                    swap_3 = b_base
                    direction_trade_3 = "quoteToBase"

                contract3 = pair_b
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        profit_loss = acquired_coin_t3-starting_amount
        profit_loss_perc = (profit_loss/starting_amount)*100

        # Trade descriptions
        trade_description_1 = f"Start with {starting_amount} of {swap_1} "
        trade_description_2 = ""
        trade_description_3 = ""

        # Output result
        if profit_loss_perc > min_surface_rate:
            surface_dict = {
                "swap_1": swap_1,
                "swap_2": swap_2,
                "swap_3": swap_3,
                "contract1": contract1,
                "contract2": contract2,
                "contract3": contract3,
                "direction_trade_1": direction_trade_1,
                "direction_trade_2": direction_trade_2,
                "direction_trade_3": direction_trade_3,
                "acquired_coin_t1" : acquired_coin_t1,
                "acquired_coin_t2" : acquired_coin_t2,
                "acquired_coin_t3" : acquired_coin_t3,
                "swap_1_rate": swap_1_rate,
                "swap_2_rate": swap_2_rate,
                "swap_3_rate": swap_3_rate,
                "starting_amount": starting_amount,
                "profit_loss": profit_loss,
                "profit_loss_perc": profit_loss_perc,
                "direction": direction,
                "trade_description_1": trade_description_1,
                "trade_description_2": trade_description_2,
                "trade_description_3": trade_description_3
            }

            return surface_dict

    return surface_dict



