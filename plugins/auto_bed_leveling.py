#Name: Auto Bed Leveling 15.02
#Info: Auto level the bed before the extruder gets heated up. This avoids blobs when using FSRs under the bed.
#Depend: GCode
#Type: postprocess

__copyright__ = "Copyright 2015, Kai Hendrik Behrends"
__license__ = "MIT"
__version__ = "15.02"

# Used G-codes
# ============
# G28: Move to Origin (Home)
# G29: Detailed Z-Probe

# Changelog
# =========
# 15.02 - Initial Version.


##################################################
# Plugin Main
##################################################

with open(filename, "r") as f:
    lines = f.readlines()
with open(filename, "w") as f:
    leveling_done = False
    layers_section_handled = False
    for line in lines:
        if line.startswith("M109") and not leveling_done:
            # Add auto bed leveling before wait for extruder
            # temperature.
            leveling_done = True
            f.write("G28 ;home all axes\n")
            f.write("G29 ;auto level the bed\n")
        elif (line.startswith("G28") or line.startswith("G29") and
                not layers_section_handled):
            # Skip all other G28 and G29 codes before the layers
            # section.
            continue
        elif line.startswith(";LAYER:"):
            layers_section_handled = True
        f.write(line)
