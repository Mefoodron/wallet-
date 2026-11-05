import os
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    application_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    application_path = base_path

DATA_FILE = os.path.join(application_path, "expenses.csv")

from gui import WalletApp

if __name__ == "__main__":
    app = WalletApp(data_file=DATA_FILE, base_path=base_path)
    app.mainloop()