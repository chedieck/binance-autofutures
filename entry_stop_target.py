import argparse

def init_args():
    parser = argparse.ArgumentParser("Set an entry, stop and target at the same time.")
    parser.add_argument("-s", "--symbol", type=str, required=True,
                        help="Symbol to trade on")
    parser.add_argument("-p", "--position", type=str, required=True,
                        help="buy or sell")
    parser.add_argument("-f", "--futures", action="store_true",
                        help="future contracts?")
    parser.add_argument("-e", "--entry", type=float, required=True,
                        help="Entry price")
    # stops
    parser.add_argument("-sla", "--stop-limit-activation", type=float,
                        help="Stop-limit activation price")
    parser.add_argument("-sm", "--stop-market", type=float,
                        help="Stop market price")
    parser.add_argument("-psl", "--price-stop-limit", type=float,
                        help="Stop-limit price, if -sla is used")
    # targets
    parser.add_argument("-tla", "--target-limit-activation", type=float,
                        help="Target limit-activation price")
    parser.add_argument("-tm", "--target-market", type=float,
                        help="Target market price")
    parser.add_argument("-tts", "--target-trailing-stop", type=float,
                        help="Target trailing stop")
    parser.add_argument("-ptl", "--price-target-limit", type=float,
                        help="Target limit price, if -tla is used")
    parser.add_argument("-ct", "--callback-target", type=float,
                        help="Target trailing stop callback percentage")
    args = parser.parse_args()
    args_tuples = args._get_kwargs()
    # basic logic errors
    assert args.position.upper() == 'BUY' or args.position.upper() == 'SELL', (
            "Position must be 'BUY' or 'SELL'")

    #assert if all pairs are being used in conjunct
    assert bool(args.stop_limit_activation) == bool(args.price_stop_limit), (
            "-sla must be used with -slp")
    assert bool(args.target_limit_activation) == bool(args.price_target_limit), (
            "-tla must be used with -tlp")
    assert bool(args.target_trailing_stop) == bool(args.callback_target), (
            "-tts must be used with -tc")

    # check for used option
    stops = []
    targets = []
    for (arg, value) in args_tuples:
        if value:
            if arg.startswith('stop'):
                stops.append((arg, value))
            if arg.startswith('target'):
                targets.append((arg, value))
    assert len(stops) == len(targets) == 1, "Exacly one type of stop/target must be provided."
    stop_type, stop_value = stops[0]
    target_type, target_value = targets[0]


    # Deal with side inequality logic:
    # assert if stops, targets, and possibly
    # activations and limits are following
    # the order they should.
    if args.position.upper() == 'BUY':
        assert stop_value < args.entry, (
                "Stop must be lower than entry for BUY order")
        assert target_value > args.entry, (
                "Target must be greater than entry for BUY order")
        if stop_type == 'stop_limit_activation':
            assert args.price_stop_limit < stop_value, (
                    "Stop price must be smaller than activation for BUY order")
        if target_type == 'target_limit_activation':
            assert args.price_target_limit > target_value, (
                    "Target price must be greater than activation for BUY order")

    elif args.position.upper() == 'SELL':
        assert stop_value > args.entry, (
                "Stop must be grater than entry for SELL order")
        assert target_value < args.entry, (
            "Target must be lower than entry for SELL order")
        if stop_type == 'stop_limit_activation':
            assert args.price_stop_limit > stop_value, (
                    "Stop price must be greater than activation for SELL order")
        if target_type == 'target_limit_activation':
            assert args.price_target_limit < target_value, (
                    "Target price must be smaller than activation for SELL order")

    return args, stops, targets


x = init_args()

