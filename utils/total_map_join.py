import os
import re

def join_maps():
    rules_dir = r"d:\DubaiMatrixASI\.agents\rules"
    output_path = r"d:\DubaiMatrixASI\PLMA\PLMA_TOTAL_CONSOLIDATED.txt"
    
    final_text = ""
    # Check 1 to 9 as user mentioned 9
    for i in range(1, 10):
        name = "projectmap.md" if i == 1 else f"projectmap{i}.md"
        path = os.path.join(rules_dir, name)
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove YAML header --- ... ---
                clean_content = re.sub(r'(?s)^---.*?---\s*', '', content)
                final_text += clean_content.strip() + " "
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text.strip())
    
    print(f"✅ Consolidação Total Realizada: {output_path}")

if __name__ == "__main__":
    join_maps()
