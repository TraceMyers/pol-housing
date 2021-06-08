from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN 
from multiprocessing import Pool, Process, Manager
import time


# instructions = initialize_VPN(area_input=['complete rotation'])
# r = 1

# for i in range(r):
#     rotate_VPN(instructions)
#     print('doing things')
#     time.sleep(10)

# terminate_VPN(instructions)

def f(process_list):
    for i in range(5):
        process_list.append(i)

if __name__ == '__main__':
    with Manager() as manager:
        process_list = manager.list()
        processes = [Process(target=f, args=(process_list,)) for i in range(5)]
        for p in processes:
            p.start()
            p.join()
        for p in processes:
                p.terminate()
        print(process_list)
