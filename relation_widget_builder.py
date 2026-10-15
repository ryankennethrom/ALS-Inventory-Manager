from RelationWidget import RelationWidget
from RelationInterface import RelationInterface
from tkinter import ttk 
from types import MethodType
import DB
import types

class RelationWidgetBuilder():
    def __init__(self, parent=None, db_path=None):
        self.db_path = db_path if db_path is not None else DB.get_db_path()
        self.widget = None
        self.default_results_color = None
        self.interface = None
        self.interface_params = dict()
        self.widget_params = dict()
        self.widget_params["master"] =  parent
        self.on_create_item_clicked_override = None

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
        self.title(title)
        self.relation_name(relation_name)
        self.is_view(is_view)
        self.filter_results_color(filter_results_color)
        self.simple_search_field(simple_search_field)
        self.min_height(minimum_height)
        self.default_search_text(default_search_text)
        self.labels(labels)
        
        return self
    
    def min_height(self, height):
        self.widget_params["min_height"] = height
        return self

    def relation_name(self, name):
        self.interface_params["relation_name"] = name
        return self

    def default_search_text(self, text):
        self.interface_params["default_search_text"] = text
        return self

    def simple_search_field(self, field):
        self.interface_params["simple_search_field"] = field
        return self

    def exclude_fields_on_update(self, fields):
        self.widget_params["exclude_fields_on_update"] = fields
        return self

    def exclude_fields_on_create(self, fields):
        self.widget_params["exclude_fields_on_create"] = fields
        return self

    def title(self, text):
        self.widget_params["title"] = text
        return self

    def is_view(self, boolean):
        self.widget_params["is_view"] = boolean
        return self
    
    def override_on_create_item_clicked(self, new_func):
        self.on_create_item_clicked_override = new_func
        return self

    def labels(self, labels):
        self.widget_params["labels"] = labels
        return self

    def parent(self, parent):
        self.widget_params["master"] = parent
        return self

    def filter_results_color(self, color):
        self.widget_params["filter_results_color"] = color
        return self
    
    def default_results_highlight(self, color):
        self.default_results_color = color
        return self

    def order_by(self, param):
        self.interface_params["order_by"] = param
        return self

    def no_export(self):
        self.widget_params["no_export"] = True
        return self

    def build(self):
        interface = RelationInterface(
                db_path=self.db_path,
                **self.interface_params
            )
        
        self.interface = interface
        self.widget_params["relation_interface"] = interface
        widget = RelationWidget(
                **self.widget_params
        )

        if self.default_results_color:
            def new_function(obj):
                color = self.default_results_color
                style = ttk.Style()
                new_style = f"RelationWidget{obj.id}NewDefault.Treeview"
                style.configure(
                            new_style,
                            background=color,
                            fieldbackground=color,
                            bordercolor=color,
                            foreground="black")

                obj.tree.configure(style=new_style)

            widget.reset_highlight_items_to_default = MethodType(new_function, widget)
        
        if self.on_create_item_clicked_override:
            interface.on_create_item_clicked_original = interface.on_create_item_clicked
            interface.on_create_item_clicked = types.MethodType(self.on_create_item_clicked_override, interface)

        return widget




