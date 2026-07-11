"""?? / ??"""

from datetime import datetime
from flask import Blueprint, render_template, g
from flask_login import login_required, current_user
from core.data_manager import DataManager

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@login_required
def dashboard():
    dm = DataManager()
    dm.set_current_user(current_user.id)
    entities = dm.list_entities()
    now = datetime.now()

    compliance_items = []
    month = now.month
    year = now.year

    compliance_items.append({"period": "??", "item": "?????1-15??", "due": month in [1,2,3,4,5,6,7,8,9,10,11,12]})
    compliance_items.append({"period": "??", "item": "???????1-15??", "due": month in [1,2,3,4,5,6,7,8,9,10,11,12]})

    if month in [1, 4, 7, 10]:
        compliance_items.append({"period": "??", "item": "??????1-15??", "due": True})
        compliance_items.append({"period": "??", "item": "??????1-15??", "due": True})
        compliance_items.append({"period": "??", "item": "?????????1-15??", "due": True})
        compliance_items.append({"period": "??", "item": "??????1-15??", "due": True})
    else:
        compliance_items.append({"period": "??", "item": "???/???/???????? 1-15 ??", "due": False})
        compliance_items.append({"period": "??", "item": "????????? 1-15 ??", "due": False})

    if month == 1:
        compliance_items.append({"period": "??", "item": "???????????1-31??", "due": True})
    else:
        compliance_items.append({"period": "??", "item": "???????1??", "due": False})

    if month in [1,2,3]:
        compliance_items.append({"period": "??", "item": "?????1-6??", "due": True})
    else:
        compliance_items.append({"period": "??", "item": "?????1-6??", "due": False})

    return render_template("dashboard.html",
        entities=entities,
        now=now,
        compliance_items=compliance_items,
    )
