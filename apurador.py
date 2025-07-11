import tkinter as tk
from ExtratorFinanceiro import ExtratorFinanceiro

if __name__ == "__main__":
    root = tk.Tk()
    
    # Tentar usar tema do Windows se disponível
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = ExtratorFinanceiro(root)
    root.mainloop()