import sqlite3
import pandas as pd  # for export to Excel
from typing import List, Dict, Any
import DB
from datetime import datetime

class RelationInterface:
    def __init__(self, relation_name: str, default_search_text: str, simple_search_field: str,
                 default_filters: List[Dict[str, Any]], db_path=DB.db_path):
        self.relation_name = relation_name
        self.db_path = db_path
        self.simple_search_field = simple_search_field
        self.filter_dict = default_filters
        self.search_field_text = default_search_text or ""
        self.curr_results = self.on_search_clicked()  # initial load

    def on_filter_changed(self, new_filter_dict):
        self.filter_dict = new_filter_dict

    def on_search_field_changed(self, text):
        self.search_field_text = text

    def on_item_clicked(self, item_index: int) -> Dict[str, Any]:
        """Return the item at the given index from the current results"""
        try:
            return self.curr_results[item_index]
        except IndexError:
            raise ValueError(f"Item index {item_index} out of range")
    
    def get_item(self, item_index):
        try:
            return self.curr_results[item_index]
        except IndexError:
            raise ValueError(f"Item index {item_index} out of range")

    def on_item_updated(self, item_index: int, item_details: Dict[str, Any]):
        """Update the row in the database with new details"""
        try:
            item = self.curr_results[item_index]
        except IndexError:
            raise ValueError(f"Item index {item_index} out of range")

        self.validate_date_inputs(item_details)
        # Build UPDATE statement
        set_clause = ", ".join([f"{col}=?" for col in item_details.keys()])
        where_clause = " AND ".join([f"{col}=?" for col in item.keys()])
        params = list(item_details.values()) + list(item.values())
        query = f"UPDATE {self.relation_name} SET {set_clause} WHERE {where_clause}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        self.curr_results = self.on_search_clicked()  # refresh

    def on_item_delete_clicked(self, item_index: int):
        """Delete the row at the given index from the database"""
        try:
            item = self.curr_results[item_index]
        except IndexError:
            raise ValueError(f"Item index {item_index} out of range")
        
        where_clause = " AND ".join([f"{col}=?" for col in item.keys()])
        query = f"DELETE FROM {self.relation_name} WHERE {where_clause}"
        params = list(item.values())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        self.curr_results = self.on_search_clicked()
    
    def on_create_item_clicked(self, details: dict):
        """Insert a new row into the database. Returns (status, user_message, error_details)."""
        self.validate_date_inputs(details)
        columns = ", ".join(details.keys())
        placeholders = ", ".join(["?"] * len(details))
        params = list(details.values())

        query = f"INSERT INTO {self.relation_name} ({columns}) VALUES ({placeholders})"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        self.curr_results = self.on_search_clicked()
    
    def validate_date_inputs(self, details):

        def is_valid_date(value: str) -> bool:
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return True
            except (ValueError, TypeError):
                return False

        col_types = DB.get_column_types(self.relation_name)

        for key, value in details.items():
            expected_type = col_types.get(key)

            if expected_type == "date":
                if not is_valid_date(value) and value != "":
                    raise ValueError(
                        f"Invalid date. Make sure {key} has the format YYYY-MM-DD and is a real date."
                    )
        return True

    def on_search_clicked(self) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.relation_name}"
        clauses = []
        params = []

        # Add LIKE condition for simple search
        if self.search_field_text:
            clauses.append(f"{self.simple_search_field} LIKE ?")
            params.append(f"{self.search_field_text}%")

        # Add additional filters
        if self.filter_dict:
            for key in self.filter_dict.keys():
                clauses += self.filter_dict[key]["clauses"]
                params += self.filter_dict[key]["params"]
        
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        self.curr_results = [dict(zip(columns, row)) for row in results]
        return self.curr_results
    
    def export_as_excel(self, exclude_columns=None, output_path="output.xlsx"):
        if exclude_columns is None:
            exclude_columns = []

        data = self.on_search_clicked()  # filtered results
        df = pd.DataFrame(data)

        # Drop excluded columns (ignore if not present)
        df = df.drop(columns=exclude_columns, errors="ignore")

        df.to_excel(output_path, index=False)
        print(f"Exported {self.relation_name} to {output_path}")
