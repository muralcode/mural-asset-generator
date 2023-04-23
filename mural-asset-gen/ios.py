"""
iOS-specific processing required for app white-labelling an application go in this file.

This file contains the Ios Platform class, which is subclassed from the MobilePlatform class.
All functions related to the iOS platform operations are contained in the Ios class. Helper functions
are typically outside the class.
"""

import json
import os
from abc import ABCMeta
from collections import OrderedDict
from xml.etree import ElementTree

import shell_commands
import git_operations
import asset_gen_tools
from ios_common import IOS_STRINGS, IOS_STRINGS_DIR, IOS_LAUNCHER, LAUNCHER_CONTENTS, IOS_LAUNCHER_DIR, \
    IOS_COMMON_MODULE_IMAGE, IOS_OUTPUT_DIR, FA_IOS_RESERVED_WORDS, FA_IOS_LAUNCHER_DENSITIES, \
    FA_IOS_IMAGE_DENSITIES, FA_IOS_WELCOME_SCREEN_DENSITIES, FA_ICON_DENSITIES, FA_NAV_ICON_DENSITIES, \
    FA_AUX_IMAGE_DENSITIES, FA_QR_FRAME_DENSITIES, FA_SBE_DENSITIES, FA_IOS_DEFAULTS_DIR, FA_IOS_VECTORS_DIR, \
    FA_INFOPLIST_STRINGS_CONFIG_FILE, IOS_LOCALIZABLE_STRINGS_DIR, IOS_INFOPLIST_FILE, \
    IOS_BASE_LOCALIZABLE_STRINGS_DIR, IOS_BASE_STRINGS, IOS_FAQS_FILENAME
from ios_swift import Swift
from mobileplatform import MobilePlatform
from platforms_common import SHARED_DIR, OUTPUT_DIR, FINANCIAL_APP_WELCOME_IMAGES, \
    FINANCIAL_APP_ALL_COMMON_IMAGES_DIR, FINANCIAL_APP_DEF_LOCALISATION, FINANCIAL_APP_BUILD_FLAG_MUTEXES

INFO = {'version': 1, 'author': 'xcode'}
IMAGES_SOURCE = IOS_COMMON_MODULE_IMAGE


