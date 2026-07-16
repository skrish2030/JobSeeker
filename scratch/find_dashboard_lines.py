with open('terraform/monitoring_userdata.sh', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'Create Dashboard JSON config file' in line:
            print(f"Start: Line {i+1}")
        if i > 250 and i < 1150 and line.strip() == 'EOF':
            print(f"End: Line {i+1}")
