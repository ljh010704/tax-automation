"""Bookkeeping routes for tax automation web app."""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from core.data_manager import DataManager


bookkeeping_bp = Blueprint("bookkeeping", __name__)


def _create_dm():
    dm = DataManager()
    dm.set_current_user(current_user.id)
    return dm


@bookkeeping_bp.route("/")
@login_required
def index():
    dm = _create_dm()
    entities = dm.get_entities()
    return render_template("bookkeeping/index.html", entities=entities)


@bookkeeping_bp.route("/<int:entity_id>", methods=["GET", "POST"])
@login_required
def entity_transactions(entity_id):
    dm = _create_dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("Entity not found.", "error")
        return redirect(url_for("bookkeeping.index"))

    if request.method == "POST":
        trans_date_raw = request.form.get("trans_date", "").strip()
        trans_type = request.form.get("trans_type", "").strip()
        category = request.form.get("category", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()

        if not trans_date_raw:
            flash("Transaction date is required.", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        if trans_type not in ("income", "expense"):
            flash("Transaction type must be income or expense.", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        if not category:
            flash("Category is required.", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            flash("Amount must be a valid number.", "error")
            return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

        dm.add_transaction(
            entity_id,
            trans_date_raw,
            trans_type,
            category,
            amount,
            description,
        )
        flash("Transaction added successfully.", "success")
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
def add_transaction(entity_id):
    dm = _create_dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("Entity not found.", "error")
        return redirect(url_for("bookkeeping.index"))

    trans_date_raw = request.form.get("trans_date", "").strip()
    trans_type = request.form.get("trans_type", "").strip()
    category = request.form.get("category", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()

    if not trans_date_raw:
        flash("Transaction date is required.", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    if trans_type not in ("income", "expense"):
        flash("Transaction type must be income or expense.", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    if not category:
        flash("Category is required.", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    try:
        amount = float(amount_raw)
    except (TypeError, ValueError):
        flash("Amount must be a valid number.", "error")
        return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))

    dm.add_transaction(
        entity_id,
        trans_date_raw,
        trans_type,
        category,
        amount,
        description,
    )
    flash("Transaction added successfully.", "success")
    return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))


@bookkeeping_bp.route("/<int:entity_id>/delete/<int:trans_id>", methods=["POST"])
@login_required
def delete_transaction(entity_id, trans_id):
    dm = _create_dm()
    dm.delete_transaction(trans_id)
    flash("Transaction deleted.", "success")
    return redirect(url_for("bookkeeping.entity_transactions", entity_id=entity_id))


@bookkeeping_bp.route("/reports/<int:entity_id>")
@login_required
def reports(entity_id):
    dm = _create_dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("Entity not found.", "error")
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
