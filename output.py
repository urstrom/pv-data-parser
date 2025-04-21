import sys, datetime, pickle, os

def data_print(data, pv_system):
    print(data, file=sys.stderr)

def pickle_write(data, pv_system):
    with open(data[0]['path'] + ".pickle", "wb") as file:
        pickle.dump(data, file)

def js_write(data, pv_system):
    header = data.pop(0)
    output = ""
    for row in data:
        output += f"m[mi++]=\"{row.pop(0).strftime('%d.%m.%Y %H:%M:%S')}"
        for inverter in row:
            inverter_out = [inverter['ac']]
            inverter_out += inverter['dc']
            if 'sum' in inverter:
                inverter_out.append(inverter['sum'])
            if 'voltage' in inverter:
                inverter_out += inverter['voltage']
            if 'temperature' in inverter:
                inverter_out.append(inverter['temperature'])
            output += f"|{';'.join(str(item) for item in inverter_out)}"
        output += "\"\r\n"
    dirname = os.path.dirname(header['path'])
    filename = os.path.basename(header['path'])
    with open(os.path.join(dirname, "w", filename), "w") as file:
        print(output, file=file)


def csv_write(data, pv_system):
    output = []
    header = data.pop(0)
    output.append(header['line1'])
    if 'line2' in header:
        output.append(header['line2'])
    for row in data:
        output += f"{row.pop(0).strftime('%d.%m.%Y %H:%M:%S')};"
        fields = [0] * max(header['tracker_offsets'] + header['inverter_offsets'])
        inverter_count = 0
        tracker_count = 0
        for inverter in row:
            fields[header['inverter_offsets'][inverter_count]] = inverter['ac']
            for tracker in inverter['dc']:
                fields[header['tracker_offsets'][tracker_count]] = tracker
                tracker_count += 1
            inverter_count += 1
        output += fields.join(";")

        # for t in data['tracker_offsets']

