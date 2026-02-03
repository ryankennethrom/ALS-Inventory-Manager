class Interface:
    def __init__(self, table_or_view, options):
        self.table_or_view = table_or_view
        self.options = options
    
    def on_search_clicked(self):
        raise Exception(f"on_search_clicked() must be overriden in {self.__class__.__name__}")

    def export_as_excel(self):
        raise Exception(f"export_as_excel() must be overriden in {self.__class__.__name__}")


