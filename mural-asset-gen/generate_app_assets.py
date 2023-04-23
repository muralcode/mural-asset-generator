"""
Author/Engineer: Lerato Mokoena

This is the main entrypoint file for app white-labelling of asset packs for the FinancialApp-iOS by Arurea Murals.
"""
import json
import os
import shutil

import ios
import shell_commands
import asset_gen_tools
from android import Android
from client_data_json import ClientData
from environmentals import get_environ_val
from ios import Ios
from ios_common import IOS_APP_MODULE_IMAGE, IOS_COMMON_MODULE_IMAGE

from ios_swift import Swift
from platforms_common import OUTPUT_DIR, CLIENT_DATA_FILE, IMAGE, AUTH_APP_WELCOME_IMAGES, AUTH_APP_IMAGES

FAQ_TITLE = 'title'
FAQ_TEXT = 'text'
FAQ_ITEMS = 'items'

SVG = 'svg'
PNG = 'png'
WEBP = "webp"

SWIFT = Swift()


def main():
    """
    :return: nothing
    """

    client_key = get_environ_val('CLIENT_KEY')
    platform = get_environ_val('PLATFORM')

    print('printing: "{0}"'.format(client_key))
    print('printing: "{0}"'.format(platform))
    print('Starting up')
    file_path = os.path.dirname(os.path.realpath(__file__))
    if file_path != os.getcwd():
        os.chdir(file_path)

    shutil.rmtree(OUTPUT_DIR, True)

    process_client(client_key, platform)

    print('All done')


def process_client(client, platform):
    """
    :param client: client name
    :param platform: Android or iOS
    :return: nothing
    """
    print('Processing client data: "{0}"'.format(client))
    client_data = ClientData(CLIENT_DATA_FILE.format(client=client), client)

    platforms = [Android(client_data), Ios(client_data)]
    temp_platform_variable = str.upper(platform)
    print(temp_platform_variable)
    if 'ALL' not in temp_platform_variable:
        if 'ANDROID' in temp_platform_variable:
            print("Platform {} only".format(temp_platform_variable))
            platforms = [Android(client_data)]
        elif 'IOS' in temp_platform_variable:
            print("Platform {} only".format(temp_platform_variable))
            platforms = [Ios(client_data)]
        else:
            print("Platform {} not supported".format(platform))
            raise Exception("Platform not supported.")
    else:
        print("ALL Platforms")

    copy_defaults(platforms)
    create_strings_files(platforms, client_data)
    create_faqs(platforms, client_data)
    create_launcher_icons(platforms, client_data)
    create_notify_icons(platforms, client_data)
    create_colors(platforms, client_data)
    create_images(platforms, client_data)
    generate_build_system_files(platforms)
    finish(platforms)
    print('Done with client data')
    print('------------------------------------')


def copy_defaults(platforms):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :return: nothing
    """
    for platform in platforms:
        platform.copy_defaults()


def create_strings_files(platforms, client_data):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :param client_data: the client-provided data, strings, faqs, colors, and images
    :return: nothing
    """
    print('Create strings files...')
    for lang, strings, is_default in client_data.get_strings():
        for platform in platforms:
            platform.process_localizations(lang, strings, is_default)
            if isinstance(platform, ios.Ios):
                SWIFT.write_out_strings()


def create_faqs(platforms, client_data):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :param client_data: the client-provided data, strings, faqs, colors, and images
    :return: nothing
    """
    print('Create FAQs ...')
    for lang, faqs_list, is_default in client_data.get_faqs():
        lst = []
        for title, text in faqs_list:
            faq = {FAQ_TITLE: title, FAQ_TEXT: text}
            lst.append(faq)

        output = json.dumps({FAQ_ITEMS: lst}, indent=2)

        for platform in platforms:
            platform.save_faqs(lang, output, is_default)


def create_launcher_icons(platforms, client_data):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :param client_data: the client-provided data, strings, faqs, colors, and images
    :return: nothing
    """
    print('Create launcher icons...')
    image = 'launcher'
    client = client_data.get_name()
    image_types = client_data.get_image_types()
    image_type = image_types[image]

    if image_type == SVG:
        svg_file = IMAGE.format(client=client, ext=SVG, image=image)
        for platform in platforms:
            platform.create_launcher_icons(shell_commands.INKSCAPE_SQUARE_COMMAND, svg_file)
    elif image_type == PNG:
        png_file = IMAGE.format(client=client, ext=PNG, image=image)
        for platform in platforms:
            platform.create_launcher_icons(shell_commands.IMAGE_MAGICK_SQUARE_COMMAND, png_file)


