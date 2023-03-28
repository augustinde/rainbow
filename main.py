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
salt_len = 4
total_reductions = 100

file_csv_rainbow = "rainbow_table.csv"
file_txt_match = "match_password.txt"
file_txt_start_words = "words_ccm_2023.txt" #"words_brute.txt"
file_txt_hash = "hash_challenges.txt"

# Keep track of lines written to rainbow table file
total_lines = 0
current_line = 0
current_rainbow_table = 0
def md5(input: str) -> str:
    return hashlib.md5(input.encode()).hexdigest()


def elapsed(func: Callable) -> Callable:    # Callable c'est juste le function Type en python
    def wrapper(*args, **kwargs):
        start = time.time_ns()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time_ns() - start}ns")
        return result
    return wrapper


def salting(word: str) -> str:
    nums = "".join([str(i) for i in range(pass_len)])
    indices = []
    for i in range(salt_len):
        digit = random.choices(nums, k=1)[0]
        nums = nums.replace(digit, "")
        indices += digit
    indices.sort(reverse=True)
    salt = random.choices("0123456789", k=salt_len)
    for i, v in enumerate(indices):
        word = word[:int(v)] + salt[i] + word[int(v):]
    return word


def deterministic_salting(word: str, hash: str) -> str:
    # Take salt_len * 2 first digits from hash
    salt_len_first_digits = "".join([c if c.isdigit() else "" for c in hash])[:salt_len*2]
    salt = salt_len_first_digits[:salt_len]
    indices = list(map(lambda x: int(x) % pass_len, salt_len_first_digits[salt_len:]))
    indices.sort(reverse=True)
    for i, v in enumerate(indices):
        word = word[:int(v)] + salt[i] + word[int(v):]
    return word


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
    temp = (int(hash, 16) + i) % (26 ** 6)       # apply reduction (returns integer)
    result = []
    for j in range(pass_len):
        result += chars[temp % chars_len]
        temp //= chars_len
    return deterministic_salting("".join(result), hash)


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
    global total_lines
    global current_line
    with open(file_txt_start_words, "r") as fr, open(file_csv_rainbow, "w") as fw:
        while True:
            line = fr.readline().strip()
            current_line += 1
            if not line:
                break
            fw.write(generate_chain(line) + "\n")
            total_lines += 1
            pretty_print()
            # print(line.strip())


def generate_chain(start_word: str) -> str:
    start_word = salting(start_word)
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
    """

    """
    global  current_rainbow_table
    current_rainbow_table += 1

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
    global current_line
    with open(file_txt_hash, "r") as fr:
        while True:
            hash = fr.readline().strip()
            current_line += 1
            if not hash:
                break
            result = reverse_lookup(hash)
            if result is not None:
                print(f"Found match for : {hash} = {result}")
            else:
                pretty_print()


def pretty_print() -> None:
    #total_single_chain_reductions = total_reductions * (1 + total_reductions) // 2
    #total = total_single_chain_reductions * total_lines
    #progress = total_lines * current_line + total_single_chain_reductions * current_rainbow_table
    print(f"Current line : {current_line:02d}", end="\r")
    #print(f"\rCurrent line : {current_line} | Current rainbow table : {current_rainbow_table} "
     #     f"| Progress : {progress / total * 100:02f}")

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
    #print("Generate brute force")
    #generate_bruteforce()
    # generate_start_words(1_000_000)
    print("Generate chains")
    generate_chains()
    current_line = 0
    print("Crack password")
    crack_password()
