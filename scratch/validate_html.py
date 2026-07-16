from html.parser import HTMLParser

class TagBalancer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        
    def handle_starttag(self, tag, attrs):
        # Self-closing tags in HTML5
        if tag in ["img", "input", "br", "hr", "meta", "link", "col", "base"]:
            return
        self.stack.append((tag, self.getpos()))
        
    def handle_endtag(self, tag):
        if tag in ["img", "input", "br", "hr", "meta", "link", "col", "base"]:
            return
        if not self.stack:
            print(f"Error: Closed tag </{tag}> at line {self.getpos()[0]} but stack is empty!")
            return
        last_tag, pos = self.stack.pop()
        if last_tag != tag:
            print(f"Error: Mismatched tag: opened <{last_tag}> at line {pos[0]} but closed </{tag}> at line {self.getpos()[0]}")
            # Put it back to try to keep balancing
            self.stack.append((last_tag, pos))

with open("frontend/index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

parser = TagBalancer()
parser.feed(html_content)

if parser.stack:
    print("Error: The following tags were never closed:")
    for tag, pos in reversed(parser.stack):
        print(f"  <{tag}> opened at line {pos[0]}")
else:
    print("Success: All tags are perfectly balanced!")
