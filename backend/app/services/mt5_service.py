import socket
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MT5Service:
    def __init__(self, instance_id: str, host: str = "localhost"):
        self.instance_id = instance_id
        self.host = host
        self._port = 18812
        self._mt5 = None
        self._container_port = None

    def _get_container_port(self):
        if self._container_port:
            return self._container_port

        try:
            import docker

            client = docker.from_env()
            container = client.containers.get(self.instance_id)
            ports = container.ports.get("18812/tcp")
            if ports:
                self._container_port = int(ports[0]["HostPort"])
                return self._container_port
        except Exception as e:
            logger.error(f"Error getting container port: {e}")

        return self._port

    def _check_server(self, timeout: int = 5) -> bool:
        port = self._get_container_port()
        try:
            sock = socket.create_connection((self.host, port), timeout=timeout)
            sock.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def _connect(self):
        if self._mt5 is None:
            if not self._check_server():
                raise ConnectionError(
                    f"MT5 server unreachable at {self.host}:{self._get_container_port()}"
                )

            try:
                from mt5linux import MetaTrader5

                self._mt5 = MetaTrader5(host=self.host, port=self._get_container_port())
                if not self._mt5.initialize():
                    raise ConnectionError(
                        f"MT5 initialize failed: {self._mt5.last_error()}"
                    )
                logger.info(
                    f"Connected to MT5 at {self.host}:{self._get_container_port()}"
                )
            except ImportError:
                raise ImportError("mt5linux not installed")
            except Exception as e:
                raise ConnectionError(f"MT5 connection error: {e}")

        return self._mt5

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        try:
            mt5 = self._connect()
            info = mt5.account_info()
            if info:
                return {
                    "login": info.login,
                    "balance": float(info.balance),
                    "equity": float(info.equity),
                    "margin": float(info.margin),
                    "free_margin": float(info.margin_free),
                    "margin_level": float(info.margin_level)
                    if info.margin_level
                    else 0,
                    "currency": info.currency,
                    "leverage": info.leverage,
                    "server": info.server,
                    "name": info.name,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            mt5 = self._connect()
            positions = (
                mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            )
            if not positions:
                return []

            return [
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": float(pos.volume),
                    "open_price": float(pos.price_open),
                    "current_price": float(pos.price_current),
                    "sl": float(pos.sl) if pos.sl else None,
                    "tp": float(pos.tp) if pos.tp else None,
                    "profit": float(pos.profit),
                    "swap": float(pos.swap),
                    "commission": float(pos.commission),
                    "comment": pos.comment,
                    "time": datetime.fromtimestamp(pos.time).isoformat(),
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        magic: int = 234000,
        comment: str = "mt5-router",
    ) -> Optional[Dict[str, Any]]:
        try:
            mt5 = self._connect()

            if price is None:
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    return None
                price = tick.ask if order_type.upper() == "BUY" else tick.bid

            type_map = {
                "BUY": mt5.ORDER_TYPE_BUY,
                "SELL": mt5.ORDER_TYPE_SELL,
                "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
                "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
                "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
                "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
            }

            is_pending = order_type.upper() in [
                "BUY_LIMIT",
                "SELL_LIMIT",
                "BUY_STOP",
                "SELL_STOP",
            ]
            action = mt5.TRADE_ACTION_PENDING if is_pending else mt5.TRADE_ACTION_DEAL

            request = {
                "action": action,
                "symbol": symbol,
                "volume": float(volume),
                "type": type_map.get(order_type.upper(), mt5.ORDER_TYPE_BUY),
                "price": float(price),
                "deviation": 20,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

            if sl is not None:
                request["sl"] = float(sl)
            if tp is not None:
                request["tp"] = float(tp)

            result = mt5.order_send(request)

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    "ticket": result.order,
                    "symbol": symbol,
                    "order_type": order_type,
                    "volume": volume,
                    "price": float(price),
                    "sl": sl,
                    "tp": tp,
                    "status": "filled",
                }

            logger.error(f"Order failed: {result.comment if result else 'No result'}")
            return None
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    def close_position(self, ticket: int) -> bool:
        try:
            mt5 = self._connect()
            positions = mt5.positions_get()
            if not positions:
                return False

            pos = next((p for p in positions if p.ticket == ticket), None)
            if not pos:
                return False

            tick = mt5.symbol_info_tick(pos.symbol)
            if not tick:
                return False

            close_type = (
                mt5.ORDER_TYPE_SELL
                if pos.type == mt5.ORDER_TYPE_BUY
                else mt5.ORDER_TYPE_BUY
            )
            price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": float(pos.volume),
                "type": close_type,
                "position": ticket,
                "price": float(price),
                "deviation": 20,
                "magic": 234000,
                "comment": "mt5-router-close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

            result = mt5.order_send(request)
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def cancel_pending_order(self, ticket: int) -> bool:
        try:
            mt5 = self._connect()
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
                "comment": "mt5-router-cancel",
            }
            result = mt5.order_send(request)
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            mt5 = self._connect()
            orders = mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get()
            if not orders:
                return []

            type_map = {2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP"}

            return [
                {
                    "ticket": order.ticket,
                    "symbol": order.symbol,
                    "type": type_map.get(order.type, "UNKNOWN"),
                    "volume": float(order.volume_initial),
                    "price": float(order.price_open),
                    "sl": float(order.sl) if order.sl else None,
                    "tp": float(order.tp) if order.tp else None,
                    "magic": order.magic,
                    "comment": order.comment,
                    "time_setup": datetime.fromtimestamp(order.time_setup).isoformat(),
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            mt5 = self._connect()
            info = mt5.symbol_info(symbol)
            if info:
                return {
                    "name": info.name,
                    "point": info.point,
                    "digits": info.digits,
                    "spread": info.spread,
                    "bid": float(info.bid) if info.bid else None,
                    "ask": float(info.ask) if info.ask else None,
                    "volume_min": float(info.volume_min),
                    "volume_max": float(info.volume_max),
                    "volume_step": float(info.volume_step),
                    "trade_allowed": info.trade_allowed,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def get_history_deals(
        self, symbol: Optional[str] = None, days: int = 30
    ) -> List[Dict[str, Any]]:
        try:
            mt5 = self._connect()
            end = datetime.now()
            start = end - timedelta(days=days)

            if symbol:
                deals = mt5.history_deals_get(symbol, start, end)
            else:
                deals = mt5.history_deals_get(start, end)

            if not deals:
                return []

            return [
                {
                    "ticket": deal.ticket,
                    "order": deal.order,
                    "symbol": deal.symbol,
                    "type": "BUY" if deal.type == 0 else "SELL",
                    "volume": float(deal.volume),
                    "price": float(deal.price),
                    "profit": float(deal.profit),
                    "commission": float(deal.commission),
                    "swap": float(deal.swap),
                    "time": datetime.fromtimestamp(deal.time).isoformat(),
                    "comment": deal.comment,
                }
                for deal in deals
            ]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []
