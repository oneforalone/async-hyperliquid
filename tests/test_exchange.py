import pytest

from async_hyperliquid.async_hyper import AsyncHyper, LimitOrder


@pytest.mark.asyncio(loop_scope="session")
async def test_update_leverage(hl: AsyncHyper):
    leverage = 10
    coin = "BTC"
    resp: dict = await hl.update_leverage(leverage, coin)
    assert resp["status"] == "ok"


@pytest.mark.asyncio(loop_scope="session")
async def test_spot_order(hl: AsyncHyper):
    # coin = "BTC/USDC"
    coin = "@142"  # @142 is the coin name for symbol BTC/USDC
    buy_value = 10 + 0.3
    buy_price = 10_000.0
    buy_sz = buy_value / buy_price
    order_req = {
        "coin": coin,
        "is_buy": True,
        "sz": buy_sz,
        "px": buy_price,
        "is_market": False,
        "order_type": LimitOrder.ALO.value,
    }

    resp: dict = await hl.place_order(**order_req)
    assert resp["status"] == "ok"

    oid = resp["response"]["data"]["statuses"][0]["resting"]["oid"]
    assert oid

    resp = await hl.cancel_order(coin, oid)
    assert resp["status"] == "ok"
    assert resp["response"]["data"]["statuses"][0] == "success"


@pytest.mark.asyncio(loop_scope="session")
async def test_perp_order(hl: AsyncHyper):
    coin = "BTC"
    px = 105_001.0
    sz = 0.0001
    order_req = {
        "coin": coin,
        "is_buy": True,
        "sz": sz,
        "px": px,
        "is_market": True,
        "order_type": LimitOrder.ALO.value,
    }

    resp: dict = await hl.place_order(**order_req)
    assert resp["status"] == "ok"
    print(resp)

    oid = resp["response"]["data"]["statuses"][0]["resting"]["oid"]
    assert oid

    resp = await hl.cancel_order(coin, oid)
    assert resp["status"] == "ok"
    assert resp["response"]["data"]["statuses"][0] == "success"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_isolated_margin(hl: AsyncHyper):
    res = await hl.update_leverage(2, "ETH", is_cross=False)
    print("Isolated leverage updated resp:", res)

    value = 10 + 0.3
    price = 2670.0
    size = value / price
    order_req = {
        "coin": "ETH",
        "is_buy": True,
        "sz": round(size, 4),
        "px": price,
        "is_market": False,
        "order_type": LimitOrder.GTC.value,
    }
    res = await hl.place_order(**order_req)


@pytest.mark.asyncio(loop_scope="session")
async def test_batch_place_orders(hl: AsyncHyper):
    coin = "BTC"
    is_buy = True
    sz = 0.001
    px = 105_000
    tp_px = px + 5_000
    sl_px = px - 5_000
    o1 = {
        "coin": coin,
        "is_buy": is_buy,
        "sz": sz,
        "px": px,
        "ro": False,
        "order_type": LimitOrder.ALO.value,
    }
    # Take profit
    tp_order_type = {
        "trigger": {"isMarket": False, "triggerPx": tp_px, "tpsl": "tp"}
    }
    o2 = {
        "coin": coin,
        "is_buy": not is_buy,
        "sz": sz,
        "px": px,
        "ro": True,
        "order_type": tp_order_type,
    }
    # Stop loss
    sl_order_type = {
        "trigger": {"isMarket": False, "triggerPx": sl_px, "tpsl": "sl"}
    }
    o3 = {
        "coin": coin,
        "is_buy": not is_buy,
        "sz": sz,
        "px": px,
        "ro": True,
        "order_type": sl_order_type,
    }

    resp = await hl.batch_place_orders([o1], is_market=True)  # type: ignore
    print("\nBatch place market orders response: ", resp)
    assert resp["status"] == "ok"

    orders = [o2, o3]
    resp = await hl.batch_place_orders(orders, grouping="positionTpsl")  # type: ignore
    print("Batch place orders with 'positionTpsl' response: ", resp)
    assert resp["status"] == "ok"

    resp = await hl.close_all_positions()
    print("Close all positions response: ", resp)
    assert resp["status"] == "ok"

    orders = [o1, o2, o3]
    resp = await hl.batch_place_orders(orders, grouping="normalTpsl")  # type: ignore
    print("Batch place orders with 'normalTpsl' response: ", resp)

    orders = await hl.get_user_open_orders(is_frontend=True)
    cancels = []
    for o in orders:
        coin = o["coin"]
        oid = o["oid"]
        cancels.append((coin, oid))
    resp = await hl.batch_cancel_orders(cancels)
    print("Batch cancel orders response: ", resp)
    assert resp["status"] == "ok"
