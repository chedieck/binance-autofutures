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
  -s SYMBOL, --symbol SYMBOL
                        Symbol to trade on
  -p POSITION, --position POSITION
                        buy or sell
  -a AMOUNT, --amount AMOUNT
                        amount to be traded
  -e ENTRY, --entry ENTRY
                        Entry price
  -l, --leverage        future contracts?
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

Working in progress, will update the documentation in the future.
