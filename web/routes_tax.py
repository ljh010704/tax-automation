"""Tax calculator routes for the Flask web app."""

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from core.data_manager import DataManager
from core.tax_calculator import TaxCalculator


tax_bp = Blueprint("tax", __name__)


def _dm():
    dm = DataManager()
    dm.set_current_user(current_user.id)
    return dm


def _calc():
    return TaxCalculator()


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
def calculator(entity_id):
    dm = _dm()
    entity = dm.get_entity(entity_id)
    if entity is None:
        flash("Entity not found.", "error")
        return redirect(url_for("tax.dashboard"))

    result = None
    active_tab = request.form.get("tab", "quarterly")

    if request.method == "POST":
        calc_type = request.form.get("calc_type", "quarterly")
        calculator_ = _calc()

        try:
            if calc_type == "quarterly":
                quarterly_income = float(request.form.get("quarterly_income", 0))
                taxpayer_type = request.form.get("taxpayer_type", "small_scale")
                result = calculator_.calculate_all_quarterly(
                    quarterly_income=quarterly_income,
                    taxpayer_type=taxpayer_type,
                )
                active_tab = "quarterly"

            elif calc_type == "stamp":
                quarterly_income = float(request.form.get("quarterly_income", 0))
                paid_capital = float(request.form.get("paid_capital", 0))
                result = calculator_.calculate_stamp_tax(
                    quarterly_income=quarterly_income,
                    paid_capital=paid_capital,
                )
                active_tab = "stamp"

            elif calc_type == "social":
                monthly_base = float(request.form.get("monthly_base", 0))
                result = calculator_.calculate_social_security(
                    monthly_base=monthly_base,
                )
                active_tab = "social"

            elif calc_type == "annual":
                annual_income = float(request.form.get("annual_income", 0))
                annual_expenses = float(request.form.get("annual_expenses", 0))
                quarterly_prepaid = float(request.form.get("quarterly_prepaid", 0))
                result = calculator_.calculate_iit_annual_reconciliation(
                    annual_income=annual_income,
                    annual_expenses=annual_expenses,
                    quarterly_prepaid=quarterly_prepaid,
                )
                active_tab = "annual"

            else:
                flash("Unknown calculation type.", "error")

        except (TypeError, ValueError) as exc:
            flash("Invalid input: " + str(exc), "error")

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
def calculate():
    data = request.get_json(silent=True) or request.form
    calc_type = data.get("calc_type", "quarterly")

    try:
        entity_id = int(data.get("entity_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "entity_id is required and must be an integer."}), 400

    dm = _dm()
    entity = dm.get_entity(entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found."}), 404

    calc = _calc()

    try:
        if calc_type == "quarterly":
            quarterly_income = float(data.get("quarterly_income", 0))
            result = calc.calculate_all_quarterly(
                quarterly_income=quarterly_income,
                quarterly_expenses=0,
            )

        elif calc_type == "stamp":
            quarterly_income = float(data.get("quarterly_income", 0))
            paid_capital = float(data.get("paid_capital", 0))
            result = calc.calculate_stamp_tax(
                quarterly_income=quarterly_income,
                paid_capital=paid_capital,
            )

        elif calc_type == "social":
            monthly_base = float(data.get("monthly_base", 0))
            result = calc.calculate_social_security(
                monthly_base=monthly_base,
            )

        elif calc_type == "annual":
            annual_income = float(data.get("annual_income", 0))
            annual_expenses = float(data.get("annual_expenses", 0))
            quarterly_prepaid = float(data.get("quarterly_prepaid", 0))
            result = calc.calculate_iit_annual_reconciliation(
                annual_income=annual_income,
                annual_expenses=annual_expenses,
                quarterly_prepaid=quarterly_prepaid,
            )

        else:
            return jsonify({"error": "Unknown calc_type: " + str(calc_type)}), 400

    except (TypeError, ValueError) as exc:
        return jsonify({"error": "Invalid parameter: " + str(exc)}), 400

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
def declaration_submit(entity_id):
    dm = _dm()
    entity = dm.get_entity(entity_id)
    if entity is None:
        return jsonify({"error": "Entity not found."}), 404

    data = request.get_json(silent=True) or request.form
    records = data.get("records", [])

    if not records:
        return jsonify({"error": "No records supplied."}), 400

    now = datetime.now()
    saved_ids = []

    for record in records:
        try:
            year = int(record.get("year", now.year))
            quarter = int(record.get("quarter", (now.month - 1) // 3 + 1))
            tax_type = record.get("tax_type", "")
            taxable_income = float(record.get("taxable_income", 0))
            tax_amount = float(record.get("tax_amount", 0))
            tax_rate = float(record.get("tax_rate", 0))
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
            return jsonify({"error": "Invalid record: " + str(exc)}), 400

    return jsonify({
        "entity_id": entity_id,
        "saved_ids": saved_ids,
        "count": len(saved_ids),
    })
