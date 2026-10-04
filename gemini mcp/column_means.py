import csv

def column_means(path):
    with open(path, mode='r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {}
        
        col_values = {field: [] for field in reader.fieldnames}
        for row in reader:
            for k in reader.fieldnames:
                col_values[k].append(row.get(k))

    result = {}
    for col, vals in col_values.items():
        nums = []
        is_numeric = True
        for v in vals:
            if v is None or v.strip() == '':
                continue
            try:
                nums.append(float(v))
            except ValueError:
                is_numeric = False
                break
        if is_numeric and nums:
            result[col] = sum(nums) / len(nums)

    return result

if __name__ == "__main__":
    print(column_means("sample.csv"))

