import argparse
import request
from binance.client import Client
from api import pub, pri
import time
from multiprocessing import Process
from requests.exceptions import ReadTimeout


REFRESH_RATE = 0.5


def init_args():
    """
    As of now, the script only trades futures.
    For both stop and targets you can use limit, market or trailing.
    """
    parser = argparse.ArgumentParser("Set an entry, stop and target at the same time.")
    parser.add_argument("-s", "--symbol", type=str, required=True,
                        help="Symbol to trade on")
    parser.add_argument("-p", "--position", type=str, required=True,
                        help="buy or sell")
    parser.add_argument("-a", "--amount", type=float, required=True,
                        help="amount to be traded")
    parser.add_argument("-e", "--entry", type=float,
                        help="Entry price")
    parser.add_argument("-l", "--leverage", action="store_true", default=10,
                        help="future contracts?")
    # stops
    parser.add_argument("-sla", "--stop-limit-activation", type=float,
                        help="Stop-limit activation price")
    parser.add_argument("-sm", "--stop-market", type=float,
                        help="Stop market price")
    parser.add_argument("-sts", "--stop-trailing-stop", type=float,
                        help="Stop trailing stop")
    parser.add_argument("-psl", "--price-stop-limit", type=float,
                        help="Stop-limit price, if -sla is used")
    parser.add_argument("-cs", "--callback-stop", type=float,
                        help="Stop trailing stop callback percentage")
    # targets
    parser.add_argument("-tl", "--target-limit", type=float,
                        help="Target limit price")
    parser.add_argument("-tm", "--target-market", type=float,
                        help="Target market price")
    parser.add_argument("-tts", "--target-trailing-stop", type=float,
                        help="Target trailing stop")
    parser.add_argument("-ct", "--callback-target", type=float,
                        help="Target trailing stop callback percentage")
    args = parser.parse_args()
    # basic logic errors
    assert args.position.upper() == 'BUY' or args.position.upper() == 'SELL', (
            "Position must be 'BUY' or 'SELL'")

    # assert if all pairs are being used together
    assert bool(args.stop_limit_activation) == bool(args.price_stop_limit), (
            "-sla must be used with -slp")
    assert bool(args.stop_trailing_stop) == bool(args.callback_stop), (
            "-sts must be used with -cs")
    assert bool(args.target_trailing_stop) == bool(args.callback_target), (
            "-tts must be used with -ct")

    # check for used option
    args_tuples = args._get_kwargs()
    stops = []
    targets = []
    for (arg, value) in args_tuples:
        if value:
            if arg.startswith('stop'):
                stops.append((arg, value))
            if arg.startswith('target'):
                targets.append((arg, value))
    assert len(stops) == len(targets) == 1, (
            "Exacly one type of stop/target must be provided.")
    stop_type, stop_value = stops[0]
    target_type, target_value = targets[0]

    # Deal with side inequality logic:
    # assert if stops, targets, and possibly
    # activations and limits are following
    # the order they should.
    if args.position.upper() == 'BUY':
        if args.entry:
            assert stop_value < args.entry, (
                    "Stop must be lower than entry for BUY order")
            assert target_value > args.entry, (
                    "Target must be greater than entry for BUY order")
        if stop_type == 'stop_limit_activation':
            assert args.price_stop_limit < stop_value, (
                    "Stop price must be smaller than activation for BUY order")

    elif args.position.upper() == 'SELL':
        if args.entry:
            assert stop_value > args.entry, (
                    "Stop must be grater than entry for SELL order")
            assert target_value < args.entry, (
                "Target must be lower than entry for SELL order")
        if stop_type == 'stop_limit_activation':
            assert args.price_stop_limit > stop_value, (
                    "Stop price must be greater than activation for SELL order")

    return {'full_args': args,
            'stop_type': stop_type,
            'stop_value': stop_value,
            'target_type': target_type,
            'target_value': target_value}


