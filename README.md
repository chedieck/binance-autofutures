# binance-autofutures
## beta version.

```
usage: Set an entry, stop and target at the same time. [-h] -s SYMBOL -p POSITION -a AMOUNT [-e ENTRY] [-l]
                                                       [-sla STOP_LIMIT_ACTIVATION] [-sm STOP_MARKET]
                                                       [-sts STOP_TRAILING_STOP] [-psl PRICE_STOP_LIMIT]
                                                       [-cs CALLBACK_STOP] [-tl TARGET_LIMIT] [-tm TARGET_MARKET]
                                                       [-tts TARGET_TRAILING_STOP] [-ct CALLBACK_TARGET]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Show your PNL history.
  -s SYMBOL, --symbol SYMBOL
                        Symbol to trade on
  -p POSITION, --position POSITION
                        buy or sell
  -a AMOUNT, --amount AMOUNT
                        amount to be traded
  -e ENTRY, --entry ENTRY
                        Entry price
  -l, --leverage        how much leverage (does not change the amount)
  -sla STOP_LIMIT_ACTIVATION, --stop-limit-activation STOP_LIMIT_ACTIVATION
                        Stop-limit activation price
  -sm STOP_MARKET, --stop-market STOP_MARKET
                        Stop market price
  -sts STOP_TRAILING_STOP, --stop-trailing-stop STOP_TRAILING_STOP
                        Stop trailing stop
  -psl PRICE_STOP_LIMIT, --price-stop-limit PRICE_STOP_LIMIT
                        Stop-limit price, if -sla is used
  -cs CALLBACK_STOP, --callback-stop CALLBACK_STOP
                        Stop trailing stop callback percentage
  -tl TARGET_LIMIT, --target-limit TARGET_LIMIT
                        Target limit price
  -tm TARGET_MARKET, --target-market TARGET_MARKET
                        Target market price
  -tts TARGET_TRAILING_STOP, --target-trailing-stop TARGET_TRAILING_STOP
                        Target trailing stop
  -ct CALLBACK_TARGET, --callback-target CALLBACK_TARGET
                        Target trailing stop callback percentage
```
---

(Working in progress, will update the documentation in the future.)
### WARNING! This code is a work in progress and may contain bugs. Use it at your own risk.

This script uses **Binance API**. To set up the keys, just create an `api.py` file on your cloned directory with two lines:

```
pub = "<your_public_api_key_goes_here>"
pri = "<your_private_api_key_goes_here>"
```

---

When running the command, note that the `--symbol`, `--amount` and `--position` are mandatory arguments.

 Exactly one type of stop and one type of target also must be provided. If the `--stop-trailing-stop` option is used, then the `--callback-stop` must be set. Similarly, the `--target-trailing-stop` requires the `--callback-target` option. At last, if the `--stop-limit-activation` is the chosen stop type, the `--price-stop-limit` must be set.

The `--amount` is the quantity that will be longed/shorted, and it is not affected by the `--leverage`. For example, if the leverage is set to 20x (default value), and you choose to buy 1 BTC (`--symbol BTCUSDT --position buy --amount 1`) for 10000 dollars, then 500 dollars of your futures wallet will be needed to process the order. On the other hand, if you pass the additional `--leverage 100` argument, thus setting the leverage to 100x, only 100 dollars will be needed. On those two scenarios the potential for profits and losses are the same, as in both of them a long position of exactly 1 BTC will be set.


The `--verbose`, `--leverage` options are not required. The `--entry` option is also not required: you can also use the script if you are already on a position.

---

Examples: 
1. `python entry_stop_target.py -s BTCUSDT -p buy -a 0.1 -e 10686.5 -sts 10680 -cs 0.1 -tl 10690`

    * This command will try to buy 0.1 BTC at $10686.5. If it succeds on doing so, it will set a limit order to close the position (sell the same amount, 0.1 BTC) at $10690; or, if the price reaches $10680 first, it will set a [trailing stop](https://www.binance.com/en/support/faq/360042299292) order with a callback rate of 0.1%.

2. `python entry_stop_target.py -s LINKUSDT -p sell -a 50 -e 19.9 -sm 21 -tts 15.1 -ct 1`

    * This command will try to sell (short) 50 LINKS at $19.9. If it succeds on doing so, it will set a [trailing stop](https://www.binance.com/en/support/faq/360042299292) order at $15.1 to close the position (buy the same amount, 50 LINKS), with callback rate of 1%; or it will close the position by buying at market price, if the price ever reaches $21.


