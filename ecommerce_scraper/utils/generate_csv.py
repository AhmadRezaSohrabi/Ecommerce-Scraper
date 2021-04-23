import csv

def generate_csv(data, filename='export'):
    with open(filename + '.csv', 'w', encoding='utf-8') as csv_f:
        writer = csv.DictWriter(csv_f, data[0].keys())
        writer.writeheader()
        writer.writerows(data)