import Interface

class TableInterface(Interface):
    def on_create_clicked(self):
        raise Exception(f"on_create_clicked() must be overriden in {self.__class__.__name__}")

    def on_item_clicked(self, item):
        raise Exception(f"on_item_clicked(item) must be overriden in {self.__class__.__name__}"

