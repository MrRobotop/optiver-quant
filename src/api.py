import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from confluent_kafka import Consumer
from schema.market_data_pb2 import MarketData, TradeSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Optiver Quant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:19092")

async def consume_market_data(queue: asyncio.Queue):
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'fastapi-market-consumer',
        'auto.offset.reset': 'latest'
    }
    consumer = Consumer(conf)
    consumer.subscribe(['market-events'])
    
    import time
    last_sent = {}
    
    while True:
        msg = consumer.poll(0.01)
        if msg is None or msg.error():
            await asyncio.sleep(0.01)
            continue
            
        md = MarketData()
        md.ParseFromString(msg.value())
        
        now = time.time()
        # Throttle each individual symbol to 150ms UI updates
        if now - last_sent.get(md.symbol, 0) > 0.15:
            last_sent[md.symbol] = now
            
            await queue.put({
                "type": "market_data",
                "symbol": md.symbol,
                "timestamp_ns": md.timestamp_ns,
                "bid_price": md.bid_price,
                "ask_price": md.ask_price,
                "bid_size": md.bid_size,
                "ask_size": md.ask_size
            })
        await asyncio.sleep(0)

async def consume_trade_signals(queue: asyncio.Queue):
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'fastapi-signal-consumer',
        'auto.offset.reset': 'latest'
    }
    consumer = Consumer(conf)
    consumer.subscribe(['trade-signals'])
    
    while True:
        msg = consumer.poll(0.05)
        if msg is None or msg.error():
            await asyncio.sleep(0.05)
            continue
            
        ts = TradeSignal()
        ts.ParseFromString(msg.value())
        
        await queue.put({
            "type": "trade_signal",
            "symbol": ts.symbol,
            "timestamp_ns": ts.timestamp_ns,
            "action": ts.action,
            "size": ts.size,
            "price": ts.price,
            "strategy": ts.strategy_name
        })
        await asyncio.sleep(0)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    
    task_md = asyncio.create_task(consume_market_data(queue))
    task_ts = asyncio.create_task(consume_trade_signals(queue))
    
    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        task_md.cancel()
        task_ts.cancel()
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
