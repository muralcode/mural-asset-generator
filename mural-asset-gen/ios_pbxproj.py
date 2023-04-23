"""
This file houses functionality related to processing of the pbxproj project file found in iOS projects
"""
import os
from string import Template

import asset_gen_tools

from ios_common import AA_IOS_PBXPROJ, AA_IOS_PBXPROJ_OUT, AA_IOS_TEMPLATES_DIR
from ios_pbxproj_helper import update_config_name, insert_new_config, build_reference_map, \
    process_config_list_id_line, find_next_config_list_start, produce_uuid, find_next_config_end

IOS_TARGETS_PATH = os.path.join("{path}", "targets")
IOS_TEMPLATES_PATH = os.path.join("{path}", AA_IOS_TEMPLATES_DIR)


class PbxProj:
    """
    A class used to process the iOS pbxproj file.

    Attributes
    ----------
    none

    Methods
    -------
    read_file(path=AA_IOS_PBXPROJ)
        reads the pbxproj file into memory
    get_build_file_line_start(pbxproj_contents, tag, start=0)
        get the first line of the build files config segment
    get_build_file_line_end(pbxproj_contents, tag, start=0)
        get the last line of the build files config segment
    duplicate_xc_build_configuration(new_config_names, file_content)
        creates duplicates of Debug and Release configs and allocates them to flavours
    update_configuration_lists(uuid_map_of_maps, file_content)
        add new configs to the config lists
    add_config_file_to_build_file_section(file_name, pbxproj_content)
        name is self-explanitory
    add_file_to_file_ref_section(file_name, pbxproj_content, uuid_map)
        name is self-explanitory
    add_file_to_pbx_group_section(file_name, pbxproj_content, uuid_map)
        name is self-explanitory
    add_file_to_pbx_resources_build_phase_section(file_name, pbxproj_content, uuid_map)
        name is self-explanitory
    link_scheme_to_base_build_ref(file_name, pbxproj_content, uuid_map, uuid_map_of_maps)
        name is self-explanitory
    """
    def __init__(self):
        self.file_path = os.path.dirname(os.path.realpath(__file__))
        if self.file_path != os.getcwd():
            os.chdir(self.file_path)

        self.templates_path = IOS_TEMPLATES_PATH.format(path=self.file_path)

        self.build_file_content_template_file = asset_gen_tools.read(
            os.path.join(self.templates_path, 'build_file_section_content_template.pbxproj'))
        self.file_ref_content_template_file = asset_gen_tools.read(
            os.path.join(self.templates_path, 'file_ref_section_content_template.pbxproj'))
        self.base_conf_ref_content_template_file = asset_gen_tools.read(
            os.path.join(self.templates_path, 'base_config_reference_template.pbxproj'))

        self.build_file_content_template = Template(self.build_file_content_template_file)
        self.file_ref_content_template = Template(self.file_ref_content_template_file)
        self.base_conf_ref_content_template = Template(self.base_conf_ref_content_template_file)

    def read_file(self, path=AA_IOS_PBXPROJ):
        """
        :param path: relative path to the file that will be read
        :return: the contents of the file, line by line in a list of lines.
        """
        pbxproj_path = os.path.join(self.file_path, path)
        pbxproj_contents = asset_gen_tools.read_lines(pbxproj_path)
        return pbxproj_contents

    @staticmethod
    def get_build_file_line_start(pbxproj_contents, tag, start=0):
        """
        :param pbxproj_contents: line by line list of the pbxproj file content
        :param tag: the c-style comment that marks the starting point of the data sought after
        :param start: offset into the buffer
        :return: the line where the tag was found, -1 if not found
        """
        build_line_start = 0

        for pbxproj_line in pbxproj_contents:
            # if a custom starting line was given
            if start != 0:
                # and we are not currently on that line:
                if build_line_start != start:
                    # increment line counter
                    build_line_start = build_line_start + 1
                    # and restart loop
                    continue
            pbxproj_line = pbxproj_line.strip('\n')

            if pbxproj_line == tag:
                return build_line_start + 1
            build_line_start = build_line_start + 1
        return -1

    @staticmethod
    def get_build_file_line_end(pbxproj_contents, tag, start=0):
        """
        :param pbxproj_contents: line by line list of the pbxproj file content
        :param tag: the c-style comment that marks the end point of the data sought after
        :param start: offset into the buffer
        :return: the line where the tag was found, -1 if not found
                """
        build_line_end = 0

        for pbxproj_line in pbxproj_contents:
            # if a custom starting line was given
            if start != 0:
                # and we are not currently on that line:
                if build_line_end != start:
                    # increment line counter
                    build_line_end = build_line_end + 1
                    # and restart loop
                    continue
            pbxproj_line = pbxproj_line.strip('\n')
            if pbxproj_line == tag:
                return build_line_end
            build_line_end = build_line_end + 1
        return -1

    def duplicate_xc_build_configuration(self, new_config_names, file_content):
        """
        :param new_config_names: list of config names, e.g Torvalds_731
        :param file_content: list of lines in the project.pbxproj file
        :return: map of uuid maps, mapped by target
        """

        # Find the 'Begin XCBuildConfiguration section' tag
        first_line = self.get_build_file_line_start(file_content, "/* Begin XCBuildConfiguration section */")

        # Find the 'End XCBuildConfiguration section' tag
        last_line = self.get_build_file_line_end(file_content, "/* End XCBuildConfiguration section */")

        # Reduce data to only lines in XCBuildConfiguration section
        lines = file_content[first_line:last_line]

        line_number = 0

        # uuid_map = dict()
        uuid_map_of_maps = dict()
        new_lines = []

        for new_config_name in new_config_names:

            uuid_map = build_reference_map(lines, line_number, dict())

            uuid_map_of_maps[new_config_name] = uuid_map

            new_lines = update_config_name(lines, new_config_name, new_lines)

        file_content = insert_new_config(first_line, new_lines, file_content)

        asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), file_content)

        return uuid_map_of_maps

    def update_configuration_lists(self, uuid_map_of_maps, file_content):
        """
        :param uuid_map_of_maps: map of uuid maps, mapped by target
        :param file_content: list of lines in the project.pbxproj file
        :return: nothing
        """

        # Find the 'Begin XCConfigurationList section' tag
        first_line = self.get_build_file_line_start(file_content, "/* Begin XCConfigurationList section */")

        # Find the 'End XCConfigurationList section' tag
        last_line = self.get_build_file_line_end(file_content, "/* End XCConfigurationList section */")

        before = file_content[:first_line]
        after = file_content[last_line:]

        # Reduce data to only lines in XCConfigurationList section
        lines = file_content[first_line:last_line]

        for uuid_map_tuple in uuid_map_of_maps.items():
            new_config_name = uuid_map_tuple[0]
            uuid_map = uuid_map_tuple[1]
            line_number = find_next_config_list_start(lines, 0)

            has_next_config_list = True
            if line_number < 0:
                has_next_config_list = False

            while has_next_config_list:

                module = process_config_list_id_line(line_number, lines)

                debug_key = module + ".debug"
                release_key = module + ".release"

                if debug_key not in uuid_map:
                    print("Key missing from UUID map.")
                    print("DEBUG KEY: {}".format(debug_key))
                    print("UUID MAP: {}".format(uuid_map))
                    raise ValueError('The memory map of modules was poorly populated.')

                if release_key not in uuid_map:
                    print("Key missing from UUID map.")
                    print("RELEASE KEY: {}".format(release_key))
                    print("UUID MAP: {}".format(uuid_map))
                    raise ValueError('The memory map of modules was poorly populated.')

                debug_uuid = uuid_map[debug_key]
                release_uuid = uuid_map[release_key]
                debug_line = "\t\t\t\t" + debug_uuid + " /* " + new_config_name + "Debug" + " */,\n"
                release_line = "\t\t\t\t" + release_uuid + " /* " + new_config_name + "Release" + " */,\n"

                line_number = line_number + 3
                lines.insert(line_number, debug_line)
                lines.insert(line_number + 1, release_line)

                line_number = find_next_config_list_start(lines, line_number)
                if line_number < 0:
                    has_next_config_list = False

        new_file_content = before
        new_file_content.extend(lines)
        new_file_content.extend(after)

        asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), new_file_content)

    def add_config_file_to_build_file_section(self, file_name, pbxproj_content):
        """
        :param file_name: the name of the file to add a reference for
        :param pbxproj_content: the content of the pbxproj file
        :return: the uuids created for build reference and file reference
        """
        # Find the 'Begin PBXBuildFile section' tag
        first_line = self.get_build_file_line_start(pbxproj_content, "/* Begin PBXBuildFile section */")

        build_ref_uuid = produce_uuid()
        file_ref_uuid = produce_uuid()

        build_config_line = self.build_file_content_template.substitute(build_ref_uuid=build_ref_uuid,
                                                                        file_ref_uuid=file_ref_uuid,
                                                                        file_name=file_name)

        pbxproj_content = insert_new_config(first_line, build_config_line, pbxproj_content)
        asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), pbxproj_content)
        build_ref_to_file_ref_map = dict()
        build_ref_to_file_ref_map[build_ref_uuid] = file_ref_uuid
        return build_ref_to_file_ref_map

    def add_file_to_file_ref_section(self, file_name, pbxproj_content, uuid_map):
        """
        :param file_name: the name of the file to add a reference for
        :param pbxproj_content: the content of the pbxproj file
        :param uuid_map: the uuids created for build reference and file reference
        :return: nothing
        """
        # Find the 'Begin PBXFileReference section' tag
        first_line = self.get_build_file_line_start(pbxproj_content, "/* Begin PBXFileReference section */")

        uuid_to_use = ""

        for _, file_ref_uuid in uuid_map.items():
            uuid_to_use = file_ref_uuid
            break

        if "xcconfig" in file_name:
            file_name = os.path.join("Config", file_name)

        file_ref_line = self.file_ref_content_template.substitute(file_ref_uuid=uuid_to_use,
                                                                  file_name=file_name)

        pbxproj_content = insert_new_config(first_line, file_ref_line, pbxproj_content)
        asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), pbxproj_content)
        return pbxproj_content

    def add_file_to_pbx_group_section(self, file_name, pbxproj_content, uuid_map):
        """
        :param file_name: the name of the file to add a reference for
        :param pbxproj_content: the content of the pbxproj file
        :param uuid_map: the uuids created for build reference and file reference
        :return: nothing
        """
        # Find the 'Begin PBXGroup section' tag
        first_line = self.get_build_file_line_start(pbxproj_content, "/* Begin PBXGroup section */")

        line_number = 0
        goto_line = first_line

        uuid_to_use = ""

        for _, file_ref_uuid in uuid_map.items():
            uuid_to_use = file_ref_uuid
            break

        # We are looking for the default group, it has no annotation, so if a group has an annotation, we skip it.
        for line in pbxproj_content:
            if goto_line == line_number:
                if "/*" in line:
                    goto_line = find_next_config_end(pbxproj_content, line_number+1) + 1
                    line_number += 1
                    continue
                else:
                    pbx_group_line = "\t\t\t\t{} /* {} */,\n".format(uuid_to_use, file_name)
                    pbxproj_content = insert_new_config(line_number + 3, pbx_group_line, pbxproj_content)
                    asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), pbxproj_content)

                    break
            else:
                line_number += 1
        return pbxproj_content

    def add_file_to_pbx_resources_build_phase_section(self, file_name, pbxproj_content, uuid_map):
        """
        :param file_name: the name of the file to add a reference for
        :param pbxproj_content: the content of the pbxproj file
        :param uuid_map: the uuids created for build reference and file reference
        :return: nothing
        """
        # Find the 'Begin PBXResourcesBuildPhase section' tag
        first_line = self.get_build_file_line_start(pbxproj_content, "/* Begin PBXResourcesBuildPhase section */")

        line_number = 0
        goto_line = first_line

        uuid_to_use = ""

        for build_ref_uuid, _ in uuid_map.items():
            uuid_to_use = build_ref_uuid
            break

        for line in pbxproj_content:
            if goto_line == line_number:
                if "/* LaunchScreen.storyboard in Resources */" not in line:
                    line_number += 1
                    goto_line += 1
                    continue
                else:
                    pbx_group_line = "\t\t\t\t{} /* {} in Resources */,\n".format(uuid_to_use, file_name)
                    pbxproj_content = insert_new_config(line_number, pbx_group_line, pbxproj_content)
                    asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), pbxproj_content)

                    break
            else:
                line_number += 1
        return pbxproj_content

    def link_scheme_to_base_build_ref(self, file_name, pbxproj_content, uuid_map, uuid_map_of_maps):
        """
        :param file_name: the name of the file to add a reference for
        :param pbxproj_content: the content of the pbxproj file
        :param uuid_map: the uuids created for build reference and file reference
        :param uuid_map_of_maps: the map of flavours to config maps of debug and release uuids
        :return: nothing
        """
        uuid_to_use = ""

        for _, file_ref_uuid in uuid_map.items():
            uuid_to_use = file_ref_uuid
            break

        into_file = self.base_conf_ref_content_template.substitute(file_ref_uuid=uuid_to_use,
                                                                   file_name=file_name)

        config_name = file_name.strip(".xcconfig")
        # Find the 'Begin XCBuildConfiguration section' tag
        first_line = self.get_build_file_line_start(pbxproj_content, "/* Begin XCBuildConfiguration section */")

        # Find the 'End XCBuildConfiguration section' tag
        last_line = self.get_build_file_line_end(pbxproj_content, "/* End XCBuildConfiguration section */")

        before = pbxproj_content[:first_line]
        after = pbxproj_content[last_line:]

        # Reduce data to only lines in XCBuildConfiguration section
        lines = pbxproj_content[first_line:last_line]

        # Now we need to find a build config that matches the AuthApp target, but has new build config.
        # It will have a config mapped to a uuid, followed by the following lines:
        #  			isa = XCBuildConfiguration;
        # 			buildSettings = {

        config_map = uuid_map_of_maps[config_name]
        relevant_debug_uuid = config_map["FinancialApp.debug"]
        relevant_release_uuid = config_map["FinancialApp.release"]

        line_number = 0

        for line in lines:
            if relevant_debug_uuid in line:
                line_number = line_number + 2
                lines.insert(line_number, into_file)

            if relevant_release_uuid in line:
                lines.insert(line_number, into_file)

            line_number += 1

        new_file_content = before
        new_file_content.extend(lines)
        new_file_content.extend(after)
        asset_gen_tools.save_lines(os.path.join(self.file_path, AA_IOS_PBXPROJ_OUT), new_file_content)


