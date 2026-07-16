import sys

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\auto_applier.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Find the start of the block
start_marker = "    with sync_playwright() as p:"
if start_marker not in content:
    print("Could not find start marker.")
    sys.exit(1)

parts = content.split(start_marker)
before_block = parts[0] + start_marker + "\n"
block = parts[1]

# In the original, it starts with:
#         try:
#             # Launch browser
#             browser = p.chromium.launch(headless=headless)

old_start = """        try:
            # Launch browser
            browser = p.chromium.launch(headless=headless)"""
            
new_start = """        last_error = None
        for browser_engine in [p.chromium, p.firefox, p.webkit]:
            try:
                logger.info(f"Attempting automation with {browser_engine.name}...")
                browser = browser_engine.launch(headless=headless)"""

if old_start not in block:
    print("Could not find old_start")
    sys.exit(1)

block = block.replace(old_start, new_start)

# Now we need to fix the exception handling at the end of the block.
# Old:
#         except Exception as e:
#             logger.error(f"Playwright auto-apply failed: {e}")
#             return {"status": "error", "message": f"Playwright automation encountered an error: {str(e)}"}
#         finally:
#             try: browser.close()
#             except Exception: pass

old_end = """        except Exception as e:
            logger.error(f"Playwright auto-apply failed: {e}")
            return {"status": "error", "message": f"Playwright automation encountered an error: {str(e)}"}
        finally:
            try: browser.close()
            except Exception: pass"""

new_end = """            except Exception as e:
                logger.warning(f"Playwright automation failed with {browser_engine.name}: {e}")
                last_error = e
                continue
            finally:
                try: browser.close()
                except Exception: pass
        
        logger.error(f"Playwright auto-apply failed on all browsers. Last error: {last_error}")
        return {"status": "error", "message": f"Playwright automation failed on all browsers: {str(last_error)}"}"""

if old_end not in block:
    print("Could not find old_end")
    sys.exit(1)

block = block.replace(old_end, new_end)

# We need to indent everything between new_start and new_end by 4 spaces.
lines = block.split("\n")
inside = False
new_lines = []
for line in lines:
    if line.strip() == "context = browser.new_context(":
        inside = True
    
    if inside and line.strip() == "except Exception as e:": # Reached the new_end part which is already indented properly in replacement
        inside = False
        
    if inside and line != "":
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

new_content = before_block + "\n".join(new_lines)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("Successfully refactored auto_applier.py")
