import argparse
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
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show your PNL history.")
    parser.add_argument("-s", "--symbol", type=str, required=True,
                        help="Symbol to trade on")
    parser.add_argument("-p", "--position", type=str, required=True,
                        help="buy or sell")
    parser.add_argument("-a", "--amount", type=float, required=True,
                        help="amount to be traded")
    parser.add_argument("-e", "--entry", type=float,
                        help="Entry price")
    parser.add_argument("-l", "--leverage", type=int, default=10,
                        help="how much leverage (does not change the amount)")
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


# Client Entry-Target-Stop
class ClientETS(Client):
    def __init__(self, pub, pri, parsed_args):
        super().__init__(pub, pri)
        self.full_args = parsed_args['full_args']
        self.stop_type = parsed_args['stop_type']
        self.stop_value = parsed_args['stop_value']
        self.target_type = parsed_args['target_type']
        self.target_value = parsed_args['target_value']
        self.entry = self.full_args.entry
        self.amount = self.full_args.amount
        self.position = self.full_args.position.upper()
        self.invposition = 'BUY' if self.position == 'SELL' else 'SELL'
        self.symbol = self.full_args.symbol
        self.leverage = self.full_args.leverage

        if self.full_args.verbose:
            self.show_pnl_history()

    def show_pnl_history(self):
        incomes = self.futures_income_history(incomeType="REALIZED_PNL",
                                              startTime=0, limit=1000)
        total = sum([float(inc['income']) for inc in incomes])
        print(f"total profit for last {len(incomes)} trades: {total}")

    def custom_trailing(self, callback):
        print('1s wait... (why is this necessary?)')
        time.sleep(1)
        while 1:
            try:
                last_price = float(self.futures_symbol_ticker(symbol=self.symbol)['price'])
            except ReadTimeout:
                print("timeout (custom_trailing), trying again...")
                time.sleep(1)
                continue
            print(f'last_price is {last_price}...')
            if self.invposition == 'BUY':
                if last_price > self.stop_value:
                    break
            if self.invposition == 'SELL':
                if last_price < self.stop_value:
                    break
            time.sleep(REFRESH_RATE)

        print('STOP HIT!')
        # I don't know why, but here there cannot be a timeInForce param.
        return self.futures_create_order(symbol=self.symbol,
                                         reduceOnly=True,
                                         side=self.invposition,
                                         positionSide='BOTH',
                                         type='TRAILING_STOP_MARKET',
                                         callbackRate=callback,
                                         quantity=self.amount)

    def create_goal(self, stop=0):
        if stop:
            if self.stop_type == 'stop_limit_activation':
                price_stop_limit = self.full_args.price_stop_limit
                return self.futures_create_order(symbol=self.symbol,
                                                 reduceOnly=True,
                                                 side=self.invposition,
                                                 positionSide='BOTH',
                                                 type='STOP',
                                                 quantity=self.amount,
                                                 stopPrice=self.stop_value,
                                                 price=price_stop_limit,
                                                 timeInForce='GTC')
            elif self.stop_type == 'stop_market':
                return self.futures_create_order(symbol=self.symbol,
                                                 reduceOnly=True,
                                                 side=self.invposition,
                                                 positionSide='BOTH',
                                                 type='STOP_MARKET',
                                                 quantity=self.amount,
                                                 stopPrice=self.stop_value,
                                                 timeInForce='GTC')
            elif self.stop_type == 'stop_trailing_stop':
                callback_stop = self.full_args.callback_stop

                p = Process(target=self.custom_trailing, args=(callback_stop,))
                p.start()
                return (p.pid, p)
        else:
            if self.target_type == 'target_limit':
                return self.futures_create_order(symbol=self.symbol,
                                                 reduceOnly=True,
                                                 side=self.invposition,
                                                 positionSide='BOTH',
                                                 price=self.target_value,
                                                 type='LIMIT',
                                                 quantity=self.amount,
                                                 timeInForce='GTC')
            elif self.target_type == 'target_market':
                return self.futures_create_order(symbol=self.symbol,
                                                 reduceOnly=True,
                                                 side=self.invposition,
                                                 positionSide='BOTH',
                                                 stopPrice=self.target_value,
                                                 type='TAKE_PROFIT_MARKET',
                                                 quantity=self.amount,
                                                 timeInForce='GTC')
            elif self.target_type == 'target_trailing_stop':
                callback_target = self.full_args.callback_target
                return self.futures_create_order(symbol=self.symbol,
                                                 reduceOnly=True,
                                                 side=self.invposition,
                                                 positionSide='BOTH',
                                                 type='TRAILING_STOP_MARKET',
                                                 quantity=self.amount,
                                                 callbackRate=callback_target,
                                                 activationPrice=self.target_value)

    def clear_goals(self, goal_dict):
        if stop := goal_dict['stop']:
            if type(stop) == dict:  # case where target is an order.
                self.futures_cancel_order(symbol=self.symbol, orderId=stop['orderId'])
            elif type(stop) == tuple:  # case where target is process
                stop[1].terminate()
        if target := goal_dict['target']:
            self.futures_cancel_order(symbol=self.symbol, orderId=target['orderId'])

    def entry_target_stop(self):
        self.futures_change_leverage(symbol=self.symbol, leverage=self.leverage)
        goals = {'stop': '', 'target': ''}

        # case where we are already on position
        if not self.entry:
            goals['stop'] = self.create_goal(stop=1)
            goals['target'] = self.create_goal()
            print("goals set.")
            return goals

        # set limit order
        limit = self.futures_create_order(symbol=self.symbol,
                                          side=self.position,
                                          positionSide='BOTH',
                                          type='LIMIT',
                                          quantity=self.amount,
                                          price=self.entry,
                                          timeInForce='GTC')

        # set goals
        executed = 0
        print('sending limit...')
        # loop to wait for order to be filled or canceled.
        while limit['status'] != 'CANCELED':
            time.sleep(REFRESH_RATE)
            limit = self.futures_get_order(symbol=self.symbol, orderId=limit['orderId'])
            if limit['status'] == 'NEW':
                continue
            elif limit['executedQty'] != executed:
                print(f"limit status is {limit['status']}...")
                print(f"{self.position} {limit['executedQty']}{self.symbol} foi executado!")
                self.clear_goals(goals)
                goals['stop'] = self.create_goal(stop=1)
                goals['target'] = self.create_goal()
                executed = limit['executedQty']

            if limit['status'] == 'FILLED':
                break
        print("all target and stops are set\n---/---")
        return goals

    def watch_for_end(self, goals):
        # check if any of the goals have already been completed
        time.sleep(1)
        stop = goals['stop']
        target = goals['target']

        print("Waiting for exit...")
        while True:
            try:
                if type(stop) == dict:  # case where target is an order.
                    stop_status = self.futures_get_order(symbol=self.symbol, orderId=stop['orderId'])['status']
                    stop_is_on = stop_status != 'FILLED'

                elif type(stop) == tuple:  # case where target is process
                    stop_is_on = stop[1].is_alive()
                    stop_status = stop_is_on

                target_status = self.futures_get_order(symbol=self.symbol, orderId=target['orderId'])['status']
                target_is_on = target_status != 'FILLED'
            except ReadTimeout:
                print("timeout (watch_for_end), trying again...")
                time.sleep(1)
                continue

            if not (target_is_on and stop_is_on):
                self.clear_goals(goals)
                return
            time.sleep(1)


if __name__ == '__main__':
    parsed_args = init_args()
    client = ClientETS(pub, pri, parsed_args)
    try:
        goals = client.entry_target_stop()
        client.watch_for_end(goals)
    except KeyboardInterrupt:
        # <--- fix here
        client.futures_cancel_all_open_orders(symbol=parsed_args['full_args'].symbol)
