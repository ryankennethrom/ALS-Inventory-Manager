
            Set WshShell = CreateObject("Wscript.Shell")
            WshShell.Run "powershell.exe -WindowStyle Hidden -Command ""Start-Process 'ALS Inventory Manager.exe' -WorkingDirectory 'G:\QA - NEW\Material Log\InventoryManager' -WindowStyle Hidden""", 0, False
            