import json
import os
import datetime

class SavingFiles:
    def __init__(self, index_path=None):
        if index_path is None:
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            self.index_path = os.path.join(app_data, "DiplomaChecker", "index.json")
        else:
            self.index_path = index_path
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self.data = self._load_index()

    def _load_index(self):
        if not os.path.exists(self.index_path) or os.path.getsize(self.index_path) == 0:
            return self._create_initial_index()
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "documents" not in data:
                data["documents"] = []
            if "rule_configurations" not in data:
                data["rule_configurations"] = []
                
            return data
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading index.json: {e}")
            return self._create_initial_index()

    def _create_initial_index(self):
        initial_data = {"documents": [], "rule_configurations": []}
        self._save_to_disk(initial_data)
        return initial_data

    def _save_to_disk(self, data):
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing to file: {e}")

    def add_document(self, name, path, document_type="PDF"):
        if any(doc['local_path'] == path for doc in self.data["documents"]):
            return
            
        new_entry = {
            "file_name": name,
            "local_path": path,
            "type": document_type,
            "date_added": datetime.date.today().strftime("%Y-%m-%d"),
            "comments": []
        }
        self.data["documents"].append(new_entry)
        self._save_to_disk(self.data)

    def delete_document(self, path):
        self.data["documents"] = [doc for doc in self.data["documents"] if doc['local_path'] != path]
        self._save_to_disk(self.data)

    def save_comment(self, path, comment_data):
        for doc in self.data["documents"]:
            if doc['local_path'] == path:
                if "comments" not in doc:
                    doc["comments"] = []
                doc["comments"].append(comment_data)
                self._save_to_disk(self.data)
                return

    def get_comments(self, path):
        for doc in self.data["documents"]:
            if doc['local_path'] == path:
                return doc.get("comments", [])
        return []

    def save_errors(self, path, errors):
        for doc in self.data["documents"]:
            if doc['local_path'] == path:
                doc["analysis_errors"] = errors
                self._save_to_disk(self.data)
                return

    def get_errors(self, path):
        for doc in self.data["documents"]:
            if doc['local_path'] == path:
                return doc.get("analysis_errors", [])
        return []
    
    def save_ai_result(self, path, sota_data):
        for doc in self.data["documents"]:
            if doc['local_path'] == path:
                doc["sota_result"] = sota_data
                self._save_to_disk(self.data)
                return