# ================= PROFITMAGNET CORE SERVER =================

import asyncio
from fastapi import FastAPI
import time
import os
from typing import Dict

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ================= FASTAPI =================
app = FastAPI(title="ProfitMagnet Core 🚀")

signals: Dict[str, dict] = {}

# ================= SYMBOL NORMALIZER =================
def normalize_symbol(symbol: str) -> str:
    symbol = symbol.upper()

    for suffix in ["M", ".M", "C", ".C", "S", ".S", "PRO", ".PRO"]:
        if symbol.endswith(suffix):
            symbol = symbol.replace(suffix, "")

    return symbol

# ================= API =================

@app.get("/")
def home():
    return {
        "status": "running",
        "service": "ProfitMagnet Core",
        "active_symbols": list(signals.keys())
    }

@app.get("/core")
def get_signal(symbol: str):
    symbol = normalize_symbol(symbol)

    if symbol not in signals:
        return {
            "symbol": symbol,
            "signal": "none",
            "id": 0
        }

    return signals[symbol]

# ================= TELEGRAM CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

raw_users = os.getenv("AUTHORIZED_USERS", "")

AUTHORIZED_USERS = [
    int(x.strip())
    for x in raw_users.split(",")
    if x.strip().isdigit()
]

print(f"✅ Authorized Users Loaded: {AUTHORIZED_USERS}")

telegram_app = None

# ================= TELEGRAM HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Unauthorized")
        return

    text = update.message.text.upper().strip()
    parts = text.split()

    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Format:\nBUY XAUUSD\nSELL EURUSD\nCLOSE XAUUSD\nCLOSE_ID XAUUSD 12345"
        )
        return

    action = parts[0]
    symbol = normalize_symbol(parts[1])

    # ===== DEFAULT ID =====
    signal_id = int(time.time())

    # ===== CLOSE SPECIFIC TRADE =====
    if action == "CLOSE_ID":
        if len(parts) < 3:
            await update.message.reply_text("❌ Use: CLOSE_ID XAUUSD 12345")
            return

        try:
            signal_id = int(parts[2])
        except:
            await update.message.reply_text("❌ Invalid ID")
            return

        signals[symbol] = {
            "symbol": symbol,
            "signal": "close_id",
            "id": signal_id
        }

        print(f"🎯 CLOSE_ID: {signals[symbol]}")
        await update.message.reply_text(f"🎯 Closing trade ID {signal_id}")
        return

    # ===== VALID ACTIONS =====
    if action not in ["BUY", "SELL", "CLOSE"]:
        await update.message.reply_text("❌ Invalid command")
        return

    signals[symbol] = {
        "symbol": symbol,
        "signal": action.lower(),
        "id": signal_id
    }

    print(f"📡 Signal: {signals[symbol]}")
    await update.message.reply_text(f"✅ {action} {symbol}")

# ================= START TELEGRAM =================

async def start_telegram():
    global telegram_app

    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

@app.on_event("startup")
async def startup():
    asyncio.create_task(start_telegram())

# ================= MAIN =================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    print(f"⚡ ProfitMagnet Core running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
