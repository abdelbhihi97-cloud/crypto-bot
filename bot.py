import ccxt
import pandas as pd
import ta
import os
import requests

# جلب بيانات تليجرام بأمان من أسرار GitHub
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("بيانات تليجرام غير متوفرة!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"خطأ في إرسال تليجرام: {e}")

# إعدادات Binance Spot لأهم العملات المتقلبة
exchange = ccxt.binance({'enableRateLimit': True})
symbols = ["SOL/USDT", "BTC/USDT", "ETH/USDT", "XRP/USDT", "DOGE/USDT"]

def run_bot():
    print("بدء فحص أسواق Binance...")
    for symbol in symbols:
        try:
            # جلب آخر 250 شمعة فريم 15 دقيقة
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=250)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # المؤشرات الخمسة
            df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            
            bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_upper'] = bb.bollinger_hband()
            
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
            df['adx'] = adx.adx()

            last = df.iloc[-2]
            current_price = last['close']

            # شروط الفلترة الخماسية الدقيقة للشراء
            c1 = current_price > last['ema200']             # اتجاه صاعد
            c2 = last['rsi'] < 48                           # ليس متشبعاً شرائياً
            c3 = last['macd'] > last['macd_signal']        # زخم صاعد إيجابي
            c4 = current_price <= last['bb_lower'] * 1.003  # ارتداد من الحد السفلي
            c5 = last['adx'] > 22                           # قوة في الحركة

            if c1 and c2 and c3 and c4 and c5:
                sl = round(current_price * 0.991, 4)
                tp = round(current_price * 1.020, 4)
                msg = (
                    f"🚀 *فرصة شراء قوية (Binance Spot)* 🚀\n\n"
                    f"📌 *الزوج:* `{symbol}`\n"
                    f"💲 *السعر الحالي:* `{current_price}`\n"
                    f"🛑 *وقف الخسارة (SL):* `{sl}`\n"
                    f"🎯 *جني الأرباح (TP):* `{tp}`\n"
                    f"⚡ *الحالة:* توافق مؤشرات الفلترة الخماسية بنجاح تام!"
                )
                send_telegram_message(msg)
                print(f"تم رصد وإرسال صفقة لـ {symbol}")

        except Exception as e:
            print(f"خطأ في فحص {symbol}: {e}")

if __name__ == "__main__":
    run_bot()
