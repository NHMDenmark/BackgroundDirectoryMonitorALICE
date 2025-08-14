For windows use only.
This program will monitor a specific parent folder and send pop ups to the user if the predetermined number of files are not added within a short timeframe.
It is meant to be used while digitizing at the ALICE setup and is set to expect 7 files all starting with the same 10 digits each time. This assumes the files that are being produced from the cameras all start with the barcode in their file name. 

How to install:

Clone the repository.  

Open a terminal window.  

Setup a virtual python environment then install the dependencies (or from requirements.txt):

```
pip install watchdog pystray pillow pyinstaller
```

Navigate to the BackgroundMonitor folder and then run:

```
pyinstaller --noconsole --onefile --name "Folder Monitor" --icon="logo.ico" --add-data "logo.ico;." folder_monitor.py
```

This will create a dist folder with the app in it ("Folder Monitor.exe"). Move or copy it onto the desktop and then double clik it to run it.  

It will keep running until shutdown. This can be done by finding it in the icon tray of running programs and right clicking the icon and then click exit.  