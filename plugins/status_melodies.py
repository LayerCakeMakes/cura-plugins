#Name: Status Melodies 15.02
#Info: Add status melodies for print started, heat up finished, and print finished.
#Depend: GCode
#Type: postprocess
#Param: print_started_string(string:fifth:d=4,o=5,b=63:8P,8G5,8G5,8G5,2D#5) Print started (RTTTL)
#Param: heat_up_finished_string(string:fifth:d=4,o=5,b=63:8P,8G5,8G5,8G5,2D#5) Heat up finished (RTTTL)
#Param: print_finished_string(string:fifth:d=4,o=5,b=63:8P,8G5,8G5,8G5,2D#5) Print finished (RTTTL)

from __future__ import division
import math
import re

__copyright__ = "Copyright 2015, Kai Hendrik Behrends"
__license__ = "MIT"
__version__ = "15.02"

# Used G-codes
# ============
# G4 P<duration ms>: Dwell
# M300 S<frequency Hz> P<duration ms>: Play beep sound

# Changelog
# =========
# 15.02 - Initial Version.


##################################################
# Background Information
##################################################

# Music Note Basics
# =================
# Standard Pitch: A4 = 440 Hz
# Halfsteps: C, C#, D, D#, E, F, F#, G, G#, A, A#, B (H)
# Frequency: f = 2^(n/12) * A4
# n = difference to A4 in halfsteps e.g. n = 3 for C5

# RTTTL Specification
# ===================
# <name>:[<settings>]:<notes>
#
# Name
# ----
# String of max 10 characters excluding colon.
#
# Settings (optional)
# -------------------
# e.g. "d=4,o=6,b=63"
# d = duration [1,2,4,8,16,32] optional, default: 4 (equals one beat)
# o = octave [4,5,6,7] optional, default: 6
# b = beats per minute [25-900] optional, default: 63
#
# Notes
# -----
# e.g. "4A4.,8P,C."
# Lowest note possible A4, highest note possible B7 (Nokia Standard)
# duration [1,2,4,8,16,32] optional, defaults to settings duration.
# pitch [C, C#, D, D#, E, F, F#, G, G#, A, A#, B, H, P(pause)] required.
# octave [4,5,6,7] optional, defaults to settings duration. Not to be
# used in combination with pause.
# dot [.] optional multiplies duration by 1.5 for dotted note.


##################################################
# Rtttl classes
##################################################

class _RtttlSettings:
    """Private dummy class for RTTTL settings values."""
    pass


class _RtttlNote:
    """Private class for a single RTTTL note."""

    # Music Standards
    __STANDARD_PITCH = 440
    __BASE_OCTAVE = 4
    __NOTE_OFFSETS = {
        "c": -9, "c#": -8, "d": -7, "d#": -6, "e": -5, "f": -4, "f#": -3,
        "g": -2, "g#": -1, "a": 0, "a#": 1, "b": 2, "h": 2
    }
    __OCTAVE_OFFSET = 12

    # Constructor
    def __init__(self, duration, pitch, octave, dotted, whole_note_duration):
        self.__duration = duration
        self.__pitch = pitch
        self.__octave = octave
        self.__dotted = dotted
        self.__whole_note_duration = whole_note_duration

        # Calculate frequency in Hz.
        if self.__pitch is None:
            self.frequency = 0
        else:
            offset = (
                _RtttlNote.__NOTE_OFFSETS[self.__pitch] +
                (_RtttlNote.__OCTAVE_OFFSET * (_RtttlNote.__BASE_OCTAVE -
                 self.__octave))
            )
            self.frequency = round(
                math.pow(2, (offset/12)) * _RtttlNote.__STANDARD_PITCH, 2)

        # Calculate duration in milliseconds.
        self.duration = self.__whole_note_duration / self.__duration
        if self.__dotted:
            self.duration *= 1.5
        self.duration = int(round(self.duration, 0))

    # String representation
    def __repr__(self):
        return "['{0} Hz', '{1} ms']".format(self.frequency, self.duration)


