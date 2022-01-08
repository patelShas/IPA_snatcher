#!/usr/bin/env python3

import socket
import ssl
import argparse
import time
import threading

# set up arguments
parser = argparse.ArgumentParser()
parser.add_argument('wordlist')
args = parser.parse_args()

wordlist = args.wordlist

# Create Context
hostname = 'en.wiktionary.org'
context = ssl.create_default_context()


def send_get(sock, address, contents):  # O(constant)
    msg = "GET {} HTTP/1.1\r\n" \
          "From: shashwat.sudashima@gmail.com\r\n" \
          "Host: {}\r\n" \
          "Connection: keep-alive\r\n" \
          "{}\r\n".format(address, hostname, contents)
    # print(msg)
    sock.send(msg.encode())


main_list_of_words = []
with open(wordlist) as f:
    lines = f.readlines()
for line in lines:
    main_list_of_words.append(line[:-1])
count = 0
code_results = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
real_start = time.time()

mutex = 1
words_as_read = []
ptr = 0
english_found = 0
english_not_found = 0


def process_words(list_of_words, list_of_fails, list_of_results):
    global count, code_results, mutex, ptr, english_found, english_not_found
    sock = socket.create_connection((hostname, 443))
    sock = context.wrap_socket(sock, server_hostname=hostname)
    sock.settimeout(1)
    while True:
        if ptr >= len(list_of_words):
            break
        while mutex < 1:
            pass
        mutex -= 1
        word = list_of_words[ptr]
        count += 1
        ptr += 1
        words_as_read.append(word)
        mutex += 1
        send_get(sock, f"/wiki/{word}", "")
        response = b""
        while b"</html>" not in response:
            try:
                response += sock.recv(4096)
            except socket.timeout:
                break
        response = response.decode('utf-8', 'replace')
        if response == "":
            list_of_fails.append(word)
        else:
            http_code = response[9:12]
            if http_code != "" and http_code.isnumeric():
                if http_code[0] == "2":
                    if '<span class="mw-headline" id="English">English</span>' in response and '<span class="mw-headline" id="References">References</span>' in response:
                        english_found += 1
                    else:
                        english_not_found += 1
                elif http_code[0] == "4":
                    list_of_fails.append(word)
                code_results[http_code[0]] += 1
            start = response.find('<span class="mw-headline" id="English">English</span>')
            ref = response.find('<span class="mw-headline" id="References">References</span>', start)
            line_split = response.find('hr ', start)
            if ref == -1:
                end = line_split
            elif line_split == -1:
                end = ref
            else:
                end = min(ref, line_split)
            if start != -1 and end != -1:
                subsection = response[start:end]
                pt = subsection.find('<span class="IPA">')
                pt2 = subsection.find('</span>', pt)
                entry = f"{word}"
                while pt != -1:
                    if entry[0] != '-':
                        entry += f' {subsection[pt:pt2][18:]}'
                    subsection = subsection[pt2:]
                    pt = subsection.find('<span class="IPA">')
                    pt2 = subsection.find('</span>', pt)
                if entry != word:
                    list_of_results.append(entry)

    sock.close()


def run_thru(num_threads, how_many):
    global mutex, words_as_read, ptr, english_found, english_not_found
    mutex = 1
    words_as_read = []
    ptr = 0
    english_found = 0
    english_not_found = 0
    list_of_results = []

    num_words = how_many // num_threads
    lots = []
    lofs = []
    i = 0
    while i < how_many:
        lots.append(threading.Thread(target=process_words, args=(main_list_of_words[0:how_many], lofs, list_of_results,)))
        i += num_words
    # starting thread 1 and 2
    for t in lots:
        t.start()
    # counter
    start = time.time()
    last_count = 0
    ongoing = True
    last_num_dead = 0
    while ongoing:
        ongoing = False
        num_dead = 0
        for t in lots:
            if t.is_alive():
                ongoing = True
            else:
                num_dead += 1
        if time.time() - start > 10:
            start = time.time()
            print(f"Gone through {count} words so far. Rate is about {int((count - last_count) / 10)} words/sec")
            last_count = count

            if num_dead != last_num_dead:
                print(f"{num_dead} / {num_threads} threads finished btw - {int(time.time() - real_start)} seconds")
                last_num_dead = num_dead

    # wait until thread 1 and 2 are completely executed
    for t in lots:
        t.join()

    print(f"We counted {count} attempts when running together")
    print(f"{english_found} / {english_found + english_not_found} entries had english sections")
    print(f"{len(list_of_results)} / {english_found} entries had pronunciations listed")
    print(f"  Informational : {code_results['1']}\n"
          f"  Successful : {code_results['2']}\n"
          f"  Redirection : {code_results['3']}\n"
          f"  Client Error : {code_results['4']}\n"
          f"  Server Error : {code_results['5']}\n  ")
    print(f"took {int(time.time() - real_start)} seconds")

    i = 0
    while i < how_many:
        if words_as_read[i] != main_list_of_words[i]:
            print(f"{i}: {words_as_read[i]} vs {main_list_of_words[i]}")
        i += 1
    print(f"We had {len(lofs)} failures")
    print("all done!")


run_thru(5, 100000)

#2326 failures on 10000, 3348
