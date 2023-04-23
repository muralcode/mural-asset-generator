"""
Author/Engineer: Lerato Mokoena

This file houses helper functions for ios_xcconfig.py
"""

def process_list(key, body, content_template, list_in, tracking_set):
    """
    :param key: the key in the dictionary that had a list for a value
    :param body: the body string blob containing output
    :param content_template: the content template for output file body entries
    :param list_in: the list to be processed
    :param tracking_set: set of values used to build up unique list for plist
    :return: the modified body blob
    """
    # We declare a counter
    body += content_template.substitute(key="{}_{}".format(key.upper(), "COUNT"),
                                        value=len(list_in)) + "\n"

    tracking_set.add("{}_{}".format(key.upper(), "COUNT"))
    tracking_set.add("{}".format(key.upper()))

    counter = 1
    # We process the contents of the list, with a counter appended after each
    for value in list_in:
        final_value = handle_bool_as_string(value)
        body += content_template.substitute(key="{}_{}".format(key.upper(), counter),
                                            value=final_value) + "\n"
        counter += 1
    return body


def process_dict(body, dict_in, content_template, tracking_set):
    """
    :param body: the body string blob containing output
    :param dict_in: the dictionary to be processed
    :param content_template: the content template for output file body entries
    :param tracking_set: set of values used to build up unique list for plist
    :return: the modified body blob
    """
    for key, value in dict_in.items():
        tracking_set.add(key.upper())
        final_value = handle_bool_as_string(value)
        body += content_template.substitute(key=key.upper(),
                                            value=final_value) + "\n"
    return body


def handle_bool_as_string(value):
    """
    :param value: either string, bool, or nothing
    :return: cleaned up value, swift compatible
    """
    final_value = "false"
    if isinstance(value, bool):
        if value:
            final_value = "true"

    else:
        final_value = value

    return final_value
