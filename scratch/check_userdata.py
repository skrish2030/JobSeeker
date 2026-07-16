with open('terraform/monitoring_userdata.sh', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '${' in line:
            print(f"Line {i+1} ($): {line.strip()}")
        if '%{' in line:
            print(f"Line {i+1} (%): {line.strip()}")
