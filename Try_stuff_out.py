import random
import time
import threading

many_tr = 50
to_read = []
ptr_1 = 1
while ptr_1 <= 50:
    to_read.append(ptr_1)
    ptr_1 += 1

ptr_1 = 0
mutex = 1
list_of_results = []
def print_nums():
    global ptr_1, mutex
    while ptr_1 < len(to_read):
        while mutex < 1:
            pass
        mutex -= 1
        num = to_read[ptr_1]
        ptr_1 += 1
        list_of_results.append(num)
        mutex += 1
        to_sleep = random.randrange(100, 1900) / 1000
        time.sleep(to_sleep)

start = time.time()
num_threads = 10
tpt = 0
lots = []
while tpt < num_threads:
    lots.append(threading.Thread(target=print_nums, args=()))
    tpt += 1
for t in lots:
    t.start()
for t in lots:
    t.join()
finish = time.time()

print(f"took {int(finish - start)} seconds")
print(list_of_results)
print("all done!")