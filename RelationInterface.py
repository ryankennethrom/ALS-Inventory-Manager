import sqlite3
import pandas as pd  # for export to Excel
from typing import List, Dict, Any

class RelationInterface:
    def __init__(self, relation_name: str, default_search_text: str, simple_search_field: str,
                 default_filters: List[Dict[str, Any]], db_path="inventory.db"):
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

    def on_item_save_clicked(self, item_index: int, item_details: Dict[str, Any]):
        """Update the row in the database with new details"""
        try:
            item = self.curr_results[item_index]
        except IndexError:
            raise ValueError(f"Item index {item_index} out of range")

        # Build UPDATE statement
        set_clause = ", ".join([f"{col}=?" for col in item_details.keys()])
        params = list(item_details.values())
        params.append(item[self.simple_search_field])  # WHERE condition

        query = f"UPDATE {self.relation_name} SET {set_clause} WHERE {self.simple_search_field}=?"

        with sqlite3.connect(self.db_path) as conn:
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

        query = f"DELETE FROM {self.relation_name} WHERE {self.simple_search_field}=?"
        params = [item[self.simple_search_field]]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        self.curr_results = self.on_search_clicked()

    def on_create_item_clicked(self, details: Dict[str, Any]):
        """Insert a new row into the database"""
        columns = ", ".join(details.keys())
        placeholders = ", ".join(["?"] * len(details))
        params = list(details.values())

        query = f"INSERT INTO {self.relation_name} ({columns}) VALUES ({placeholders})"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        self.curr_results = self.on_search_clicked()

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
            for flter in self.filter_dict:
                clauses.append(flter["clause"])
                params.append(flter["param"])

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        with sqlite3.connect(self.db_path) as conn:
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
