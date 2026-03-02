from typing import Optional


VALID_ROLES = {"owner", "manager", "staff"}

ROLE_PERMISSIONS = {
    "owner": {
        "sale:create",
        "expense:create",
        "inventory:view",
        "inventory:update",
        "customer:view",
        "customer:update",
        "report:view",
        "analytics:view",
        "member:view",
        "member:manage",
        "activity:view",
    },
    "manager": {
        "sale:create",
        "expense:create",
        "inventory:view",
        "inventory:update",
        "customer:view",
        "customer:update",
        "report:view",
        "analytics:view",
        "member:view",
        "activity:view",
    },
    "staff": {
        "sale:create",
    },
}


ACTION_MAP = {
    "/sale": "sale:create",
    "💰 Record Sale": "sale:create",
    "/expense": "expense:create",
    "💸 Record Expense": "expense:create",
    "/expenses_today": "report:view",
    "/today": "report:view",
    "📊 Today's Report": "report:view",
    "/report": "report:view",
    "/weekly": "report:view",
    "/monthly": "report:view",
    "/profit": "report:view",
    "/custom_report": "report:view",
    "/insights": "analytics:view",
    "🚀 Insights": "analytics:view",
    "/products": "inventory:view",
    "/stock": "inventory:view",
    "📦 Inventory": "inventory:view",
    "/add_product": "inventory:update",
    "/add_stock": "inventory:update",
    "/customers": "customer:view",
    "/credits": "customer:view",
    "👥 Customers": "customer:view",
    "/add_customer": "customer:update",
    "/credit": "customer:update",
    "/team": "member:view",
    "🧑‍💼 Team": "member:view",
    "/invite": "member:manage",
    "/set_role": "member:manage",
    "/remove_member": "member:manage",
    "/activity": "activity:view",
}


def resolve_action_from_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    stripped = text.strip()
    if stripped in ACTION_MAP:
        return ACTION_MAP[stripped]

    if stripped.startswith("/"):
        command = stripped.split()[0]
        if "@" in command:
            command = command.split("@", 1)[0]
        return ACTION_MAP.get(command)

    return None


def has_permission(role: str, action: Optional[str]) -> bool:
    if not action:
        return True
    return action in ROLE_PERMISSIONS.get(role, set())


def action_label(action: Optional[str]) -> str:
    if not action:
        return "this action"
    return action.replace(":", " ")