def create_notify_icons(platforms, client_data):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :param client_data: the client-provided data, strings, faqs, colors, and images
    :return: nothing
    """
    print('Create notify icons...')
    image = 'notify'
    client = client_data.get_name()
    image_types = client_data.get_image_types()
    image_type = image_types[image]

    if image_type == SVG:
        svg_file = IMAGE.format(client=client, ext=SVG, image=image)
        for platform in platforms:
            platform.create_notify_icons(shell_commands.INKSCAPE_SQUARE_COMMAND, svg_file)
    elif image_type == PNG:
        png_file = IMAGE.format(client=client, ext=PNG, image=image)
        for platform in platforms:
            platform.create_notify_icons(shell_commands.IMAGE_MAGICK_SQUARE_COMMAND, png_file)


def create_images(platforms, client_data):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :param client_data: the client-provided data, strings, faqs, colors, and images
    :return: nothing
    """
    images = asset_gen_tools.get_json_array_from_file(AUTH_APP_IMAGES, "data")
    if 'welcome_1' in client_data.get_image_types():
        extended_images = asset_gen_tools.get_json_array_from_file(AUTH_APP_WELCOME_IMAGES, "data")
        images.extend(extended_images)

    print('Create ' + ','.join(images) + ' icons...')
    client = client_data.get_name()
    image_types = client_data.get_image_types()

    for image in images:
        image_type = image_types[image]
        command = ""
        if image_type == SVG:
            command = shell_commands.INKSCAPE_COMMAND
        elif image_type == PNG:
            command = shell_commands.IMAGE_MAGICK_COMMAND
        handle_image(client, platforms, image_type, image, command)
    for platform in platforms:
        platform.create_other_images(shell_commands.INKSCAPE_COMMAND)
        if isinstance(platform, ios.Ios):
            SWIFT.write_out_images()


def handle_image(client, platforms, image_type, image, command):
    """
    :param client: name of the client
    :param platforms: platforms to be processed, Android, iOS, or both
    :param image_type: SVG, PNG, WEBP
    :param image: image variant being processed
    :param command: command to be used for processing the image
    :return: nothing
    """
    image_file = IMAGE.format(client=client, ext=image_type, image=image)
    for platform in platforms:
        platform.create_image(command, image_file, image)
        if isinstance(platform, ios.Ios):
            # also add launch screen image
            if image == "home":
                ios.IMAGES_SOURCE = IOS_APP_MODULE_IMAGE
                new_image_file = IMAGE.format(client=client, ext=image_type, image="launch")
                shutil.copyfile(image_file, new_image_file)
                image_file = IMAGE.format(client=client, ext=image_type, image="launch")
                platform.create_image(command, image_file, "launch")
                SWIFT.append_image("launch")
                ios.IMAGES_SOURCE = IOS_COMMON_MODULE_IMAGE
            SWIFT.append_image(image)


def create_colors(platforms, client_data):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :param client_data: the client-provided data, strings, faqs, colors, and images
    :return: nothing
    """
    print('Create color files...')
    colors = client_data.get_colors()

    for platform in platforms:
        platform.save_colors(colors)
        if isinstance(platform, ios.Ios):
            SWIFT.write_out_colors()

    if 'welcome_1' not in client_data.get_image_types():
        for platform in platforms:
            welcome_paths = platform.create_welcome_screens(client_data.get_name(), colors['primary'],
                                                            colors['secondary'])
            platform.copy_welcome_screen(welcome_paths, None)
        SWIFT.append_image('image_1')
        SWIFT.append_image('image_2')
        SWIFT.append_image('image_3')


def generate_build_system_files(platforms):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :return: nothing
    """
    print('Create build system files...')
    for platform in platforms:
        platform.save_build_system_files()


def finish(platforms):
    """
    :param platforms: platforms to be processed, Android, iOS, or both
    :return: nothing
    """
    file_path = os.path.dirname(os.path.realpath(__file__))
    if file_path != os.getcwd():
        os.chdir(file_path)
    print("------------ CLEANUP --------------")
    directories = os.listdir(os.path.join(file_path, OUTPUT_DIR))
    for directory in directories:
        if directory.startswith("temp_"):
            print("removing... {}".format(directory))
            shutil.rmtree(os.path.join(file_path, OUTPUT_DIR, directory))
    for platform in platforms:
        platform.finish()


if __name__ == "__main__":
    main()
