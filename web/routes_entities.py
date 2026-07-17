"""企业管理模块"""

import logging
import threading
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from core.data_manager import DataManager
from core.tax_calculator import TaxCalculator
from core.business_query import BusinessQueryOffline
from web.csrf import csrf_required

logger = logging.getLogger(__name__)

entities_bp = Blueprint("entities", __name__)


def _dm():
    dm = DataManager()
    dm.set_current_user(current_user.id)
    return dm


@entities_bp.route("/")
@login_required
def list_entities():
    dm = _dm()
    entities = dm.list_entities()
    return render_template("entities/list.html", entities=entities)


@entities_bp.route("/api/lookup", methods=["POST"])
@login_required
@csrf_required
def api_lookup():
    """通过统一社会信用代码查询企业信息"""
    data = request.get_json() or {}
    credit_code = (data.get("credit_code", "") or "").strip().upper()

    if not BusinessQueryOffline.validate_credit_code(credit_code):
        return jsonify({"error": "统一社会信用代码格式不正确，应为18位数字大写字母"}), 400

    try:
        from core.business_query import query_business_info_sync
    except ImportError:
        return jsonify({"error": "服务器未安装 playwright，无法自动查询。请手动填写企业信息。", "playwright_missing": True}), 503

    try:
        result = query_business_info_sync(credit_code)
        if result:
            return jsonify({"success": True, "data": result})
        return jsonify({"error": "未查询到企业信息，请检查信用代码是否正确"}), 404
    except Exception as e:
        logger.error("查询企业信息失败: %s", str(e))
        return jsonify({"error": "查询失败，请稍后重试"}), 500


@entities_bp.route("/add", methods=["GET", "POST"])
@login_required
@csrf_required
def add_entity():
    if request.method == "POST":
        credit_code = request.form.get("credit_code", "").strip().upper()
        if not BusinessQueryOffline.validate_credit_code(credit_code):
            flash("统一社会信用代码格式不正确", "error")
            return redirect(url_for("entities.add_entity"))

        entity = {
            "name": request.form.get("name", "").strip(),
            "credit_code": credit_code,
            "entity_type": request.form.get("entity_type", "个体工商户"),
            "taxpayer_type": request.form.get("taxpayer_type", "small_scale"),
            "legal_representative": request.form.get("legal_representative", "").strip(),
            "business_status": request.form.get("business_status", "正常"),
            "taxpayer_status": request.form.get("taxpayer_status", "正常"),
            "province": request.form.get("province", "").strip(),
            "city": request.form.get("city", "").strip(),
            "tax_authority": request.form.get("tax_authority", "").strip(),
            "login_url": request.form.get("login_url", "").strip(),
        }
        if not entity["name"]:
            flash("企业名称不能为空", "error")
            return redirect(url_for("entities.add_entity"))

        try:
            dm = _dm()
            dm.add_entity(entity)
            flash("企业信息添加成功", "success")
            return redirect(url_for("entities.list_entities"))
        except Exception as e:
            logger.error("添加企业失败: %s", str(e))
            if "UNIQUE" in str(e):
                flash("企业已存在", "error")
            else:
                flash("添加失败，请稍后重试", "error")
            return redirect(url_for("entities.add_entity"))

    return render_template("entities/add.html")


@entities_bp.route("/<int:entity_id>/edit", methods=["GET", "POST"])
@login_required
@csrf_required
def edit_entity(entity_id):
    dm = _dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        flash("企业不存在", "error")
        return redirect(url_for("entities.list_entities"))

    if request.method == "POST":
        updates = {
            "name": request.form.get("name", "").strip(),
            "entity_type": request.form.get("entity_type", ""),
            "taxpayer_type": request.form.get("taxpayer_type", ""),
            "legal_representative": request.form.get("legal_representative", "").strip(),
            "business_status": request.form.get("business_status", ""),
            "taxpayer_status": request.form.get("taxpayer_status", ""),
            "province": request.form.get("province", "").strip(),
            "city": request.form.get("city", "").strip(),
            "tax_authority": request.form.get("tax_authority", "").strip(),
            "login_url": request.form.get("login_url", "").strip(),
        }
        dm.update_entity(entity_id, updates)
        flash("更新成功", "success")
        return redirect(url_for("entities.list_entities"))

    return render_template("entities/edit.html", entity=entity)


@entities_bp.route("/<int:entity_id>/delete", methods=["POST"])
@login_required
@csrf_required
def delete_entity(entity_id):
    dm = _dm()
    dm.delete_entity(entity_id)
    flash("已删除", "success")
    return redirect(url_for("entities.list_entities"))


@entities_bp.route("/<int:entity_id>/query", methods=["POST"])
@login_required
@csrf_required
def query_entity(entity_id):
    try:
        from core.business_query import query_business_info_sync
    except ImportError:
        return jsonify({"error": "服务器未安装 playwright，无法自动查询。请手动填写企业信息。", "playwright_missing": True}), 503

    dm = _dm()
    entity = dm.get_entity(entity_id)
    if not entity:
        return jsonify({"error": "企业不存在"}), 404

    credit_code = entity["credit_code"]
    if not BusinessQueryOffline.validate_credit_code(credit_code):
        return jsonify({"error": "统一社会信用代码格式不正确"}), 400

    try:
        result = query_business_info_sync(credit_code)
        if result:
            dm.update_entity(entity_id, result)
            return jsonify({"success": True, "data": result})
        return jsonify({"error": "查询企业信息失败请稍后重试"}), 500
    except Exception as e:
        logger.error("查询企业信息失败: %s", str(e))
        return jsonify({"error": "查询失败，请稍后重试"}), 500
