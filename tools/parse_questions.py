import re
import json
import os
import sys

# SOURCE_FILE = r"c:\Users\Acer\.gemini\antigravity\brain\97d6784c-d44e-48ff-b049-ed56afad70fc\full_questions.md"
# Let's use the path found in list_dir to be sure, or pass it as arg.
# We will defaults to the hardcoded path but allow override.
SOURCE_FILE = r"c:\Users\Acer\.gemini\antigravity\brain\97d6784c-d44e-48ff-b049-ed56afad70fc\full_questions.md"
OUTPUT_FILE = r"c:\Users\Acer\.gemini\antigravity\playground\galactic-singularity\archetype_bot\data\questions.json"

def parse_markdown():
    print(f"Checking Source File: {SOURCE_FILE}")
    if not os.path.exists(SOURCE_FILE):
        print(f"ERROR: Source file not found at {SOURCE_FILE}")
        sys.exit(1)
        
    try:
        with open(SOURCE_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"Read {len(content)} bytes from file.")
    except Exception as e:
        print(f"ERROR reading file: {e}")
        sys.exit(1)

    question_pattern = re.compile(r"## (\d+)\.\s+(.*?)\n(.*?)(?=## \d+\.|# Part|$)", re.DOTALL)
    
    matches = question_pattern.findall(content)
    print(f"Found {len(matches)} potential questions via regex.")
    
    final_questions = []
    
    for q_num, q_title, q_body in matches:
        try:
            q_num_int = int(q_num)
            domain = "Business"
            if 13 <= q_num_int <= 24: domain = "Family"
            if 25 <= q_num_int <= 36: domain = "Social"
            
            context_match = re.search(r"\*\*Context:\*\*(.*?)\n", q_body)
            coaching_match = re.search(r"\*\*Coaching Question:\*\*(.*?)\n", q_body)
            
            context = context_match.group(1).strip() if context_match else ""
            coaching_q = coaching_match.group(1).strip().strip("*") if coaching_match else ""
            
            options = []
            lines = q_body.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("*   **") or line.startswith("* **"):
                    if "**F)**" in line:
                        options.append({"id": "F", "text": "Власна відповідь", "archetype": None, "points": 0})
                        continue
                    
                    match = re.search(r"\*\*([A-E])\)\s*(.*?):\*\*\s*\"(.*?)\"", line)
                    if match:
                        oid = match.group(1)
                        arch = match.group(2).strip()
                        text = match.group(3).strip()
                        options.append({"id": oid, "text": text, "archetype": arch, "points": 2})
            
            if len(options) < 5:
                print(f"WARNING: Question {q_num_int} has only {len(options)} options.")

            final_questions.append({
                "id": q_num_int,
                "text": q_title.strip(),
                "context": context,
                "coaching_question": coaching_q,
                "options": options,
                "domain": domain
            })
        except Exception as e:
            print(f"Error parsing question {q_num}: {e}")

    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_questions, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote {len(final_questions)} questions to {OUTPUT_FILE}")
    except Exception as e:
        print(f"ERROR writing JSON: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parse_markdown()
