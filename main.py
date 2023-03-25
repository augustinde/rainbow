import hashlib
import random
import string
import time

random.seed(1)

chars="abcdefghijklmnopqrstuvwxyz"
chars_len = len(chars)
pass_len = 6
hash_len = 32
hash_bits = 128

def md5(input):
    return hashlib.md5(input.encode()).hexdigest()

def elapsed(func):
    def wrapper(*args, **kwargs):
        start = time.time_ns()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time_ns() - start}ns")
        return result
    return wrapper

def r1(hash):
    result = ""
    offset = random.randint(0, chars_len)
    for i in range(pass_len):
        pos = random.randint(0, hash_len)
        result += hash[(offset+pos) % hash_len]
    return result

def r2(hash):
    result = ""
    offset = random.randint(0, chars_len)
    for i in range(pass_len):
        pos = random.randint(0, hash_len)
        result += chars[int(hash[(offset + pos) % hash_len], 16) % chars_len]
    return result

def r3(hash):
    result = ""
    offset = random.randint(0, chars_len)
    for i in range(pass_len):
        pos = random.randint(0, hash_len)
        result += hash[((pos+offset) ^ 0xD34D833F)**69 % hash_len]
    return result

def generate_chains():
    #words_ccm_2023
    with open("words_brute.txt", "r") as fr, open("rainbow_table.csv", "w") as fw:
        while True:
            line = fr.readline().strip()
            if not line:
                break
            fw.write(generate_chain(line) + "\n")
            #print(line.strip())

def generate_chain(word):
    """
    Generates a chain following this algorithm:
                H       R1      H       R2      H       R3
    start_word  ->  h1  ->  r1  ->  h2  ->  r2  ->  h3  ->  r3  = end_word
    """
    temp = md5(word)
    reductions = [r1, r2, r3]
    reductions_len = len(reductions)
    i = 0
    for r in reductions:
        temp = r(temp)
        if i < reductions_len - 1:
            temp = md5(temp)
        i += 1
    return f"{word},{temp}"


def lookup_chain(start_word, hash):
    temp = start_word
    for reduction in [r1, r2, r3]:
        digest = md5(temp)
        if digest == hash:
            return temp
        temp = reduction(digest)
    return None

def lookup_generic(hash, reverse_reductions):
    """
    hash -> r3
         -> r2 -> hash -> r3
         -> r1 -> hash -> r2 -> hash -> r3
    """
    digest = hash
    for reduction in reverse_reductions:
        temp = reduction(digest)
        digest = md5(temp)

    with open("rainbow_table.csv", "r") as fr:
        while True:
            line = fr.readline().strip()
            if not line:
                break
            line_split = line.split(",")

            if temp == line_split[1]:
                password = lookup_chain(line_split[0], hash)
                if password is not None:
                    return password

def lookup(hash):
    lookups = [[r3], [r2, r3], [r1, r2, r3]]

    for lookup in lookups:
        result = lookup_generic(hash, lookup)
        if result is not None:
            with open("match_password.txt", "w") as fw:
                fw.write(hash + " = " + result + "\n")
            return result
    return None

def crack_password():
    with open("hash_challenges.txt", "r") as fr:
        while True:
            line = fr.readline().strip()
            if not line:
                break
            result = lookup(line)
            if result is not None:
                print(result)
            else:
                print("No password in table")

def generate_start_words(total):
    with open("words.txt", "w") as fw:
        for i in range(total):
            fw.write(''.join(random.choices(string.ascii_lowercase, k=6)) + "\n")


def generate_bruteforce():
    with open("words_brute.txt", "w") as fw:
        for i in chars:
            for j in chars:
                for k in chars:
                    for l in chars:
                        for m in chars:
                            for n in chars:
                                result = i + j + k + l + m + n
                                fw.write(result + "\n")


if __name__ == '__main__':
    generate_bruteforce()
    #generate_start_words(1_000_000)
    # TODO run before you sleep!
    generate_chains()
    crack_password()
    #print(r3("c5f0d8ce7ba4b986f7480681f52c0f4b"))
