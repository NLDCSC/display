import secrets
import string


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
