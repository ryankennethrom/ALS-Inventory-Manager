import types

relation_widgets = dict()
refresh_callbacks = dict()
next_id = 0

def register(widget, parents):
    global next_id

    for parent in parents:
        if parent not in relation_widgets:
            relation_widgets[parent] = [widget]
        else:
            relation_widgets[parent].append(widget)
        widget.id = next_id
        next_id += 1

def _hash(parents):
    return str(sorted(parents))

def on_refresh(parents, func):
    refresh_callbacks[_hash(parents)] = func

def refresh(parents):
    finished = set()
    for parent in parents:
        for relation_widget in relation_widgets[parent]:
            if relation_widget.id in finished:
                continue
            relation_widget.refresh()
            finished.add(relation_widget.relation.relation_name)
            parent_set_hash = _hash(parents)
            if parent_set_hash in refresh_callbacks:
                refresh_callbacks[parent_set_hash]()

def refresh_all(exceptions=[]):
    parents = {parent for parent in relation_widgets.keys() if parent not in exceptions}
    refresh(parents)

def destroy_popups(parents):
    finished = set()
    for parent in parents:
        for relation_widget in relation_widgets[parent]:
            if relation_widget.relation.relation_name in finished:
                continue
            if relation_widget.popup is not None:
                relation_widget.popup.destroy()

def destroy_all_popups(exceptions=[]):
    parents = {parent for parent in relation_widgets.keys() if parent not in exceptions}
    finished = set()
    for parent in parents:
        for relation_widget in relation_widgets[parent]:
            if relation_widget.relation.relation_name in finished:
                continue
            if relation_widget.popup is not None:
                relation_widget.popup.destroy()



def on_table_update(callback, exceptions=[], parents={parent for parent in relation_widgets.keys()}):
    parents = {parent for parent in parents if parent not in exceptions}
    finished = set()
    for parent in parents:
        for relation_widget in relation_widgets[parent]:
            if relation_widget.relation.relation_name in finished:
                continue
            
            if not hasattr(relation_widget, "update_table_original_saved"):
                relation_widget.update_table_original = relation_widget.update_table
            
            if not hasattr(relation_widget, "callbacks"):
                relation_widget.callbacks = []
            
            relation_widget.callbacks.append(callback)

            def callback_after_table_update(obj):
                obj.update_table_original()
                for c in obj.callbacks:
                    c()
            relation_widget.update_table = types.MethodType(callback_after_table_update, relation_widget)
