from error_ui import ask_yes_no
import DB

def ask_to_notify_management(root):
    return ask_yes_no("Attempt to use emergency supplies. You must notify management about this product. Type 'I will notify management' below to confirm.", root, "I will notify management")

def confirm_emergency_supply_use(root, product_name, req_quantity):
    return ask_to_notify_management(root)

def is_attempt_to_use_emergency_supply(product_name, req_quantity):
    return (DB.total_quantity_available(product_name) - req_quantity) < DB.emergency_count(product_name)

def run_with_emergency_supply_confirmation(root, func, product_name, req_quantity):
    if is_attempt_to_use_emergency_supply(product_name, req_quantity):
        confirmed = confirm_emergency_supply_use(root, product_name, req_quantity)
        if confirmed:
            DB.run_with_disabled_emergency_lock(DB.PATH, func, None, None)
    else:
        func()
