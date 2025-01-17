# main.py

from telnet_app.telnet_gui import TelnetGUI

def main():
    app = TelnetGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