class Rtttl:
    """Class for validating and converting RTTTL strings."""

    # RTTTL Standards
    __RTTTL_DURATIONS = [1, 2, 4, 8, 16, 32]
    __RTTTL_MIN_OCTAVE = 4
    __RTTTL_MAX_OCTAVE = 7
    __RTTTL_MIN_BPM = 25
    __RTTTL_MAX_BPM = 900
    __RTTTL_PITCHES = [
        "c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b", "h",
        "p"
    ]
    __RTTTL_PAUSE = "p"

    # Constructor
    def __init__(self, rtttl_string):
        self.name = ""
        self.__settings = _RtttlSettings()
        self.__settings.duration = 4
        self.__settings.octave = 6
        self.__settings.beats_per_minute = 63
        self.notes = []

        # Seperate the RTTTL sections.
        if not rtttl_string:
            raise ValueError("RTTTL string not valid. Empty string.")
        sections = rtttl_string.split(":")
        if len(sections) > 3:
            raise ValueError(
                "RTTTL string not valid. To many sections. [:] '{0}'"
                .format(rtttl_string))
        note_strings = sections[-1].strip().lower().split(",")
        if not note_strings[0]:
            raise ValueError("RTTTL string not valid. Note section empty.")
        setting_strings = None
        settings_regex = "^(d|o|b)\=\d+(,(d|o|b)\=\d+){0,2}$"
        if len(sections) == 3:
            self.name = sections[0]
            if sections[1]:
                if not re.match(settings_regex, sections[1].strip().lower()):
                    raise ValueError(
                        "Settings section not valid. '{0}'"
                        .format(sections[1]))
                setting_strings = sections[1].strip().lower().split(",")
            # else:
            #     Settings section is empty.
        elif len(sections) == 2:
            # Either name or settings section is missing.
            if re.match(settings_regex, sections[0].strip().lower()):
                setting_strings = sections[0].strip().lower().split(",")
            else:
                self.name = sections[0]
        # else:
        #     Name and settings section are missing.

        # Extract the settings information.
        duration_handled = False
        octave_handled = False
        beats_per_minute_handled = False
        if setting_strings is not None:
            for setting_string in setting_strings:
                # Extract settings duration.
                if setting_string.startswith("d") and not duration_handled:
                    duration_handled = True
                    duration = int(setting_string[2:])
                    if duration not in Rtttl.__RTTTL_DURATIONS:
                        raise ValueError(
                            "Settings string not valid: '{0}'\n"
                            "Unsupported duration: {1}\n"
                            "Supported durations: {2}".format(
                                setting_string, duration,
                                Rtttl.__RTTTL_DURATIONS
                            ))
                    self.__settings.duration = duration
                # Extract settings octave.
                elif setting_string.startswith("o") and not octave_handled:
                    octave_handled = True
                    octave = int(setting_string[2:])
                    if (octave < Rtttl.__RTTTL_MIN_OCTAVE or
                            octave > Rtttl.__RTTTL_MAX_OCTAVE):
                        raise ValueError(
                            "Settings string not valid: '{0}'\n"
                            "Unsupported octave: {1}\n"
                            "Supported octaves: [{2}-{3}]".format(
                                setting_string, octave,
                                Rtttl.__RTTTL_MIN_OCTAVE,
                                Rtttl.__RTTTL_MAX_OCTAVE
                            ))
                    self.__settings.octave = octave
                # Extract settings beats per minute.
                elif (setting_string.startswith("b") and
                        not beats_per_minute_handled):
                    beats_per_minute_handled = True
                    beats_per_minute = int(setting_string[2:])
                    if (beats_per_minute < Rtttl.__RTTTL_MIN_BPM or
                            beats_per_minute > Rtttl.__RTTTL_MAX_BPM):
                        raise ValueError(
                            "Settings string not valid: '{0}'\n"
                            "Unsupported beats per minute: {1}\n"
                            "Supported beats per minute: [{2}-{3}]".format(
                                setting_string, beats_per_minute,
                                Rtttl.__RTTTL_MIN_BPM, Rtttl.__RTTTL_MAX_BPM
                            ))
                    self.__settings.beats_per_minute = beats_per_minute
                # Validation error section already handled before.
                else:
                    raise ValueError(
                        "Settings section not valid: {0}\n"
                        "Double entry found: '{1}'".format(
                            setting_strings, setting_string
                        ))

        # Calculate whole note duration from settings.
        # ============================================
        # Single beat length in milliseconds = (60s / bpm) * 1000
        # One beat is the time for the settings sections duration e.g. 4
        # representing a quarter note. A whole note is 4 times longer so
        # we multiply with the settings sections duration to get to the
        # whole note duration in milliseconds.
        whole_note_duration = (
            (60 / self.__settings.beats_per_minute) * 1000 *
            self.__settings.duration
        )

        # Extract the note information.
        for note_string in note_strings:
            note_regex = (
                "^(?P<duration>\d+)?(?P<pitch>[^0-9.]+?)(?P<octave>\d+)?"
                "(?P<dotted>\.)?$"
            )
            match = re.match(note_regex, note_string)
            if not match:
                raise ValueError(
                    "Note string not valid: '{0}'\n"
                    "Pitch is missing.".format(note_string))
            # Extract note duration.
            duration = self.__settings.duration
            if match.group("duration") is not None:
                duration = int(match.group("duration"))
                if duration not in Rtttl.__RTTTL_DURATIONS:
                    raise ValueError(
                        "Note string not valid: '{0}'\n"
                        "Unsupported duration: {1}\n"
                        "Supported durations: {2}".format(
                            note_string, duration, Rtttl.__RTTTL_DURATIONS
                        ))
            # Extract note pitch.
            pitch = match.group("pitch")
            if pitch not in Rtttl.__RTTTL_PITCHES:
                raise ValueError(
                    "Note string not valid: '{0}'\n"
                    "Unsupported pitch: {1}\n"
                    "Supported pitches: {2}".format(
                        note_string, pitch, Rtttl.__RTTTL_PITCHES
                    ))
            if pitch == Rtttl.__RTTTL_PAUSE:
                pitch = None
            # Extract note octave.
            octave = None if pitch is None else self.__settings.octave
            if match.group("octave") is not None:
                if pitch is None:
                    raise ValueError(
                        "Note string not valid: '{0}'\n"
                        "Pause does not support an octave value."
                        .format(note_string))
                octave = int(match.group("octave"))
                if (octave < Rtttl.__RTTTL_MIN_OCTAVE or
                        octave > Rtttl.__RTTTL_MAX_OCTAVE):
                    raise ValueError(
                        "Note string not valid: '{0}'\n"
                        "Unsupported octave: {1}\n"
                        "Supported octaves: [{2}-{3}]".format(
                            note_string, octave, Rtttl.__RTTTL_MIN_OCTAVE,
                            Rtttl.__RTTTL_MAX_OCTAVE
                        ))
            # Extract note dotted.
            dotted = match.group("dotted") is not None
            # Create the note.
            note = _RtttlNote(
                duration, pitch, octave, dotted, whole_note_duration)
            self.notes.append(note)


