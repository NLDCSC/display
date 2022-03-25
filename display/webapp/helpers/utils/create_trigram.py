import random
import string
import time

from trigram.webapp.app.models import names
from trigram.webapp.run import db


def check_trigram(trigram):

    stored_trigram = names.query.filter(names.trigram == trigram).first()

    if stored_trigram is None:
        return True

    return False


def check_name(name):

    stored_name = names.query.filter(names.name == name).first()

    if stored_name is None:
        return True

    return False


def create_trigram_entry(name, trigram, status):
    new_name = names(
        name=name, trigram=trigram, status=status, created=int(time.time())
    )

    db.session.add(new_name)
    db.session.commit()

    return True


def create_trigrams_from_list(name_process_list):

    new = 0

    if isinstance(name_process_list, list):

        for name in sorted(name_process_list):

            # normalize name
            name = name.lower()

            if check_name(name):

                name_list = name.split(" ")

                # Default trigram, 1 letter firstname, 2 letters lastname
                if len(name_list) == 2:
                    trigram = f"{name_list[0][:1]}{name_list[1][:2]}".upper()
                else:
                    trigram = f"{name_list[0][:1]}{name_list[-1][:2]}".upper()

                if check_trigram(trigram):
                    # new entry with free trigram, create it...
                    create_trigram_entry(name=name, trigram=trigram, status=0)
                    new += 1
                else:
                    # conflicting trigram, try 2 letters firstname, 1 letter lastname
                    if len(name_list) == 2:
                        trigram = f"{name_list[0][:2]}{name_list[1][:1]}".upper()
                    else:
                        trigram = f"{name_list[0][:2]}{name_list[-1][:1]}".upper()

                    if check_trigram(trigram):
                        create_trigram_entry(name=name, trigram=trigram, status=1)
                        new += 1
                    else:
                        # right; lets create random trigram from the letters in the name
                        name_letters = name.replace(" ", "")
                        # try 10 loops
                        x = 0
                        got_trigram = False
                        while x < 10:
                            trigram = "".join(
                                random.choice(name_letters) for _ in range(3)
                            )

                            if check_trigram(trigram):
                                create_trigram_entry(
                                    name=name, trigram=trigram.upper(), status=2
                                )
                                new += 1
                                got_trigram = True
                                break

                            x += 1

                        # F..k!, still no trigram; creating something totally random....
                        if not got_trigram:
                            name_letters = string.ascii_lowercase

                            while True:
                                trigram = "".join(
                                    random.choice(name_letters) for _ in range(3)
                                )

                                if check_trigram(trigram):
                                    create_trigram_entry(
                                        name=name, trigram=trigram.upper(), status=3
                                    )
                                    new += 1
                                    break

        return f"{len(name_process_list)} names processed! --> New entries: {new}"

    else:
        raise TypeError(
            f"Wrong type supplied, expecting: for {type(name_process_list)}"
        )
