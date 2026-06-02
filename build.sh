./ins_req.sh

awk '
/version *=/ {
    match($0, /[0-9]+/)
    num = substr($0, RSTART, RLENGTH) + 1
    sub(/[0-9]+/, num)
}
{ print }
' app_version.py > tmp && mv tmp app_version.py

# Build ALS Inventory Manager
python -m PyInstaller --onefile \
    --collect-all tkcalendar \
    --collect-all babel \
    --noconsole \
    --name "ALS Inventory Manager" \
    main.py

# Build ALS Inventory Helper
python -m PyInstaller --onefile \
    --collect-all tkcalendar \
    --collect-all babel \
    --noconsole \
    --name "ALS Inventory Helper" \
    helper.py

mv "dist/ALS Inventory Helper"* "dist/Resources/Helper/"
