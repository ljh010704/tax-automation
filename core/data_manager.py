"""数据管理模块

统一管理企业、记账、税务数据，支持多用户隔离
设置当前用户 (user_id)

"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict


class DataManager:
    """数据管理器 - 初始化数据库 - 创建表结构"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "entities.db")
        self.db_path = db_path
        self._current_user_id = None
        self._init_db()

    def set_current_user(self, user_id: int):
        """设置当前用户 ID用于数据隔离"""
        self._current_user_id = user_id

    def _init_db(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                credit_code TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                taxpayer_type TEXT DEFAULT 'small_scale',
                legal_representative TEXT,
                business_status TEXT DEFAULT '正常',
                taxpayer_status TEXT DEFAULT '正常',
                province TEXT,
                city TEXT,
                tax_authority TEXT,
                login_url TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 添加 user_id 列用于多用户隔离
        try:
            cursor.execute("ALTER TABLE entities ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass

        # 添加企业状态列（如果不存在）
        try:
            cursor.execute("ALTER TABLE entities ADD COLUMN legal_representative TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE entities ADD COLUMN business_status TEXT DEFAULT '正常'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE entities ADD COLUMN taxpayer_status TEXT DEFAULT '正常'")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income_records (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                quarter INTEGER NOT NULL,
                income REAL DEFAULT 0,
                expenses REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_records (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                quarter INTEGER NOT NULL,
                tax_type TEXT NOT NULL,
                taxable_income REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                tax_rate REAL DEFAULT 0,
                is_submitted BOOLEAN DEFAULT 0,
                submitted_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                entity_id INTEGER NOT NULL,
                trans_date DATE NOT NULL,
                trans_type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
        """)

        conn.commit()
        conn.close()

    def _next_id(self, table_name: str) -> int:
        """获取下一个 ID（MAX(id)+1，如果没有则返回 1）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table_name}")
        next_id = cursor.fetchone()[0]
        conn.close()
        return next_id

    def add_entity(self, entity: Dict) -> int:
        """添加企业"""
        entity_id = self._next_id("entities")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities (id, name, credit_code, entity_type, taxpayer_type,
            legal_representative, business_status, taxpayer_status,
            province, city, tax_authority, login_url, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entity_id,
                entity["name"],
                entity["credit_code"],
                entity["entity_type"],
                entity.get("taxpayer_type", "small_scale"),
                entity.get("legal_representative"),
                entity.get("business_status", "正常"),
                entity.get("taxpayer_status", "正常"),
                entity.get("province"),
                entity.get("city"),
                entity.get("tax_authority"),
                entity.get("login_url"),
                self._current_user_id,
            ),
        )
        conn.commit()
        conn.close()
        return entity_id

    def get_entities(self) -> List[Dict]:
        """获取所有企业列表（按用户隔离）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if self._current_user_id is not None:
            cursor.execute("SELECT * FROM entities WHERE user_id=? ORDER BY id", (self._current_user_id,))
        else:
            cursor.execute("SELECT * FROM entities ORDER BY id")
        entities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return entities

    def get_entity(self, entity_id: int) -> Optional[Dict]:
        """根据ID获取企业"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if self._current_user_id is not None:
            cursor.execute("SELECT * FROM entities WHERE id=? AND user_id=?", (entity_id, self._current_user_id))
        else:
            cursor.execute("SELECT * FROM entities WHERE id=?", (entity_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_entity(self, entity_id: int, entity: Dict):
        """更新企业信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE entities SET
                name=?, credit_code=?, entity_type=?, taxpayer_type=?,
                legal_representative=?, business_status=?, taxpayer_status=?,
                province=?, city=?, tax_authority=?, login_url=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """,
            (
                entity["name"],
                entity["credit_code"],
                entity["entity_type"],
                entity.get("taxpayer_type", "small_scale"),
                entity.get("legal_representative"),
                entity.get("business_status", "正常"),
                entity.get("taxpayer_status", "正常"),
                entity.get("province"),
                entity.get("city"),
                entity.get("tax_authority"),
                entity.get("login_url"),
                entity_id,
            ),
        )
        conn.commit()
        conn.close()

    def delete_entity(self, entity_id: int):
        """删除企业"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if self._current_user_id is not None:
            cursor.execute("DELETE FROM entities WHERE id=? AND user_id=?", (entity_id, self._current_user_id))
        else:
            cursor.execute("DELETE FROM entities WHERE id=?", (entity_id,))
        conn.commit()
        conn.close()

    def save_income(self, entity_id: int, year: int, quarter: int,
                    income: float, expenses: float, notes: str = None):
        """保存收入记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM income_records WHERE entity_id=? AND year=? AND quarter=?",
            (entity_id, year, quarter),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE income_records
                SET income=?, expenses=?, notes=?, created_at=CURRENT_TIMESTAMP
                WHERE entity_id=? AND year=? AND quarter=?
            """,
                (income, expenses, notes, entity_id, year, quarter),
            )
        else:
            rec_id = self._next_id("income_records")
            cursor.execute(
                """
                INSERT INTO income_records (id, entity_id, year, quarter, income, expenses, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (rec_id, entity_id, year, quarter, income, expenses, notes),
            )

        conn.commit()
        conn.close()

    def get_income(self, entity_id: int, year: int, quarter: int) -> Optional[Dict]:
        """获取收入记录（优先从交易汇总）"""
        summary = self.get_quarterly_summary(entity_id, year, quarter)
        if summary["income"] > 0 or summary["expense"] > 0:
            return {
                "income": summary["income"],
                "expenses": summary["expense"],
                "notes": "",
            }

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM income_records WHERE entity_id=? AND year=? AND quarter=?",
            (entity_id, year, quarter),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_income_by_entity(self, entity_id: int, year: int = None) -> List[Dict]:
        """获取企业所有收入记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if year:
            cursor.execute(
                "SELECT * FROM income_records WHERE entity_id=? AND year=? ORDER BY quarter",
                (entity_id, year),
            )
        else:
            cursor.execute(
                "SELECT * FROM income_records WHERE entity_id=? ORDER BY year DESC, quarter",
                (entity_id,),
            )

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    def save_tax_record(self, entity_id: int, year: int, quarter: int,
                        tax_type: str, taxable_income: float, tax_amount: float,
                        tax_rate: float, notes: str = None) -> int:
        """保存/更新税务记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM tax_records
            WHERE entity_id=? AND year=? AND quarter=? AND tax_type=?
        """,
            (entity_id, year, quarter, tax_type),
        )
        existing = cursor.fetchone()

        if existing:
            rec_id = existing[0]
            cursor.execute(
                """
                UPDATE tax_records
                SET taxable_income=?, tax_amount=?, tax_rate=?, notes=?,
                    is_submitted=0, submitted_at=NULL
                WHERE id=?
            """,
                (taxable_income, tax_amount, tax_rate, notes, rec_id),
            )
        else:
            rec_id = self._next_id("tax_records")
            cursor.execute(
                """
                INSERT INTO tax_records
                (id, entity_id, year, quarter, tax_type, taxable_income,
                 tax_amount, tax_rate, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (rec_id, entity_id, year, quarter, tax_type,
                 taxable_income, tax_amount, tax_rate, notes),
            )

        conn.commit()
        conn.close()
        return rec_id

    def get_tax_records(self, entity_id: int, year: int = None) -> List[Dict]:
        """获取税务记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if year:
            cursor.execute(
                "SELECT * FROM tax_records WHERE entity_id=? AND year=? ORDER BY quarter, tax_type",
                (entity_id, year),
            )
        else:
            cursor.execute(
                "SELECT * FROM tax_records WHERE entity_id=? ORDER BY year DESC, quarter, tax_type",
                (entity_id,),
            )

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    def mark_submitted(self, record_id: int):
        """标记为已申报"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE tax_records
            SET is_submitted=1, submitted_at=CURRENT_TIMESTAMP
            WHERE id=?
        """,
            (record_id,),
        )
        conn.commit()
        conn.close()

    def add_transaction(self, entity_id: int, trans_date: str, trans_type: str,
                        category: str, amount: float, description: str = None) -> int:
        """添加交易记录"""
        trans_id = self._next_id("transactions")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (id, entity_id, trans_date, trans_type, category, amount, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (trans_id, entity_id, trans_date, trans_type, category, amount, description),
        )
        conn.commit()
        conn.close()
        return trans_id

    def delete_transaction(self, trans_id: int):
        """删除交易记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
        conn.commit()
        conn.close()

    def get_transactions(self, entity_id: int, year: int = None, month: int = None) -> List[Dict]:
        """获取交易记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM transactions WHERE entity_id=?"
        params = [entity_id]

        if year:
            query += " AND strftime('%Y', trans_date)=?"
            params.append(str(year))
        if month:
            query += " AND strftime('%m', trans_date)=?"
            params.append(f"{month:02d}")

        query += " ORDER BY trans_date DESC, id DESC"

        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records

    def get_quarterly_summary(self, entity_id: int, year: int, quarter: int) -> Dict:
        """获取季度汇总"""
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT trans_type, SUM(amount) as total
            FROM transactions
            WHERE entity_id=?
            AND strftime('%Y', trans_date)=?
            AND CAST(strftime('%m', trans_date) AS INTEGER) BETWEEN ? AND ?
            GROUP BY trans_type
        """,
            (entity_id, str(year), start_month, end_month),
        )

        summary = {"income": 0, "expense": 0}
        for row in cursor.fetchall():
            if row["trans_type"] == "income":
                summary["income"] = row["total"]
            elif row["trans_type"] == "expense":
                summary["expense"] = row["total"]

        summary["profit"] = summary["income"] - summary["expense"]
        conn.close()
        return summary

    def get_monthly_summary(self, entity_id: int, year: int, month: int) -> Dict:
        """获取月度汇总"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT trans_type, category, SUM(amount) as total
            FROM transactions
            WHERE entity_id=?
            AND strftime('%Y', trans_date)=?
            AND strftime('%m', trans_date)=?
            GROUP BY trans_type, category
            ORDER BY trans_type, total DESC
        """,
            (entity_id, str(year), f"{month:02d}"),
        )

        result = {"income": {}, "expense": {}, "total_income": 0, "total_expense": 0}
        for row in cursor.fetchall():
            if row["trans_type"] == "income":
                result["income"][row["category"]] = row["total"]
                result["total_income"] += row["total"]
            elif row["trans_type"] == "expense":
                result["expense"][row["category"]] = row["total"]
                result["total_expense"] += row["total"]

        result["profit"] = result["total_income"] - result["total_expense"]
        conn.close()
        return result

    def list_entities(self):
        """列出所有企业（别名方法）"""
        return self.get_entities()