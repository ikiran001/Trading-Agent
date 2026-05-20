from app.domain.signal import SignalCreate


def format_alert(signal: SignalCreate) -> str:
    if signal.signal.value == "HOLD":
        return f"{signal.symbol} — HOLD\nConfidence: {signal.confidence}%"
    lines = [
        f"{signal.signal.value} ALERT: {signal.symbol}",
        f"Category: {signal.category.value}",
    ]
    if signal.instrument:
        lines.append(f"Instrument: {signal.instrument}")
    if signal.entry:
        lines.append(f"Entry: {signal.entry}")
    if signal.stop_loss:
        lines.append(f"SL: {signal.stop_loss}")
    if signal.target_1:
        lines.append(f"Target 1: {signal.target_1}")
    if signal.target_2:
        lines.append(f"Target 2: {signal.target_2}")
    lines.append(f"Confidence: {signal.confidence}%")
    if signal.reasons:
        lines.append("Reasons: " + "; ".join(signal.reasons[:3]))
    return "\n".join(lines)


async def send_telegram(token: str, chat_id: str, message: str) -> None:
    if not token or not chat_id:
        return
    from telegram import Bot

    bot = Bot(token=token)
    await bot.send_message(chat_id=chat_id, text=message)