##################################################
# G-code conversion
##################################################

def gcode(object):
    if isinstance(object, Rtttl):
        gcode_string = ""
        if object.name:
            gcode_string += ";{0}\n".format(object.name)
        for note in object.notes:
            if note.frequency == 0:
                # Add pause.
                gcode_string += "G4 P{0}\n".format(note.duration)
            else:
                # Add note.
                gcode_string += "M300 S{0:.0f} P{1}\n".format(
                    note.frequency, note.duration)
        return gcode_string
    else:
        raise ValueError(
            "G-code conversion not implemented for passed object type:"
            " '{0}'".format(object))


##################################################
# Plugin Main
##################################################

print_started_gcode = None
try:
    print_started_gcode = gcode(Rtttl(print_started_string))
except:
    pass
heat_up_finished_gcode = None
try:
    heat_up_finished_gcode = gcode(Rtttl(heat_up_finished_string))
except:
    pass
print_finished_gcode = None
try:
    print_finished_gcode = gcode(Rtttl(print_finished_string))
except:
    pass

# TODO(15.02): Inform user if parsing has failed. Currently there is no
# interface available for error handling in Cura 15.02.1.

with open(filename, "r") as f:
    lines = f.readlines()
with open(filename, "w") as f:
    if print_started_gcode is not None:
        f.write(";Begin print started melody\n")
        f.write(print_started_gcode)
        f.write(";End print started melody\n")
    heat_up_handled = False
    print_finished_handled = False
    for line in lines:
        if line.startswith("M109") and not heat_up_handled:
            # Add heat up finished melody after wait for extruder
            # temperature.
            heat_up_handled = True
            f.write(line)
            if heat_up_finished_gcode is not None:
                f.write(";Begin heat up finished melody\n")
                f.write(heat_up_finished_gcode)
                f.write(";End heat up finished melody\n")
            continue
        if (line.startswith(";CURA_PROFILE_STRING:") and
                not print_finished_handled):
            # Add print finished melody before the CURA_PROFILE_STRING.
            if print_finished_gcode is not None:
                f.write(";Begin print finished melody\n")
                f.write(print_finished_gcode)
                f.write(";End print finished melody\n")
            f.write(line)
            continue
        f.write(line)
    if not print_finished_handled:
        # CURA_PROFILE_STRING not present. Just add print finished
        # melody to the end.
        if print_finished_gcode is not None:
            f.write(";Begin print finished melody\n")
            f.write(print_finished_gcode)
            f.write(";End print finished melody\n")