class ClientETS(Client):
    def income_full_history(self):
        incomes = self.futures_income_history()
        types = set()
        total = 0
        for inc in incomes:
            types.add(inc['incomeType'])
            total += float(inc['income'])
        return types, total

    def custom_trailing(self, **params):
        print('dormindo...')
        time.sleep(1)
        print('dormiu')
        thresh_price = params.get('thresh_price')
        position = params.get('position')
        symbol = params.get('symbol')
        amount = params.get('amount')
        callback = params.get('callback')
        while 1:
            try:
                last_price = float(self.futures_symbol_ticker(symbol=symbol)['price'])
            except ReadTimeout:
                print("timeout, trying again...")
                time.sleep(1)
                continue
            print(f'last_price is {last_price}...')
            if position == 'BUY':
                if last_price > thresh_price:
                    break
            if position == 'SELL':
                if last_price < thresh_price:
                    break
            time.sleep(REFRESH_RATE)

        print(f'BREAKEAOU')
        # I don't know why, but here there cannot be timeInForce param.
        return self.futures_create_order(symbol=symbol,
                                  reduceOnly=True,
                                  side=position,
                                  positionSide='BOTH',
                                  type='TRAILING_STOP_MARKET',
                                  callbackRate=callback,
                                  quantity=amount)

    def create_goal(self, parsed_args, amount, stop=0):
        full_args = parsed_args['full_args']
        stop_type = parsed_args['stop_type']
        stop_value = parsed_args['stop_value']
        target_type = parsed_args['target_type']
        target_value = parsed_args['target_value']
        position = 'BUY' if full_args.position.upper() == 'SELL' else 'SELL'
        symbol = full_args.symbol

        if stop:
            if stop_type == 'stop_limit_activation':
                price_stop_limit = full_args.price_stop_limit
                return self.futures_create_order(symbol=symbol,
                                                 reduceOnly=True,
                                                 side=position,
                                                 positionSide='BOTH',
                                                 type='STOP',
                                                 quantity=amount,
                                                 stopPrice=stop_value,
                                                 price=price_stop_limit,
                                                 timeInForce='GTC')
            elif stop_type == 'stop_market':
                return self.futures_create_order(symbol=symbol,
                                                 reduceOnly=True,
                                                 side=position,
                                                 positionSide='BOTH',
                                                 type='STOP_MARKET',
                                                 quantity=amount,
                                                 stopPrice=stop_value,
                                                 timeInForce='GTC')
            elif stop_type == 'stop_trailing_stop':
                callback_stop = full_args.callback_stop
                local_args = {'thresh_price': stop_value,
                              'symbol': symbol,
                              'position': position,
                              'amount': amount,
                              'callback': callback_stop}

                p = Process(target=self.custom_trailing, kwargs=local_args)
                p.start()
                return (p.pid, p)
        else:
            if target_type == 'target_limit':
                return self.futures_create_order(symbol=symbol,
                                                 reduceOnly=True,
                                                 side=position,
                                                 positionSide='BOTH',
                                                 type='TAKE_PROFIT',
                                                 quantity=amount,
                                                 price=target_value,
                                                 timeInForce='GTC')
            elif target_type == 'target_market':
                return self.futures_create_order(symbol=symbol,
                                          reduceOnly=True,
                                          side=position,
                                          positionSide='BOTH',
                                          stopPrice=target_value,
                                          type='TAKE_PROFIT_MARKET',
                                          quantity=amount,
                                          timeInForce='GTC')
            elif target_type == 'target_trailing_stop':
                callback_target = full_args.callback_target
                return self.futures_create_order(symbol=symbol,
                                                 reduceOnly=True,
                                                 side=position,
                                                 positionSide='BOTH',
                                                 type='TRAILING_STOP_MARKET',
                                                 quantity=amount,
                                                 callbackRate=callback_target,
                                                 activationPrice=target_value)

    def clear_goals(self, goal_dict):
        if stop := goal_dict['stop']:
            if type(stop) == dict:  # case where target is an order.
                self.futures_cancel_order(symbol=stop['symbol'], orderId=stop['orderId'])
            elif type(stop) == tuple:  # case where target is process
                stop[1].terminate()
        if target := goal_dict['target']:
            self.futures_cancel_order(symbol=target['symbol'], orderId=target['orderId'])

    def entry_target_stop(self, parsed_args):
        full_args = parsed_args['full_args']
        position = full_args.position.upper()
        amount = full_args.amount
        symbol = full_args.symbol
        leverage = full_args.leverage
        entry = full_args.entry
        self.futures_change_leverage(symbol=symbol, leverage=leverage)
        goals = {'stop': '', 'target': ''}

        # case where we are already on position
        if not entry:
            goals['stop'] = self.create_goal(parsed_args, amount, stop=1)
            goals['target'] = self.create_goal(parsed_args, amount)
            print("goals set.")
            return goals

        # set limit order
        limit = self.futures_create_order(symbol=symbol,
                                          side=position,
                                          positionSide='BOTH',
                                          type='LIMIT',
                                          quantity=amount,
                                          price=entry,
                                          timeInForce='GTC')

        # set goals
        executed = 0
        print('sending limit...')
        while limit['status'] != 'CANCELED':
            time.sleep(REFRESH_RATE)
            limit = self.futures_get_order(symbol=symbol, orderId=limit['orderId'])
            if limit['status'] == 'NEW':
                continue
            elif limit['executedQty'] != executed:
                print(f"limit status is {limit['status']}...")
                print(f"{limit['executedQty']} foi executado!")
                self.clear_goals(goals)
                goals['stop'] = self.create_goal(parsed_args, limit['executedQty'], stop=1)
                goals['target'] = self.create_goal(parsed_args, limit['executedQty'])
                executed = limit['executedQty']

            if limit['status'] == 'FILLED':
                break
            print(f"goals: {goals}")
        print(f"all target and stops are set\n---/---")
        return goals

    def watch_for_end(self, goals):
        # check if any of the goals have already been completed
        time.sleep(1)
        stop = goals['stop']
        target = goals['target']
        symbol = goals['target']['symbol']
        while True:
            try:
                print("waiting at exit loop...")
                if type(stop) == dict:  # case where target is an order.
                    stop_status = self.futures_get_order(symbol=symbol, orderId=stop['orderId'])['status']
                    stop_is_on = stop_status != 'FILLED'

                elif type(stop) == tuple:  # case where target is process
                    stop_is_on = stop[1].is_alive()
                    stop_status = stop_is_on

                target_status = self.futures_get_order(symbol=symbol, orderId=target['orderId'])['status']
                target_is_on = target_status != 'FILLED'
            except ReadTimeout:
                print("timeout, trying again...")
                time.sleep(1)
                continue
            
            if not (target_is_on and stop_is_on):
                return
            time.sleep(1)


if __name__ == '__main__':
    parsed_args = init_args()
    client = ClientETS(pub, pri)
    try:
        goals = client.entry_target_stop(parsed_args)
        client.watch_for_end(goals)
    except KeyboardInterrupt:
        client.futures_cancel_all_open_orders(symbol=parsed_args['full_args'].symbol)
