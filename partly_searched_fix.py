import sys

# Because datacollector doesn't always write exit data correctly, if a county shows up in
# error_counties.txt (or maybe even if it doesn't), it might be a good idea to troll the
# zest_data.csv file for addresses that have already been logged for a given county
# and send them to partly_searched_counties.txt. This script does not make sure
# there aren't multiple instances of a county within that file.
def add_county(county_name, state_letters):
    with open('zest_data.csv', 'r') as data:
        county_name = county_name.capitalize()
        dashed_addresses = []
        for line in data:
            if county_name in line:
                street_start = line.find('|') + 1
                start_sum = street_start
                city_start = line[street_start:].find('|') + start_sum + 1
                start_sum = city_start
                state_start = line[city_start:].find('|') + start_sum + 1
                start_sum = state_start
                zipc_start = line[state_start:].find('|') + start_sum + 1
                start_sum = zipc_start
                zipc_end = line[zipc_start:].find('|') + start_sum
                address = []
                address.append(line[street_start:city_start-1])
                address.append(line[city_start:state_start-1])
                address.append(line[state_start:zipc_start-1])
                address.append(line[zipc_start:zipc_end])
                for i in range(len(address)):
                    item = address[i]
                    try:
                        subitems = item.split(' ')
                        dashed_item = '-'.join(subitems)
                        
                    except:
                        dashed_item = item
                    address[i] = dashed_item
                dashed_address = '-'.join(address)
                dashed_addresses.append(dashed_address)
        county_and_state = county_name + ' County, ' + state_letters.upper()
    with open('partly_searched_counties.txt', 'a') as ps_f:
        ps_f.write(f"{county_and_state}:")
        for i in range(len(dashed_addresses) - 1):
            ps_f.write(f"{dashed_addresses[i]}||")
        ps_f.write(f"{dashed_addresses[-1]}\n")

if __name__ == '__main__':
    try:
        assert len(sys.argv) == 3
        county = sys.argv[1].strip('-')
        state = sys.argv[2].strip('-')
        add_county(county, state)
    except:
        print('please call this script with one county name and one state name')
        print('example: python partly_searched_fix.py -monroe -fl')