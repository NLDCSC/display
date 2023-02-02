import calendar
from datetime import datetime


def timestringTOtimestamp(timestring):
    """
    Method to convert a given date time string into a timestamp. Timestring is matched to the date_time_formats
    'date time string formats' list. If matched will return a timestamp integer; will return False otherwise.

    :param timestring: date time string
    :type timestring: str
    :return: unix timestamp
    :rtype: int
    """

    date_time_formats = [
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%H:%M:%S %d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S,%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S,%fZ",
    ]

    match = False

    # try to match string formats to given string
    for each in date_time_formats:
        try:
            match = datetime.strptime(timestring, each)
        except ValueError:
            continue

    if match:
        match = calendar.timegm(match.utctimetuple())

    return match


def datetimeTOtimestamp(date_time_object):
    return calendar.timegm(date_time_object.utctimetuple())


def dateTOtimestamp(date_time_object):
    return calendar.timegm(date_time_object.timetuple())


def timestampTOdatetime(timestamp):
    """
    Method that will take the provided timestamp and converts it into a date time object

    :param timestamp: unix timestamp
    :type timestamp: int
    :return: date time object
    :rtype: datetime
    """
    value = datetime.utcfromtimestamp(timestamp)

    return value


def timestampTOdatestring(timestamp):
    """
    Method that will take the provided timestamp and converts it into a date time string

    :param timestamp: unix timestamp
    :type timestamp: int
    :return: date time object
    :rtype: datetime.datetime (format: '%d-%m-%Y')
    """
    value = datetime.utcfromtimestamp(timestamp)

    return value.strftime("%d-%m-%Y")


def timestampTOdatetimestring(timestamp, vis=False):
    """
    Method that will take the provided timestamp and converts it into a RFC3339 date time string

    :param timestamp: unix timestamp
    :type timestamp: int
    :return: date time object
    :rtype: datetime.datetime (format: '%d-%m-%YT%H:%M:%SZ')
    """
    value = datetime.utcfromtimestamp(timestamp)

    if not vis:
        return value.strftime("%d-%m-%YT%H:%M:%SZ")
    else:
        return value.strftime("%Y-%m-%d %H:%M:%S")
