./ins_req.sh
python -m PyInstaller --onefile --collect-all tkcalendar --collect-all babel --noconsole --name "ALS Inventory Manager" main.py
