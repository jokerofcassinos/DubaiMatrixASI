import os
import json
import shutil
from datetime import datetime

base_dir = "d:/DubaiMatrixASI/data/audits/ghost_trade_audits"

def migrate_category(category):
    cat_path = os.path.join(base_dir, category)
    if not os.path.exists(cat_path): return
    
    files = [f for f in os.listdir(cat_path) if f.endswith(".json") and os.path.isfile(os.path.join(cat_path, f))]
    print(f"Migrating {len(files)} files in {category}...")
    
    for filename in files:
        old_path = os.path.join(cat_path, filename)
        try:
            with open(old_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extrair data e ciclo
            entry_time = data.get("entry_time")
            cycle_code = data.get("cycle_code", "cycle_000")
            
            if entry_time:
                date_str = entry_time.split("T")[0]
            else:
                # Usar data de modificação se não houver entry_time
                mtime = os.path.getmtime(old_path)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            
            new_dir = os.path.join(cat_path, date_str, cycle_code)
            os.makedirs(new_dir, exist_ok=True)
            
            new_path = os.path.join(new_dir, filename)
            shutil.move(old_path, new_path)
            # print(f"Moved {filename} -> {new_path}")
        except Exception as e:
            print(f"Error migrating {filename}: {e}")

migrate_category("corretos")
migrate_category("errados")
print("Migration completed.")
