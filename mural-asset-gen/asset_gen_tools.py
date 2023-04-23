"""
This file houses a collection of tool functions. It is a utility collection.
"""
from __future__ import unicode_literals

import json
import os
import shlex
import shutil
import subprocess
from xml.dom import minidom
from xml.etree import ElementTree
from zipfile import ZipFile

import sys

import shell_commands

FILE_NOT_FOUND = "{path} not found"
IS_WIN = (sys.platform == 'win32')


def prettify(elem, indent):
    """
    :param elem: the XML element
    :param indent: string of indentation spaces
    :return: a pretty-printed XML string for the Element
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent)


def read(path):
    """
    :param path: path to file that will be read
    :return: contents of the file
    """
    create_needed_dirs(path)
    with open(path, "r") as input_file:
        content = input_file.read()
        return content


def read_lines(path):
    """
    :param path: path to file that will be read
    :return: contents line by line as an array
    """
    create_needed_dirs(path)
    with open(path, "r") as input_file:
        content = input_file.readlines()
        return content


def save(path, output):
    """
    :param path: path to file that will be saved
    :param output: the process output that will be written to file
    :return: nothing
    """
    create_needed_dirs(path)
    with open(path, "w") as output_file:
        try:
            output_file.write(output)
        except UnicodeEncodeError:
            output_file.write(output.encode('utf-8'))


def save_lines(path, output):
    """
    :param path: path to file that will be saved
    :param output: the process output as an array of lines to be saved
    :return: nothing
    """
    create_needed_dirs(path)
    with open(path, "w") as output_file:
        try:
            output_file.writelines("%s" % line for line in output)
        except UnicodeEncodeError:
            output_file.writelines(output.encode('utf-8'))


def zip_directory(path):
    """
    :param path: directory to be zipped
    :return: nothing
    """
    with ZipFile("{0}.zip".format(path), "w") as output_file:
        for root, _, files in os.walk(path):
            for my_file in files:
                output_file.write(os.path.join(root, my_file), os.path.join(remove_prefix(root, path), my_file))
    shutil.rmtree(path)


def file_exist(path):
    """
    :param path: path to file
    :return: bool, true if exists, false if not
    """
    return file_exist_custom_error(path, FILE_NOT_FOUND.format(path=path))


def file_exist_silent(path):
    """
    :param path: path to file
    :return: bool, true if exists, false if not
    """
    return file_exist_custom_error(path, None)


def file_exist_custom_error(path, error_message):
    """
    :param path: path to file
    :param error_message: error message to be printed to log
    :return: bool, true if exists, false if not
    """
    if os.path.isfile(path):
        return True
    else:
        if error_message is not None:
            print(error_message)
        return False


def resize_image(command_string, input_path, output_path, size):
    """
    :param command_string: commandline to be executed
    :param input_path: the file to be converted
    :param output_path: the path where the output should be written
    :param size: image size for the output image
    :return: nothing
    """
    create_needed_dirs(output_path)
    command = shlex.split(command_string.format(input=input_path, size=size, output=output_path))
    subprocess.check_output(command, env=shell_commands.ENV)


def convert_flatten_image(command_string, input_path, output_path):
    """
    :param command_string: image flatten command
    :param input_path: file to be flattened
    :param output_path: path to write flattened file to
    :return: nothing
    """
    create_needed_dirs(output_path)
    command = shlex.split(command_string.format(input=input_path, output=output_path))
    subprocess.check_output(command, env=shell_commands.ENV)


def copy(input_path, output_path, print_path=False):
    """
    :param input_path: file to copy
    :param output_path: where file will be copied to
    :param print_path: whether or not to print the the directory in the output path
    :return: nothing
    """
    create_needed_dirs(output_path)
    shutil.copy(input_path, output_path)

    if print_path:
        the_idx = output_path.rfind('/')
        the_dir = output_path[:the_idx]
        print('The Dir: \n{0}'.format(os.listdir(the_dir)))


def create_needed_dirs(path):
    """
    :param path: the path
    :return: nothing
    """
    path_dir = os.path.dirname(path)
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)


def remove_prefix(text, prefix):
    """
    :param text: the string containing a prefix to be removed
    :param prefix: the prefix to be removed
    :return: the text with prefix removed
    """
    return text[len(prefix) + 1:] if text.startswith(prefix) else text


def copytree(src, dst, symlinks=False, ignore=None):
    """
    :param src: source tree to copy
    :param dst: destination to copy to
    :param symlinks: whether symlinks should be followed
    :param ignore: silences exceptions around dangling symlinks
    :return: nothing
    """
    create_needed_dirs(dst)
    for item in os.listdir(src):
        source = os.path.join(src, item)
        destination = os.path.join(dst, item)

        if os.path.isdir(source):
            shutil.copytree(source, destination, symlinks, ignore)
        else:
            shutil.copy2(source, destination)


def get_json_array_from_file(file, data_tag):
    """
    :param file: file to read
    :param data_tag: tag to parse
    :return: file contents as array of values
    """
    json_data = read(file)
    json_dictionary = json.loads(json_data)
    return json_dictionary[data_tag]


# Utility wrapper to make return type more explicit to readers of the code.
def get_json_dictionary_from_file(file, data_tag):
    """
    :param file: file to read
    :param data_tag: tag to parse
    :return: file contents as json dictionary
    """
    return get_json_array_from_file(file, data_tag)


def to_camel_case(snake_str):
    """
    :param snake_str: input string in snake case
    :return: output string in camel case
    """
    components = snake_str.split('_')
    return components[0].lower() + ''.join(x.title() for x in components[1:])


def get_build_config_mutex_id_dict(file, data_tag):
    """
    :param file: the file location where the mutexes are defined
    :param data_tag: the root tag of the json file
    :return: dictionary of mutex names with associated ids
    """
    mutex_ids_by_key = dict()
    mutex_configs = get_json_array_from_file(file, data_tag)

    for mutex_config in mutex_configs:
        mutex_ids_by_key[mutex_config["name"]] = mutex_config["mutex_id"]

    return mutex_ids_by_key


def get_mutexes_by_id(mutex_id, file, data_tag):
    """
    :param mutex_id: the integer id that uniquely identifies the mutex
    :param file: the file location where the mutexes are defined
    :param data_tag: the root tag of the json file
    :return: array of incompatible config mutex ids
    """
    mutex_configs = get_json_array_from_file(file, data_tag)
    for mutex_config in mutex_configs:
        if mutex_id == mutex_config["mutex_id"]:
            return mutex_config["mutex_with"]


def get_mutex_name_from_id(mutex_id, file, data_tag):
    """
    :param mutex_id: the integer id that uniquely identifies the mutex
    :param file: the file location where the mutexes are defined
    :param data_tag: the root tag of the json file
    :return: the mutex config that matches the supplied ID
    """
    mutex_configs = get_json_array_from_file(file, data_tag)
    for mutex_config in mutex_configs:
        if mutex_id == mutex_config["mutex_id"]:
            return mutex_config["name"]


def check_string_mutexes(mutex_tags, strings, lang, file):
    """
    :param mutex_tags: tags being evaluated
    :param strings: localisation strings
    :param lang: language
    :param file: the file location where the mutexes are defined
    :return: nothing
    """
    # Dictionary of mutexed feature names with associated ids
    mutex_id_dict = get_build_config_mutex_id_dict(file, "data")
    active_components = []
    for tag, value in strings.items():
        if tag in mutex_tags:
            if tag in mutex_id_dict:
                if len(value) > 0:
                    active_components.append(mutex_id_dict[tag])

    if len(active_components) == 0:
        print("A configuration anomaly has been detected.")
        print(f"Some required strings are empty. Check {mutex_tags} strings")
        message = "Check app localisation {lang}."
        message = message.format(lang=lang)
        print(message)
        raise ValueError('Required strings missing from data.json')

    # Check if any of the active components are in conflict with any of the other active components
    for active_component in active_components:
        mutexes = get_mutexes_by_id(active_component, file, "data")
        for mutex in mutexes:
            if mutex in active_components:
                print("A configuration anomaly has been detected.")
                print("Mutually exclusive build system strings have been given values.")
                message = "Check strings {bf_one} and {bf_two} for language {lang}"

                build_flag_one = get_mutex_name_from_id(active_component,
                                                        file,
                                                        "data")

                build_flag_two = get_mutex_name_from_id(mutex,
                                                        file,
                                                        "data")
                message = message.format(bf_one=build_flag_one,
                                         bf_two=build_flag_two,
                                         lang=lang)
                print(message)
                raise ValueError('Incompatible build configurations in data.json file')


def check_app_location_flags(app_components, flavour_name, file):
    """
    :param app_components: list of build flags specified for this flavour
    :param flavour_name: name of the flavour
    :param file: the file location where the mutexes are defined
    :return: nothing
    """
    # Dictionary of mutexed feature names with associated ids
    mutex_id_dict = get_build_config_mutex_id_dict(file, "data")
    active_components = []
    for attribute, value in app_components.items():
        if attribute == 'geo_location':
            for each in value:
                for sub_attribute, sub_value in each.items():
                    if sub_value:
                        # Build a list of components to be enable in the app
                        active_components.append(mutex_id_dict[sub_attribute])

    if len(active_components) == 0:
        print("A configuration anomaly has been detected.")
        print("No geo-location mechanism enabled.")
        message = "Check app variant {variant}."
        message = message.format(variant=flavour_name)
        print(message)
        raise ValueError('No geo-location mechanism enabled in targets file')

    # Check if any of the active components are in conflict with any of the other active components
    for active_component in active_components:
        mutexes = get_mutexes_by_id(active_component, file, "data")
        for mutex in mutexes:
            if mutex in active_components:
                print("A configuration anomaly has been detected.")
                print("Mutually exclusive build system flags have been enabled.")
                message = "Check app variant {variant} for flags {bf_one} and {bf_two}"
                build_flag_one = get_mutex_name_from_id(active_component,
                                                        file,
                                                        "data")
                build_flag_two = get_mutex_name_from_id(mutex,
                                                        file,
                                                        "data")
                message = message.format(variant=flavour_name,
                                         bf_one=build_flag_one,
                                         bf_two=build_flag_two)
                print(message)
                raise ValueError('Incompatible build configurations in targets file')
    return active_components


def check_app_registration_flags(app_components, flavour_name, file):
    """
    :param app_components: list of build flags specified for this flavour
    :param flavour_name: name of the flavour
    :param file: the file location where the mutexes are defined
    :return: nothing
    """
    # Dictionary of mutexed feature names with associated ids
    mutex_id_dict = get_build_config_mutex_id_dict(file, "data")
    active_components = []
    for attribute, value in app_components.items():
        if attribute == 'registration':
            for each in value:
                for sub_attribute, sub_value in each.items():
                    if sub_value:
                        # Build a list of components to be enable in the app
                        active_components.append(mutex_id_dict[sub_attribute])

    if len(active_components) == 0:
        print("A configuration anomaly has been detected.")
        print("No registration mechanism enabled. App will be useless.")
        message = "Check app variant {variant}."
        message = message.format(variant=flavour_name)
        print(message)
        raise ValueError('No registration mechanism enabled in targets file')

    # Check if any of the active components are in conflict with any of the other active components
    for active_component in active_components:
        mutexes = get_mutexes_by_id(active_component, file, "data")
        for mutex in mutexes:
            if mutex in active_components:
                print("A configuration anomaly has been detected.")
                print("Mutually exclusive build system flags have been enabled.")
                message = "Check app variant {variant} for flags {bf_one} and {bf_two}"
                build_flag_one = get_mutex_name_from_id(active_component,
                                                        file,
                                                        "data")
                build_flag_two = get_mutex_name_from_id(mutex,
                                                        file,
                                                        "data")
                message = message.format(variant=flavour_name,
                                         bf_one=build_flag_one,
                                         bf_two=build_flag_two)
                print(message)
                raise ValueError('Incompatible build configurations in targets file')


def check_call_support_flags(app_components, flavour_name, call_support_strings_all_present):
    """
    :param app_components: list of build flags specified for this flavour
    :param flavour_name: name of the flavour
    :param call_support_strings_all_present: pre-parsed boolean that encompasses all call support strings over all
           translations
    :return: nothing
    """
    check_support_flags(app_components, flavour_name, call_support_strings_all_present, "include_call_support")


def check_email_support_flags(app_components, flavour_name, email_support_strings_all_present):
    """
    :param app_components: list of build flags specified for this flavour
    :param flavour_name: name of the flavour
    :param email_support_strings_all_present: pre-parsed boolean that encompasses all email support strings over all
           translations
    :return: nothing
    """
    check_support_flags(app_components, flavour_name, email_support_strings_all_present, "include_email_support")


def check_support_flags(app_components, flavour_name, all_strings_present, check):
    """
    :param app_components: list of build flags specified for this flavour
    :param flavour_name: name of the flavour
    :param all_strings_present: pre-parsed boolean that encompasses all email/call support strings over all
           translations
    :param check: which build-attribute to check
    :return: nothing
    """
    for attribute, value in app_components.items():
        if attribute == check:
            if value is True:
                if not all_strings_present:
                    print("A configuration anomaly has been detected.")
                    print("Support feature enabled, but some strings not present.")
                    message = "Check app variant {variant} for flag \"{check}\""
                    message = message.format(variant=flavour_name,
                                             check=check)
                    print(message)
                    raise ValueError('Missing SUPPORT localisation data.')


def consolidate_build_flags(defaults_in, specifics_in):
    """
    :param defaults_in: defaults in targets.json
    :param specifics_in: specifics for the target under consideration
    :return: nothing
    """
    # defaults will have all items supported.
    # iterate through defaults and see if specifics contain it
    # if not, add the default.
    for attribute, value in defaults_in.items():
        # Check if specifics contain this item
        specific_items = specifics_in.keys()
        if attribute not in specific_items:
            # if not, we add it
            specifics_in[attribute] = value
            continue
        if attribute == 'registration':  # value will be an array of single-item dictionaries
            # also get from specifics
            registration_block = specifics_in["registration"]  # same as attribute == registration
            for each in value:  # for each single-item dictionary
                for sub_attribute, sub_value in each.items():  # extract the single key with value
                    found = False
                    # Run through the specifics, check against the defaults
                    for sub_dict in registration_block:
                        for sub_attr_compare, _ in sub_dict.items():
                            if sub_attribute == sub_attr_compare:
                                found = True
                                break
                        if found:
                            break
                    if not found:  # If no specific is found matching the default, add it
                        item = dict()
                        item[sub_attribute] = sub_value
                        specifics_in["registration"].append(item)


def add_manifest_permission(path, permission, output_path):

    manifest = read_lines(path)
    insert_at = 0

    split_count = 0
    if path != output_path:
        split_count = 1

    for line in manifest:
        if "uses-permission" in line:
            before = manifest[:insert_at]
            after = manifest[insert_at+split_count:]
            new_manifest = before
            new_manifest.append(permission)
            new_manifest = new_manifest + after
            break
        else:
            insert_at = insert_at + 1
    save_lines(output_path, new_manifest)
