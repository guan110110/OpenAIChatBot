"""
Business Action Tools & Mock Database Operations.
业务动作工具集（订单查询、退换货申请、修改收货地址）。
"""

import os
import json
from typing import Dict, Any, Optional


class OrderService:
    """模拟业务数据库服务"""
    def __init__(self, db_file_path: Optional[str] = None):
        if not db_file_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_file_path = os.path.join(base_dir, "data", "mock_orders.json")

        self.db_file_path = db_file_path
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.db_file_path):
            with open(self.db_file_path, "r", encoding="utf-8") as f:
                self.orders: Dict[str, Any] = json.load(f)
        else:
            self.orders = {}

    def query_order(self, order_id: str) -> str:
        order = self.orders.get(order_id.strip().upper())
        if not order:
            return f"❌ 未查到订单号为【{order_id}】的记录。请核对订单号是否正确（例如 ORD1001、ORD1002、ORD1003）。"

        return (
            f"📦 订单详情：\n"
            f"• 订单编号: {order['order_id']}\n"
            f"• 商品名称: {order['product_name']}\n"
            f"• 订单金额: ¥{order['amount']:.2f}\n"
            f"• 订单状态: 【{order['status']}】\n"
            f"• 承运物流: {order['express_company']} ({order['tracking_number']})\n"
            f"• 当前轨迹: {order['current_location']}\n"
            f"• 收货地址: {order['address']}"
        )

    def apply_refund(self, order_id: str, reason: str = "协商退款") -> str:
        order = self.orders.get(order_id.strip().upper())
        if not order:
            return f"❌ 无法办理退款：未查到订单【{order_id}】。"

        if order['status'] == "已签收":
            return (
                f"✅ 您的退款申请已受理！\n"
                f"• 订单【{order_id}】({order['product_name']}) 处于已签收状态，已为您生成退货寄件单号。\n"
                f"• 退款原因: {reason}\n"
                f"• 寄回地址: 广东省东莞市售后服务中心1号仓 (运费险已自动垫付)，仓库验货无误后款项将在 24 小时内原路退回。"
            )
        elif order['status'] == "待发货":
            order['status'] = "已取消退款中"
            return f"✅ 拦截成功！订单【{order_id}】尚未发出，已为您立即办理全额退款 ¥{order['amount']:.2f}，款项预计将在 1-3 小时内到账。"
        else:
            return f"⚠️ 订单【{order_id}】当前处于【{order['status']}】运输途中，建议您收到包裹后选择拒签或申请 7 天无理由退货。"

    def update_shipping_address(self, order_id: str, new_address: str) -> str:
        order = self.orders.get(order_id.strip().upper())
        if not order:
            return f"❌ 未查到订单【{order_id}】。"

        if order['status'] == "待发货":
            old_addr = order['address']
            order['address'] = new_address
            return f"✅ 地址修改成功！订单【{order_id}】尚未发出，原地址已更新为：【{new_address}】。"
        else:
            return f"⚠️ 修改失败：订单【{order_id}】已经进入【{order['status']}】阶段，包裹已发往原地址，如需转寄请联系顺丰/京东快递客服办理重定向。"


# 工具定义与 OpenAPI JSON Schema
ORDER_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "查询订单的详细状态、商品名称与最新物流轨迹信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号，例如 ORD1001, ORD1002"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_refund",
            "description": "为指定订单申请退货退款或取消未发货订单",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号，例如 ORD1001"},
                    "reason": {"type": "string", "description": "退款原因"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_shipping_address",
            "description": "修改未发货订单的收货地址",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号"},
                    "new_address": {"type": "string", "description": "新的收件人详细地址"}
                },
                "required": ["order_id", "new_address"]
            }
        }
    }
]
