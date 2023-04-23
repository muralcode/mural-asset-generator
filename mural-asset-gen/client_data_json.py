"""
Author/Engineer: Lerato Mokoena

This file houses the code class ClientData, and its purpose is to convert client input from JSON format into usable
data structures for white-labelling apps.
"""
import json

VERSION_KEY = 'version'
LANGUAGES_KEY = 'languages'
DEFAULT_LANG_KEY = 'default_language'
STRINGS_KEY = 'app_strings'
LANGUAGE_KEY = 'language'
FAQS_KEY = 'faqs'
FAQ_TITLE_KEY = 'question'
FAQ_TEXT_KEY = 'answer'
COLORS_KEY = 'app_colors'
IMAGES_TYPE_KEY = 'app_images'


class ClientData:
    """
    A class used to extract client-supplied values from a JSON file.

    Attributes
    ----------
    none

    Methods
    -------
    get_strings()
        getter that returns the client strings loaded from JSON in __init__
    get_faqs()
        getter that returns the client faqs loaded from JSON in __init__
    get_colors()
        getter that returns the client colors loaded from JSON in __init__
    get_name()
        getter that returns the name we use for the client
    def get_version()
    --- Deprecated
        getter that returns the resources version loaded from JSON in __init__
    def get_image_types()
        getter that returns the image types loaded from JSON in __init__
    """
    def __init__(self, path_to_file, client):
        file_pointer = open(path_to_file)
        dict_json = json.load(file_pointer)
        print('Loaded JSON from file: "{0}"'.format(path_to_file))
        self.version = dict_json[VERSION_KEY]
        self.strings = _load_strings(dict_json, client)
        self.faqs = _load_faqs(dict_json, client)
        self.colors = _load_colors(dict_json, client)
        self.name = client
        self.image_types = dict_json[IMAGES_TYPE_KEY]

    def get_strings(self):
        """
        :return: localisation strings
        """
        return self.strings

    def get_faqs(self):
        """
        :return: client frequently asked questions
        """
        return self.faqs

    def get_colors(self):
        """
        :return: client color scheme
        """
        return self.colors

    def get_name(self):
        """
        :return: name of the client
        """
        return self.name

    def get_version(self):
        """
        :return: version from json file, now unused/non-existent
        """
        return self.version

    def get_image_types(self):
        """
        :return: list of image types to be processed for this client
        """
        return self.image_types


def _load_strings(dict_json, client):
    """
    :param dict_json: the dictionary where the strings are located
    :param client: the client
    :return: the localised strings
    """
    if dict_json[LANGUAGES_KEY] is None:
        print('No key named "{0}" was found, strings files not created for "{1}"'.format(LANGUAGES_KEY, client))
        return None

    localised_strings = []
    default_lang = dict_json[DEFAULT_LANG_KEY]
    for language_entry in dict_json[LANGUAGES_KEY]:
        lang = language_entry[LANGUAGE_KEY]
        strings_list = []
        for name, text in language_entry[STRINGS_KEY].items():
            text = text.strip() if text is not None else ''
            strings_list.append((name, text))
        localised_strings.append((lang, strings_list, default_lang == lang))
    return localised_strings


def _load_faqs(dict_json, client):
    """
    :param dict_json: the dictionary where the faqs are located
    :param client: the client
    :return: the localised faqs
    """
    if dict_json[LANGUAGES_KEY] is None:
        print('No key named "{0}" was found, faq files not created for "{1}"'.format(LANGUAGES_KEY, client))
        return None

    localised_faqs = []
    default_lang = dict_json[DEFAULT_LANG_KEY]
    for language_entry in dict_json[LANGUAGES_KEY]:
        lang = language_entry[LANGUAGE_KEY]
        faqs_list = []
        for faq_entry in language_entry[FAQS_KEY]:
            if faq_entry[FAQ_TITLE_KEY] is None:
                break
            title = faq_entry[FAQ_TITLE_KEY].strip()
            text = faq_entry[FAQ_TEXT_KEY]
            faqs_list.append((title, text))
        localised_faqs.append((lang, faqs_list, default_lang == lang))
    return localised_faqs


def _load_colors(dict_json, client):
    """
    :param dict_json: the dictionary where the colors are located
    :param client: the client
    :return: the color schemes of the app
    """
    if dict_json[COLORS_KEY] is None:
        print('No key named "{0}" was found, color files not created for "{1}"'.format(COLORS_KEY, client))
        return None

    colors = {}
    color_entry = dict_json[COLORS_KEY]
    for name, text in color_entry.items():
        if name is not None:
            text = text if text is not None else ''
            colors[name] = text
    return colors
