import polars as pl

def get_obi_microprice(bid_price, ask_price, bid_size, ask_size):
    df = pl.DataFrame({
        "bid_price": [bid_price],
        "ask_price": [ask_price],
        "bid_size": [bid_size],
        "ask_size": [ask_size]
    })
    df = df.with_columns([
        ((pl.col("bid_size") - pl.col("ask_size")) / (pl.col("bid_size") + pl.col("ask_size"))).alias("obi"),
        ((pl.col("bid_price") * pl.col("ask_size") + pl.col("ask_price") * pl.col("bid_size")) / (pl.col("bid_size") + pl.col("ask_size"))).alias("micro_price")
    ])
    return df["obi"][0], df["micro_price"][0]

def test_obi_symmetric():
    obi, mp = get_obi_microprice(100.0, 101.0, 50.0, 50.0)
    assert obi == 0.0
    assert mp == 100.5

def test_obi_bid_heavy():
    obi, mp = get_obi_microprice(100.0, 101.0, 80.0, 20.0)
    assert abs(obi - 0.6) < 1e-6
    assert abs(mp - 100.8) < 1e-6
    
def test_obi_ask_heavy():
    obi, mp = get_obi_microprice(100.0, 101.0, 20.0, 80.0)
    assert abs(obi - (-0.6)) < 1e-6
    assert abs(mp - 100.2) < 1e-6
