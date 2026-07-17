"""Tax calculator routes for the Flask web app."""

import logging
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from core.data_manager import DataManager
from core.tax_calculator import TaxCalculator
from web.csrf import csrf_required

logger = logging.getLogger(__name__)

tax_bp = Blueprint("tax", __name__)


def _dm():
    dm = DataManager()
    dm.set_current_user(current_user.id)
    return dm


def _calc():
    return TaxCalculator()


def _validate_amount(value, field_name="金额"):
    """Validate a monetary amount: must be finite and non-negative."""
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name}必须是有效数字")
    if val != val or val == float('inf') or val == float('-inf'):  # NaN/Inf check
        raise ValueError(f"{field_name}必须是有限数字")
    if val < 0:
        raise ValueError(f"{field_name}不能为负数")
    return val


def _validate_quarter(quarter):
    """Validate quarter is 1-4."""
    try:
        q = int(quarter)
    except (TypeError, ValueError):
        raise ValueError("季度必须是1-4的整数")
    if q < 1 or q > 4:
        raise ValueError("季度必须在1到4之间")
    return q


# ---------------------------------------------------------------------------
# Route 1 -- Pick entity, show available tax calculations
# ---------------------------------------------------------------------------
@tax_bp.route("/")
@login_required
def dashboard():
    dm = _dm()
    entities = dm.list_entities()
    now = datetime.now()
    return render_template(
        "tax/dashboard.html",
        entities=entities,
        now=now,
    )


# ---------------------------------------------------------------------------
# Route 2 -- Tax calculator page (4 tabs)
# ---------------------------------------------------------------------------
@tax_bp.route("/calculator/<int:entity_id>", methods=["GET", "POST"])
@login_required
@csrf_required
def calculator(entity_id):
    dm = _dm()
    entity = dm.get_entity(entity_id)
    if entity is None:
        flash("企业不存在或无权限访问", "error")
        return redirect(url_for("tax.dashboard"))

    result = None
    active_tab = request.form.get("tab", "quarterly")

    if request.method == "POST":
        calc_type = request.form.get("calc_type", "quarterly")
        calculator_ = _calc()

        try:
            if calc_type == "quarterly":
                quarterly_income = _validate_amount(request.form.get("quarterly_income", 0), "季度收入")
                quarterly_expenses = _validate_amount(request.form.get("quarterly_expenses", 0), "季度费用")
                result = calculator_.calculate_all_quarterly(
                    quarterly_income=quarterly_income,
                    quarterly_expenses=quarterly_expenses,
                )
                active_tab = "quarterly"

            elif calc_type == "stamp":
                quarterly_income = _validate_amount(request.form.get("quarterly_income", 0), "季度收入")
                paid_capital = _validate_amount(request.form.get("paid_capital", 0), "实收资本")
                result = calculator_.calculate_stamp_tax(
                    quarterly_income=quarterly_income,
                    paid_capital=paid_capital,
                )
                active_tab = "stamp"

            elif calc_type == "social":
                monthly_base = _validate_amount(request.form.get("monthly_base", 0), "月缴费基数")
                result = calculator_.calculate_social_security(
                    monthly_base=monthly_base,
                )
                active_tab = "social"

            elif calc_type == "annual":
                annual_income = _validate_amount(request.form.get("annual_income", 0), "年度收入")
                annual_expenses = _validate_amount(request.form.get("annual_expenses", 0), "年度费用")
                quarterly_prepaid = _validate_amount(request.form.get("quarterly_prepaid", 0), "季度预缴")
                result = calculator_.calculate_iit_annual_reconciliation(
                    annual_income=annual_income,
                    annual_expenses=annual_expenses,
                    quarterly_prepaid=quarterly_prepaid,
                )
                active_tab = "annual"

            else:
                flash("未知的计算类型", "error")

        except (TypeError, ValueError) as exc:
            flash("输入错误: " + str(exc), "error")

    return render_template(
        "tax/calculator.html",
        entity=entity,
        result=result,
        active_tab=active_tab,
    )


