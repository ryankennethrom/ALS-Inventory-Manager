class ItemInterface:
    def __init__(self, table_or_view, item_id):
        self.table_or_view = table_or_view
        self.item_id = item_id

    def on_double_click(self):
        raise Exception(f"on_double_click(self) must be overriden in {self.__class__.__name__}")

    def on_delete_clicked(self):
        raise Exception(f"on_delete_clicked(self) must be overriden in {self.__class__.__name__}")

    def on_save_clicked(self):
        raise Exception(f"on_save_clicked(self) must be overriden in {self._class__.__name__}"


