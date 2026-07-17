"""Bookkeeping routes for tax automation web app."""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from core.data_manager import DataManager
from web.csrf import csrf_required

logger = logging.getLogger(__name__)

bookkeeping_bp = Blueprint("bookkeeping", __name__)


def _create_dm():
    dm = DataManager()
    dm.set_current_user(current_user.id)
    return dm


def _validate_amount(value, field_name="金额"):
    """Validate a monetary amount."""
    try:
        val = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name}必须是有效数字")
    if val != val or val == float('inf') or val == float('-inf'):
        raise ValueError(f"{field_name}必须是有限数字")
    if val < 0:
        raise ValueError(f"{field_name}不能为负数")
    return val


@bookkeeping_bp.route("/")
@login_required
def index():
    dm = _create_dm()
    entities = dm.get_entities()
    return render_template("bookkeeping/index.html", entities=entities)


@bookkeeping_bp.route("/<int:entity_id>", methods=["GET", "POST"])
@login_required
@csrf_required
def entity_transactions(entity_id):
    dm = _create_dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("企业不存在或无权限访问", "error")
        return redirect(url_for("bookkeeping.index"))

    if request.method == "POST":
        trans_date_raw = request.form.get("trans_date", "").strip()
        trans_type = request.form.get("trans_type", "").strip()
        category = request.form.get("category", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()

        if not trans_date_raw:
            flash("交易日期不能为空", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        if trans_type not in ("income", "expense"):
            flash("交易类型必须是收入或支出", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        if not category:
            flash("分类不能为空", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        try:
            amount = _validate_amount(amount_raw)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        dm.add_transaction(
            entity_id,
            trans_date_raw,
            trans_type,
            category,
            amount,
            description,
        )
        flash("交易添加成功", "success")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    transactions = dm.get_transactions(entity_id, year=year, month=month)
    monthly_summary = dm.get_monthly_summary(entity_id, year, month)

    quarter = (month - 1) // 3 + 1
    quarterly_summary = dm.get_quarterly_summary(entity_id, year, quarter)

    return render_template(
        "bookkeeping/entity_transactions.html",
        entity=entity,
        transactions=transactions,
        year=year,
        month=month,
        quarter=quarter,
        monthly_summary=monthly_summary,
        quarterly_summary=quarterly_summary,
    )


@bookkeeping_bp.route("/<int:entity_id>/add", methods=["POST"])
@login_required
@csrf_required
def add_transaction(entity_id):
    dm = _create_dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("企业不存在或无权限访问", "error")
        return redirect(url_for("bookkeeping.index"))

    trans_date_raw = request.form.get("trans_date", "").strip()
    trans_type = request.form.get("trans_type", "").strip()
    category = request.form.get("category", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()

    if not trans_date_raw:
        flash("交易日期不能为空", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    if trans_type not in ("income", "expense"):
        flash("交易类型必须是收入或支出", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    if not category:
        flash("分类不能为空", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    try:
        amount = _validate_amount(amount_raw)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    dm.add_transaction(
        entity_id,
        trans_date_raw,
        trans_type,
        category,
        amount,
        description,
    )
    flash("交易添加成功", "success")
    return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))


@bookkeeping_bp.route("/<int:entity_id>/delete/<int:trans_id>", methods=["POST"])
@login_required
@csrf_required
def delete_transaction(entity_id, trans_id):
    dm = _create_dm()
    try:
        dm.delete_transaction(trans_id)
        flash("交易已删除", "success")
    except PermissionError as e:
        flash(str(e), "error")
    return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))


@bookkeeping_bp.route("/reports/<int:entity_id>")
@login_required
def reports(entity_id):
    dm = _create_dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("企业不存在或无权限访问", "error")
        return redirect(url_for("bookkeeping.index"))

    year = request.args.get("year", type=int)
    if not year:
        year = datetime.now().year

    monthly_breakdown = {}
    for m in range(1, 13):
        monthly_breakdown[m] = dm.get_monthly_summary(entity_id, year, m)

    total_income = 0.0
    total_expenses = 0.0
    for m in monthly_breakdown:
        total_income += monthly_breakdown[m]["total_income"]
        total_expenses += monthly_breakdown[m]["total_expense"]

    return render_template(
        "bookkeeping/reports.html",
        entity=entity,
        year=year,
        monthly_breakdown=monthly_breakdown,
        total_income=total_income,
        total_expenses=total_expenses,
        profit=total_income - total_expenses,
    )