class Ios(MobilePlatform):
    """
    A class used to represent a Mobile Platform file processing operations, and in this case, iOS-specific
    processing (Localizable.strings for localisations, png processing for images, etc).

    Attributes
    ----------
    none

    Methods
    -------
    finish()
        Cleanup call, last function called.
    create_notify_icons(command, input_path)
        Creates the notification icons for Android
    copy_defaults()
        Copies the default android assets into the output folder structure.
    process_localizations(lang, strings, default)
        Process the data.json file into multiple strings.xml files.
    save_faqs(lang, output, default)
        Processes the FAQ blocks of data.json into faqs.json
    create_launcher_icons(command, input_path)
        Creates the launcher icons of various densities.
    create_image(command, input_path, image)
        Creates/processes all images given from config.
    create_other_images(command)
        Creates/processes aux images given from config.
    save_colors(colors)
        Save color information to colors.xml file.
    copy_values()
        Helper, not inherited, called by copy_defaults()
    copy_welcome_screen(input_paths, image)
        Copies the welcome screen images to the correct location.
    save_build_system_files()
        Creates files used by the build system to build white-labelled/flavoured apps.
    create_welcome_screens(client, color_primary, color_secondary)
        Creates welcome screens according to default images and color schemes of the client.
    add_dict_values(key, value, dictionary_data)
        Builds up a dictionary (unique set) of string key/value pairs.
    image_loop(command, input_path, densities, idiom, swift)
        Sequence of procedures to execute on every image.
    fmt_lang(lang)
        Format the language code to a format that iOS will accept.
    """
    __metaclass__ = ABCMeta

    def __init__(self, client_data):
        super().__init__(client_data)

        self.reserved = asset_gen_tools.get_json_array_from_file(FA_IOS_RESERVED_WORDS, "data")

        self.swift = Swift()

    def copy_defaults(self):
        """
        :return: nothing
        """
        self.copy_values()

    def process_localizations(self, lang, strings, default):
        """
        :param lang: language being considered
        :param strings: the strings of aforementioned language
        :param default: indication of whether or not the passed language is considered the default for this app
        :return: nothing
        """
        file_path = os.path.dirname(os.path.realpath(__file__))
        if file_path != os.getcwd():
            os.chdir(file_path)

        # Determine the relevant file path to be written (language dependent)
        dictionary_lang = lang
        lang = self.format_language(lang)

        output_kv_path = IOS_STRINGS.format(lang=lang)

        json_languages = asset_gen_tools.read(os.path.join(file_path, FINANCIAL_APP_DEF_LOCALISATION))
        json_languages_dictionary = json.loads(json_languages)["languages"]
        json_by_language = json_languages_dictionary[dictionary_lang]

        # prepare empty dictionary
        data = dict()

        for key, value in json_by_language.items():
            self.add_dict_values(key, value, data)

        output = ''

        for name, text in strings:
            self.add_dict_values(name, text, data)

        # populate the InfoPlist Localizable strings files.
        self.process_infoplist_strings_localised(data, lang, default)

        # Check mutexes
        asset_gen_tools.check_string_mutexes(["privacy_policy", "privacy_policy_url"], data, lang,
                                             FINANCIAL_APP_BUILD_FLAG_MUTEXES)

        asset_gen_tools.check_string_mutexes(["terms_and_conditions", "terms_and_conditions_url"], data, lang,
                                             FINANCIAL_APP_BUILD_FLAG_MUTEXES)

        # create file output from dictionary
        for key, val in data.items():
            self.swift.append_string(key)
            try:
                output += '"{0}" = "{1}";\n'.format(key, val)
            except UnicodeDecodeError as main_exception:
                print("key: {}".format(key))
                print("val: {}".format(val))
                raise RuntimeError("There is a problem with the input encoding") from main_exception

        try:
            asset_gen_tools.save(output_kv_path, output)
            if lang.startswith("en"):
                output_kv_path = IOS_BASE_STRINGS
                asset_gen_tools.save(output_kv_path, output)
        except UnicodeDecodeError as main_exception:
            print("path: {}".format(output_kv_path))
            print(output)
            raise RuntimeError("There is a problem with the input encoding") from main_exception

    def process_infoplist_strings_localised(self, data, lang, default):
        """
        :param data: the string data in a dictionary
        :param lang: the language being processed
        :param default: indication of whether or not the passed language is considered the default for this app
        :return: nothing
        """
        mapping = asset_gen_tools.get_json_array_from_file(FA_INFOPLIST_STRINGS_CONFIG_FILE, "data")
        # print(mapping)
        output = ""
        path = IOS_LOCALIZABLE_STRINGS_DIR.format(lang=lang)
        for entry in mapping:

            for key, value in entry.items():
                value_expanded = data[value]

                # If the expanded value is empty for app_name, populate from targets
                if len(value_expanded) is 0:
                    self.swift.append_infoplist_string(value, key, lang)
                    continue

                line = "\"{}\" = \"{}\";\n".format(key, value_expanded)
                output = output + line

        real_path = IOS_INFOPLIST_FILE.format(path=path)
        asset_gen_tools.save(real_path, output)
        if default:
            real_path = IOS_INFOPLIST_FILE.format(path=IOS_BASE_LOCALIZABLE_STRINGS_DIR)
            asset_gen_tools.save(real_path, output)

    def add_dict_values(self, key, value, dictionary_data):
        """
        :param key: the dictionary key
        :param value: the value linked to the dictionary key
        :param dictionary_data: the dictionary containing the result data
        :return: nothing
        """
        # add suffix for reserved words
        if key in self.reserved:
            key += "_string"

        # add suffix for short words (linting rules)
        if len(key) < 3:
            key += "_string"

        # Escape double quotes and newlines
        value = value.replace('"', '\\"').replace('\n', '\\n').replace("'", "\\'")

        dictionary_data[key] = value

    def save_faqs(self, lang, faqs, default):
        """
        :param lang: the language being processed
        :param faqs: the faqs for this language
        :param default: indication of whether or not the passed language is considered the default for this app
        :return: nothing
        """
        lang = self.format_language(lang)
        path = IOS_LOCALIZABLE_STRINGS_DIR.format(lang=lang)
        real_path = os.path.join(path, IOS_FAQS_FILENAME)
        asset_gen_tools.save(real_path, faqs)
        if default:
            real_path = os.path.join(IOS_BASE_LOCALIZABLE_STRINGS_DIR, IOS_FAQS_FILENAME)
            asset_gen_tools.save(real_path, faqs)

    def save_colors(self, colors):
        """
        :param colors: the color codes for skinning the app
        :return: nothing
        """
        for key, string in colors.items():
            color = '0x' + string.lstrip('#')
            self.swift.append_color(key, color)

    def create_launcher_icons(self, command, input_path):
        """
        :param command: the command line to use when running image creation process
        :param input_path: input image to be used
        :return: nothing
        """
        sizes = asset_gen_tools.get_json_array_from_file(FA_IOS_LAUNCHER_DENSITIES, "data")
        temp_out = os.path.join(OUTPUT_DIR, "temp_ios")
        for size in sizes:
            output = os.path.join(temp_out, str(size) + '.png')
            asset_gen_tools.resize_image(command, input_path, output, size)

            output_path = IOS_LAUNCHER.format(size=size)
            asset_gen_tools.convert_flatten_image(shell_commands.IMAGE_MAGICK_FLATTEN_COMMAND, output, output_path)

        asset_gen_tools.copy(LAUNCHER_CONTENTS, IOS_LAUNCHER_DIR.format(client=self.client))

    def create_image(self, command, input_path, image):
        """
        :param command: the command line to use when running image creation process
        :param input_path: input image to be used
        :param image: which image in the set is being produced
        :return: nothing
        """
        output_densities = asset_gen_tools.get_json_array_from_file(FA_IOS_IMAGE_DENSITIES, "data")

        i = 0
        final_path = ""
        for image_path in IMAGES_SOURCE:
            output_path = image_path.format(image=image)
            asset_gen_tools.resize_image(command, input_path, output_path, output_densities[i])
            i = i + 1
            final_path = output_path

        create_image_content_json(image, os.path.dirname(final_path), i)

    def create_other_images(self, command):
        """
        :param command: the command line to use when running image creation process
        :return: nothing
        """
        icon_densities = asset_gen_tools.get_json_array_from_file(FA_ICON_DENSITIES, "data")
        nav_icon_densities = asset_gen_tools.get_json_array_from_file(FA_NAV_ICON_DENSITIES, "data")
        aux_image_densities = asset_gen_tools.get_json_array_from_file(FA_AUX_IMAGE_DENSITIES, "data")
        qr_frame_density = asset_gen_tools.get_json_array_from_file(FA_QR_FRAME_DENSITIES, "data")
        sbe_density = asset_gen_tools.get_json_array_from_file(FA_SBE_DENSITIES, "data")

        file_path = os.path.dirname(os.path.realpath(__file__))
        if file_path != os.getcwd():
            os.chdir(file_path)

        ios_vectors_path = os.path.join(file_path, FA_IOS_VECTORS_DIR)
        icons_path = os.path.join(ios_vectors_path, 'icons')
        nav_icons_path = os.path.join(ios_vectors_path, 'nav_icons')
        others_path = os.path.join(ios_vectors_path, 'other')
        common_images_path = os.path.join(file_path, FINANCIAL_APP_ALL_COMMON_IMAGES_DIR)

        icons = os.listdir(icons_path)
        nav_icons = os.listdir(nav_icons_path)
        others = os.listdir(others_path)
        commons = os.listdir(common_images_path)
        universal_idiom = 'universal'

        for icon in icons:
            self.image_loop(command, icons_path + "/" + icon, icon_densities, universal_idiom, self.swift)

        for nav_icon in nav_icons:
            self.image_loop(command, nav_icons_path + "/" + nav_icon, nav_icon_densities, universal_idiom, self.swift)

        for other in others:
            self.image_loop(command, others_path + "/" + other, aux_image_densities, universal_idiom, self.swift)

        for common in commons:
            if 'qr' in common:
                self.image_loop(shell_commands.IMAGE_MAGICK_COMMAND, common_images_path + "/" + common,
                                qr_frame_density, universal_idiom, self.swift)
            if 'secured' in common:
                self.image_loop(shell_commands.IMAGE_MAGICK_COMMAND, common_images_path + "/" + common, sbe_density,
                                universal_idiom, self.swift)

    def image_loop(self, command, input_path, densities, idiom, swift):
        """
        :param command: the command line to use when running image creation process
        :param input_path: input image to be used
        :param densities: list of image densities to be created (for different mobile screen sizes/pixel densities)
        :param idiom: for which device is it being made (mac/iphone/ipad/universal)
        :param swift: instance object of the swift class (ios_swift.py)
        :return: nothing
        """
        i = 0
        final_path = ""
        image_temp = os.path.basename(input_path).split(".")
        if len(image_temp) < 2:
            return
        if len(image_temp[0]) < 1:
            return
        if len(image_temp[1]) > 4:
            return
        image = image_temp[0]

        for image_path in IMAGES_SOURCE:
            output_path = image_path.format(image=image)
            asset_gen_tools.resize_image(command, input_path, output_path, densities[i])
            i = i + 1
            final_path = output_path

        create_image_content_json(image, os.path.dirname(final_path), i, idiom)

        swift.append_image(image)

    def copy_welcome_screen(self, input_paths, image):
        """
        :param input_paths: input images to be used
        :param image: which image in the set is being produced
        :return: nothing
        """
        density_track = 0
        final_path = ""
        final_real_image = ""

        for input_path, real_image in input_paths:
            if density_track > len(IMAGES_SOURCE) - 1:
                create_image_content_json(final_real_image, os.path.dirname(final_path), density_track)
                density_track = 0

            output_path = IMAGES_SOURCE[density_track].format(image=real_image)
            asset_gen_tools.copy(input_path, output_path)
            density_track += 1
            final_path = output_path
            final_real_image = real_image

        create_image_content_json(final_real_image, os.path.dirname(final_path), density_track)

    def finish(self):
        """
        :return: nothing
        """

    def create_notify_icons(self, command, input_path):
        """
        :param command: the command line to use when running image creation process
        :param input_path: input image to be used
        :return:
        """
        print("iOS not implemented")

    def copy_values(self):
        """
        :return: nothing
        """
        file_path = os.path.dirname(os.path.realpath(__file__))
        if file_path != os.getcwd():
            os.chdir(file_path)

        if not os.path.exists(IOS_STRINGS_DIR.format(client=self.client) + '/'):
            asset_gen_tools.copytree(os.path.join(file_path, FA_IOS_DEFAULTS_DIR),
                                     IOS_STRINGS_DIR.format(client=self.client) + '/')
            print("Done copying iOS defaults")

    def format_language(self, lang):
        """
        :param lang: language being considered
        :return: formatted language
        """
        dashes = lang.count('-')
        formatted_language = lang
        if dashes > 0:
            parts = lang.split('-')
            formatted_language = parts[0] + '-' + parts[1].upper()
        return formatted_language

    def save_build_system_files(self):
        """
        :return: nothing
        """
        self.swift.parse_targets()

    def create_welcome_screens(self, client, color_primary, color_secondary):
        """
        :param client: client name
        :param color_primary: primary color code
        :param color_secondary: secondary color code
        :return: paths to created images
        """
        images = asset_gen_tools.get_json_array_from_file(FINANCIAL_APP_WELCOME_IMAGES, "data")

        input_path = os.path.join(SHARED_DIR, '{image}.svg')
        temp_path = os.path.join(OUTPUT_DIR, 'temp_' + client, "{image}.svg")
        unformatted_output_paths = [os.path.join(OUTPUT_DIR, 'temp_ios_1x_' + client, "{image}.png"),
                                    os.path.join(OUTPUT_DIR, 'temp_ios_2x_' + client, "{image}.png"),
                                    os.path.join(OUTPUT_DIR, 'temp_ios_3x_' + client, "{image}.png")]

        output_densities = asset_gen_tools.get_json_array_from_file(FA_IOS_WELCOME_SCREEN_DENSITIES, "data")

        paths = []

        for image in images:
            i = 0
            for unformatted_output_path in unformatted_output_paths:
                temp_path = temp_path.format(image=image)
                output_path = unformatted_output_path.format(image=image)
                with open(input_path.format(image=image), 'r') as welcome_file:
                    welcome = welcome_file.read().replace("#DD4814", color_primary).replace("#002244", color_secondary)
                    asset_gen_tools.save(temp_path, welcome)
                    asset_gen_tools.resize_image(shell_commands.INKSCAPE_COMMAND, temp_path, output_path,
                                                 output_densities[i])
                paths.append([output_path, image])
                i = i + 1

        return paths


