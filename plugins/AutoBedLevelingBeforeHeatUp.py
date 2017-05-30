# AutoBedLevelingBeforeHeatUp

# Adds G28 and G29 before the automatically inserted heat up code M104.
# Also removes any additional G28 and G29 codes from the start gcode.

# Copyright 2017, Kai Hendrik Behrends
# Licensed under the MIT license.
# Version 17.04

# Used G-codes
# ============
# G28: Move to Origin (Home)
# G29: Detailed Z-Probe

# Changelog
# =========
# 17.04 - Ported to work with the Cura 2.x PostProcessingPlugin.
# 15.03 - Fixed removal of G-codes after begin of layers section.
# 15.02 - Initial Version.

from ..Script import Script

##################################################
# Plugin Main
##################################################

class AutoBedLevelingBeforeHeatUp(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Auto bed leveling before heat up",
            "key": "AutoBedLevelingBeforeHeatUp",
            "metadata": {},
            "version": 2,
            "settings": {}
        }"""

    def execute(self, data):
        leveling_done = False
        for index, layer in enumerate(data):
            if ";LAYER:0" in layer:
                # We only need to change code before the layer start.
                break
            lines_modified = False
            processedLines = []
            lines = layer.split("\n")
            for line in lines:
                if line.startswith("G28") or line.startswith("G29"):
                    # Remove all other G28 and G29 codes from the start gcode.
                    lines_modified = True
                    continue
                if line.startswith("M104") and not leveling_done:
                    # Add auto bed leveling before setting hotend temperature.
                    leveling_done = True
                    lines_modified = True
                    processedLines.append("G28 ;home all axes")
                    processedLines.append("G29 ;auto level the bed")
                processedLines.append(line)
            if lines_modified:
                # Override data with modified lines.
                data[index] = "\n".join(processedLines)
        return data
