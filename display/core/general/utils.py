import secrets
import string
from collections import defaultdict


def generate_random_password():
    # define the alphabet
    letters = string.ascii_letters
    digits = string.digits

    alphabet = letters + digits

    # fix password length
    pwd_length = 32

    # generate a password string
    pwd = ""
    for i in range(pwd_length):
        pwd += "".join(secrets.choice(alphabet))

    return pwd


def exclude_optional_dict(value):
    return value is None or not value


def defaultdict_to_regular(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_regular(v) for k, v in d.items()}
    return d


def chunks(a: list, n: int):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))
