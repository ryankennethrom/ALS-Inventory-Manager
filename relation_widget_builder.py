from RelationWidget import RelationWidget
from RelationInterface import RelationInterface
from tkinter import ttk 
from types import MethodType

class RelationWidgetBuilder():
    def __init__(self, parent, db_path):
        self.db_path = db_path
        self.widget = None
        self.parent = parent

    def default_widget(
        self,
        *,
        title,
        relation_name,
        is_view,
        filter_results_color="#ADD8E6",
        simple_search_field="ProductName",
        minimum_height=500,
        default_search_text="",
        labels=None):
        
        interface = RelationInterface(
                        relation_name=relation_name,
                        default_search_text=default_search_text,
                        simple_search_field=simple_search_field,
                        db_path=self.db_path
                    )

        self.widget = RelationWidget(
                self.parent,
                interface,
                labels=labels,
                min_height=minimum_height,
                is_view=is_view,
                filter_results_color=filter_results_color,
                title=title
            )

        return self
    
    def default_results_highlight(self, color):
        def new_function(obj):
            style = ttk.Style()
            new_style = f"RelationWidget{obj.id}NewDefault.Treeview"
            style.configure(
                        new_style,
                        background=color,
                        fieldbackground=color,
                        bordercolor=color,
                        foreground="black")

            obj.tree.configure(style=new_style)

        self.widget.reset_highlight_items_to_default = MethodType(new_function, self.widget)
        return self

    def build(self):
        if self.widget is None:
            raise Exception("Did not create a RelationWidget() or RelationInterface() after calling WidgetBuilder()")
        return self.widget




