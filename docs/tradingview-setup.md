# TradingView Webhook Setup

## Alert message (JSON)

```json
{
  "symbol": "NIFTY",
  "action": "buy",
  "price": "{{close}}",
  "indicator": "EMA_CROSS"
}
```

## Pine Script alert example

```pine
//@version=5
indicator("EMA Cross Signal", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
bull = ta.crossover(fast, slow)
plot(fast, color=color.green)
plot(slow, color=color.red)
if bull
    alert('{"symbol":"NIFTY","action":"buy","price":"' + str.tostring(close) + '","indicator":"EMA_CROSS"}', alert.freq_once_per_bar)
```

## Webhook URL

`https://your-domain/api/v1/webhooks/tradingview`

## Signature

Set header `X-TV-Signature` to HMAC-SHA256 hex digest of the raw JSON body using `TRADINGVIEW_WEBHOOK_SECRET`.

Confirmed alerts boost decision confidence by 10% when aligned with technical analysis.
