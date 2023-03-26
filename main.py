from typing import Callable
import hashlib
import os
import random
import string
import time

random.seed(1)

chars = "abcdefghijklmnopqrstuvwxyz"
chars_len = len(chars)
pass_len = 6
hash_len = 32
hash_bits = 128
total_reductions = 3

file_csv_rainbow = "rainbow_table.csv"
file_txt_match = "match_password.txt"
file_txt_start_words = "words_brute.txt"
file_txt_hash = "hash_challenges.txt"


def md5(input: str) -> str:
    return hashlib.md5(input.encode()).hexdigest()


def elapsed(func: Callable) -> Callable:    # Callable c'est juste le function Type en python
    def wrapper(*args, **kwargs):
        start = time.time_ns()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time_ns() - start}ns")
        return result
    return wrapper


######################
# Reduction function #
######################

def r(hash: str, i: int) -> str:
    """
    Generic and parametrized reduction function that's unique to each
    column in each chain. Uses the hash to get a unique result inside
    possible password search space:
        alphabet_len    = 26 (since [a-z])
        pass_len        = 6
        search space cardinality = 26**6
    """
    hash = int(hash, 16)                # convert hash to hex integer
    temp = (hash + i) % (26 ** 6)       # apply reduction (returns integer)
    return hex(temp).split('x')[-1]     # convert to hex again and remove leading "0x"


def forward_reductions_word(start_word: str, reductions: int = total_reductions) -> str:
    """
    Applies reductions to start_word based off of total_reductions
    in this order: [R1, R2, R3, ... , Rtotal_reductions]

    Here's an example for total_reductions of 3:
                H       R1      H       R2      H       R3
    start_word  ->  h1  ->  r1  ->  h2  ->  r2  ->  h3  ->  r3  = end_word

    :param start_word
    :param reductions
    :return: end_word
    """
    temp = start_word
    for i in range(reductions):
        digest = md5(temp)
        temp = r(digest, i)
    return temp


#################
# Rainbow table #
#################

def generate_chains() -> None:
    with open(file_txt_start_words, "r") as fr, open(file_csv_rainbow, "w") as fw:
        while True:
            line = fr.readline().strip()
            if not line:
                break
            fw.write(generate_chain(line) + "\n")
            # print(line.strip())


def generate_chain(start_word: str) -> str:
    end_word = forward_reductions_word(start_word)
    return f"{start_word},{end_word}"


def lookup_chain(start_word: str, hash: str) -> str:
    temp = start_word
    for i in range(total_reductions):
        digest = md5(temp)
        if digest == hash:
            return temp
        temp = r(digest, i)


def reverse_lookup_generic(hash: str, reverse_reductions: list[int]) -> str:
    """
    hash -> r3
         -> r2 -> hash -> r3
         -> r1 -> hash -> r2 -> hash -> r3
    """
    digest = hash
    for reduction in reverse_reductions:
        temp = r(digest, reduction)
        digest = md5(temp)

    with open(file_csv_rainbow, "r") as fr:
        while True:
            line = fr.readline().strip()
            if not line:
                break
            line_split = line.split(",")

            if temp == line_split[1]:
                password = lookup_chain(line_split[0], hash)
                if password is not None:
                    return password


def reverse_lookup(hash) -> str:
    # lookups = [[r3], [r2, r3], [r1, r2, r3]]
    lookups = []
    for i in range(total_reductions):
        rlist = []
        for j in range(total_reductions - 1 - i, total_reductions):
            rlist.append(j)
        lookups.append(rlist)

    for lookup in lookups:
        result = reverse_lookup_generic(hash, lookup)
        if result is not None:
            with open(file_txt_match, "a") as fw:
                fw.write(hash + " = " + result + "\n")
            return result


def crack_password() -> None:
    with open(file_txt_hash, "r") as fr:
        while True:
            line = fr.readline().strip()
            if not line:
                break
            result = reverse_lookup(line)
            if result is not None:
                print(result)
            else:
                print("No password in table")


######################
# Wordlist functions #
######################

def generate_start_words(total: int) -> None:
    with open(file_txt_start_words, "w") as fw:
        for i in range(total):
            fw.write(''.join(random.choices(string.ascii_lowercase, k=6)) + "\n")


def generate_bruteforce():
    with open(file_txt_start_words, "w") as fw:
        for i in chars:
            for j in chars:
                for k in chars:
                    for l in chars:
                        for m in chars:
                            for n in chars:
                                result = i + j + k + l + m + n
                                fw.write(result + "\n")

###############
# Driver Code #
###############

if __name__ == '__main__':
    if os.path.exists(file_txt_match):
        os.remove(file_txt_match)
    print("Generate brute force")
    generate_bruteforce()
    #generate_start_words(1_000_000)
    # TODO run before you sleep!
    print("Generate chains")
    generate_chains()
    print("Crack password")
    crack_password()
    # print(r3("c5f0d8ce7ba4b986f7480681f52c0f4b"))