def create_image_content_json(image_name, path, total, idiom='universal'):
    """
    :param image_name: name of image that content is being created for
    :param path: path to image
    :param total:
    :param idiom:
    :return:
    """
    output = ''
    image = [OrderedDict() for _ in range(total)]

    for scale_in_range in range(total):
        if scale_in_range is 0:
            image_file = '{image}.png'.format(image=image_name)
        else:
            image_file = '{image}@{scale}x.png'.format(image=image_name, scale=scale_in_range + 1)
        scale = '{sX}x'.format(sX=scale_in_range + 1)

        image[scale_in_range] = OrderedDict([('idiom', idiom),
                                             ('filename', image_file),
                                             ('scale', scale)])

    content = {'images': image, 'info': INFO}
    output = output + json.dumps(content, indent=2)
    output = output.replace(', ', ',').replace('":', '" :').replace(':"', ': "')

    path = os.path.join(path, 'Contents.json')
    asset_gen_tools.save(path, output)


def save_git_info():
    """
    :return:
    """
    plist = ElementTree.Element('plist', {'version': '1.0'})
    dict_element = ElementTree.SubElement(plist, 'dict')

    ElementTree.SubElement(dict_element, 'key').text = 'commit_count'
    ElementTree.SubElement(dict_element, 'string').text = str(git_operations.get_commit_count())

    ElementTree.SubElement(dict_element, 'key').text = 'commit_hash'
    ElementTree.SubElement(dict_element, 'string').text = git_operations.get_hash()

    output = asset_gen_tools.prettify(plist, '    ')
    path = os.path.join(IOS_OUTPUT_DIR, 'AssetsVersion.plist')
    asset_gen_tools.save(path, output)
