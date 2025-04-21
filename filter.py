import sys

def production(array_in, pv_system):
    array_out = [array_in.pop(0)] # header
    production_indices = [index for index, dictionary in enumerate(pv_system['inverters']) if
                          dictionary.get('is_production') == 1]

    # {'ac': '8383', 'dc': ['2225', '2019', '2278', '2033']}

    for line_in in array_in:
        line_out = [line_in.pop(0)] # timestamp
        for inverter_counter in range(len(pv_system['inverters'])):
            if inverter_counter in production_indices:
                line_out.append(line_in[inverter_counter])
            else: # a consumption counter, filter it out
                field_out = {}
                for key in line_in[inverter_counter]:
                    if isinstance(line_in[inverter_counter][key], int):
                        field_out[key] = 0
                    else: # is list
                        field_out[key] = []
                        for field in line_in[inverter_counter][key]:
                            field_out[key].append(0)
                line_out.append(field_out)
            inverter_counter += 1
        array_out.append(line_out)
    return array_out

def good_array(array_in, pv_system):
    array_out = [array_in.pop(0)] # header

    # {'ac': '8383', 'dc': ['2225', '2019', '2278', '2033']}

    for line_in in array_in:
        good_line = True
        for inverter_counter in range(len(pv_system['inverters'])):
        # a consumption counter, filter it out
            field_out = {}
            for key in line_in[inverter_counter + 1]:
                if isinstance(line_in[inverter_counter + 1][key], int):
                    good_line &= good_value(line_in[inverter_counter + 1][key], line_in[0])
                else: # is list
                    field_out[key] = []
                    for field in line_in[inverter_counter + 1][key]:
                        good_line &= good_value(field, line_in[0])
            inverter_counter += 1
        if good_line:
            array_out.append(line_in)
        else:
            print(f"Bad line: {line_in}")
    return array_out


def good_value(val, context):
    val = int(val)
    if val < 0 or val > 1000000:
        print(f"Error: Context:{context}, Bad value {val}", file=sys.stderr)
        return False
    else:
        return True

def deduplicate_zeros(input_table, pv_system = None):
    """Deletes repetitions of lines that have all 0 value. One copy of all-zero line is kept at each boundary.
    Also keep lines where the interval to preceding line is not 5 minutes."""
    result = []
    if input_table is None:
        return result
    result.append(input_table.pop(0)) # header file
    skip_mode = 0  # if skip_mode == 1, then are we in a region where we are skipping, because all values are zeros
    last_line_inserted = -1  # pointer to avoid inserting a line twice
    # skip first line, it is the header line
    for i in range(len(input_table)):
        # line is empty, skip
        if input_table[i] is None or len(input_table[i]) == 0:
            continue
        # inspect whether all line values are zero
        this_line_is_nonzero = 0
        # we know that the date is non-zero, hence we skip it, and start with field number 1
        for j in range(1, len(input_table[i])):
            for k in input_table[i][j]: # iterate through inverters
                if input_table[i][j][k] != 0:
                    this_line_is_nonzero = 1
        # first and last line, always accept and continue
        if i == len(input_table) - 1 or i == 0:
            result.append(input_table[i])
            if this_line_is_nonzero == 0:
                skip_mode = 1  # relevant if first line is only zeros
            last_line_inserted = i
            continue
        # we are not in skip mode, hence we accept
        if skip_mode == 0:
            result.append(input_table[i])
            if this_line_is_nonzero == 0:
                skip_mode = 1  # enter skip mode
                last_line_inserted = i
        else:  # We are in skip mode, only accept if we found a line that is nonzero or a line following and empty line or a time delta that is not 300 seconds, but then we may have also to accept its predecessor.
            if this_line_is_nonzero == 1 or len(input_table[i - 1]) == 0 or 300 != (
                    input_table[i - 1][0] - input_table[i][0]).seconds:
                if i > last_line_inserted + 1:  # last line (zeros) has not been inserted yet
                    result.append(input_table[i - 1])  # so let's insert it
                result.append(input_table[i])
                last_line_inserted = i
                skip_mode = 0
    return result



