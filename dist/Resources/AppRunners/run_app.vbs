
            Set WshShell = CreateObject("Wscript.Shell")
            WshShell.Run "powershell.exe -WindowStyle Hidden -Command ""Start-Process 'ALS Inventory Manager.exe' -WorkingDirectory 'C:\Users\aledm.lab01\Staging\ALS-Inventory-Manager\dist' -WindowStyle Hidden""", 0, False
            