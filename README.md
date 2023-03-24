# Trading System

WIP (last updated: 22 Mar 2023)

This repository provides a basic event-driven trading system for trading on Luno. It can be adapted for other exchanges by adding similar brokerage code structure in the `brokerage` folder or use an existing library like `ccxt`. A wrapper will still be needed to handle events generation and consumption.

Order and fill management are all tested. You need to provide your API key in the `.env` file, and start writing a strategy in the `strategies` folder, and define the strategy's configuration settings in the `global_strategy_config.yaml`.

Use at your own risk.

---

# Architecture

## Initialization

The trading system sets up 2 queues:

- incoming market data (tick event),
- trading-related actions (order, fill, check_order_status events).

Before the system starts running, it does the following in sequence:

- set up 2 multi-threaded queues
- find the strategies files (see strategies logic below)
- set up brokerage trade client
- set up various managers required for trading (OMS, strategies, market data)
- `run()` to start streaming data and trading

## Market data streaming logic

- Data is streamed by default at 1 tick per second. we also call it "heartbeat". This is set according to rate limits defined in certain exchange (i.e. Kraken public API). This can be changed at the `TradingSystem` class.
- Data is passed into the market data queue.

## Order management system (OMS)

- Note that each `order_manager` is local and unique to each strategy. If there are 5 strategies, there will be 5 local order managers, each managing orders for its strategy. The same applies for `position_managers`
- all orders are placed directly through strategy file to strategy manager (via StrategyBase). It creates an order event and adds to the queue
- when an order event is received, it is passed into the strategy manager and subsequently the strategy class. It is then added into the order manager list of open orders.
- every tick, the system pushes a `check_order_status` event to the queue to check whether all open orders has been filled.
- if the order has been filled, it creates a fill event and addes to the queue.
- this fill event received is logged as a trade, and gets passed into the strategy manager to update the position **within** each strategy object. The open order is also removed from the list.

## Strategies Logic

- all strategies are defined in `configs/global_strategy_config.yaml`
- each strategy inherits functions from `strategy_base.py` and is managed by `strategy_manager.py`.
- each strategy must be named with suffix `_strategy.py`.
- each strategy comes with a local position manager and order manager. This position manager keeps track of the positions, PnL, and capital of this specific strategy. The order manager keeps track of cancelled and standing orders.

## Risk management logic (WIP)

- This is still wip but every order placed or cancelled, it should be checked whether it complies with our global portfolio and individual strategy risk settings.
- It should perform basic sanity check on each of our orders and our positions before placing them.

## To-do

- execution classes
  - change order execution to asynchronous functions
- live performance metrics
- risk manager
- performance profiling
- GUI
- add tests

# Test

- use `naive_test_strategy.py` to test order execution placement