# ---------------------------------------------------------------------------
# Route 3 -- JSON API endpoint used by the calculator tabs
# ---------------------------------------------------------------------------
@tax_bp.route("/calculate", methods=["POST"])
@login_required
@csrf_required
def calculate():
    data = request.get_json(silent=True) or request.form
    calc_type = data.get("calc_type", "quarterly")

    try:
        entity_id = int(data.get("entity_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "entity_id为必填项且必须是整数"}), 400

    dm = _dm()
    entity = dm.get_entity(entity_id)
    if entity is None:
        return jsonify({"error": "企业不存在或无权限访问"}), 404

    calc = _calc()

    try:
        if calc_type == "quarterly":
            quarterly_income = _validate_amount(data.get("quarterly_income", 0), "季度收入")
            quarterly_expenses = _validate_amount(data.get("quarterly_expenses", 0), "季度费用")
            result = calc.calculate_all_quarterly(
                quarterly_income=quarterly_income,
                quarterly_expenses=quarterly_expenses,
            )

        elif calc_type == "stamp":
            quarterly_income = _validate_amount(data.get("quarterly_income", 0), "季度收入")
            paid_capital = _validate_amount(data.get("paid_capital", 0), "实收资本")
            result = calc.calculate_stamp_tax(
                quarterly_income=quarterly_income,
                paid_capital=paid_capital,
            )

        elif calc_type == "social":
            monthly_base = _validate_amount(data.get("monthly_base", 0), "月缴费基数")
            result = calc.calculate_social_security(
                monthly_base=monthly_base,
            )

        elif calc_type == "annual":
            annual_income = _validate_amount(data.get("annual_income", 0), "年度收入")
            annual_expenses = _validate_amount(data.get("annual_expenses", 0), "年度费用")
            quarterly_prepaid = _validate_amount(data.get("quarterly_prepaid", 0), "季度预缴")
            result = calc.calculate_iit_annual_reconciliation(
                annual_income=annual_income,
                annual_expenses=annual_expenses,
                quarterly_prepaid=quarterly_prepaid,
            )

        else:
            return jsonify({"error": "未知的计算类型: " + str(calc_type)}), 400

    except (TypeError, ValueError) as exc:
        return jsonify({"error": "参数错误: " + str(exc)}), 400

    return jsonify({
        "entity_id": entity_id,
        "calc_type": calc_type,
        "result": result,
    })


# ---------------------------------------------------------------------------
# Route 4 -- Declaration status & tax records
# ---------------------------------------------------------------------------
@tax_bp.route("/declaration/")
@login_required
def declaration_page():
    dm = _dm()
    entities = dm.list_entities()

    records_by_entity = {}
    now = datetime.now()
    for entity in entities:
        records_by_entity[entity["id"]] = dm.get_tax_records(entity["id"], year=now.year)

    return render_template(
        "tax/declaration.html",
        entities=entities,
        records_by_entity=records_by_entity,
        now=now,
    )


# ---------------------------------------------------------------------------
# Route 5 -- Save tax records for an entity
# ---------------------------------------------------------------------------
@tax_bp.route("/declaration/<int:entity_id>/submit", methods=["POST"])
@login_required
@csrf_required
def declaration_submit(entity_id):
    dm = _dm()
    entity = dm.get_entity(entity_id)
    if entity is None:
        return jsonify({"error": "企业不存在或无权限访问"}), 404

    data = request.get_json(silent=True) or request.form
    records = data.get("records", [])

    if not records:
        return jsonify({"error": "未提供记录"}), 400

    now = datetime.now()
    saved_ids = []

    for record in records:
        try:
            year = int(record.get("year", now.year))
            quarter = _validate_quarter(record.get("quarter", (now.month - 1) // 3 + 1))
            tax_type = record.get("tax_type", "")
            taxable_income = _validate_amount(record.get("taxable_income", 0), "应税收入")
            tax_amount = _validate_amount(record.get("tax_amount", 0), "税额")
            tax_rate = _validate_amount(record.get("tax_rate", 0), "税率")
            notes = record.get("notes", "")

            record_id = dm.save_tax_record(
                entity_id=entity_id,
                year=year,
                quarter=quarter,
                tax_type=tax_type,
                taxable_income=taxable_income,
                tax_amount=tax_amount,
                tax_rate=tax_rate,
                notes=notes,
            )
            saved_ids.append(record_id)

        except (TypeError, ValueError) as exc:
            return jsonify({"error": "记录参数错误: " + str(exc)}), 400
        except PermissionError as exc:
            return jsonify({"error": str(exc)}), 403

    return jsonify({
        "entity_id": entity_id,
        "saved_ids": saved_ids,
        "count": len(saved_ids),
    })