# Uncomment the lines below to run file locally
# # Create PbxProj object
# proj = PbxProj()
#
# # Read project.pbxproj file
# content = proj.read_file(AA_IOS_PBXPROJ)
#
# # configs = ["Lerato_730"]
# # configs = ["Lerato_730", "Mokoena_731"]
# # configs = ["Lerato_730", "Mokoena_731", "Gates_732"]
# configs = ["Lerato_730", "Mokoena_731", "Gates_732", "Jobs_733"]
#
# map_of_configuration_maps = proj.duplicate_xc_build_configuration(configs, content)
#
# content = proj.read_file(AA_IOS_PBXPROJ_OUT)
# proj.update_configuration_lists(map_of_configuration_maps, content)
#
# content = proj.read_file(AA_IOS_PBXPROJ_OUT)
# uuids = proj.add_config_file_to_build_file_section("DefaultConfig.xcconfig", content)
#
# content = proj.read_file(AA_IOS_PBXPROJ_OUT)
# proj.add_file_to_file_ref_section("DefaultConfig.xcconfig", content, uuids)
#
# content = proj.read_file(AA_IOS_PBXPROJ_OUT)
# proj.add_file_to_pbx_group_section("DefaultConfig.xcconfig", content, uuids)
#
# content = proj.read_file(AA_IOS_PBXPROJ_OUT)
# proj.add_file_to_pbx_resources_build_phase_section("DefaultConfig.xcconfig", content, uuids)
#
# content = proj.read_file(AA_IOS_PBXPROJ_OUT)
# proj.link_scheme_to_base_build_ref("Torvalds_731.xcconfig", content, uuids, map_of_configuration_maps)
