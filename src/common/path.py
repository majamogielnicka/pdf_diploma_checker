import os
import sys

import os
import sys

def resource_path(relative_path):
    """Zwraca absolutną ścieżkę do zasobów, działającą lokalnie i w PyInstallerze"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        if not relative_path.startswith("src") and "src" in os.listdir(os.path.dirname(src_dir)):
            return os.path.join(src_dir, relative_path)
        
        return os.path.join(os.path.dirname(src_dir), relative_path)