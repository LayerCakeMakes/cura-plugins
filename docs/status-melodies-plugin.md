# Status Melodies Plugin

**Current Version:** 15.02

## Description

Add status melodies for print started, heat up finished, and print finished.

### Input Format

The expected input are ringtones in [Nokia's RTTTL format][rtttl].
To save precious text box space a shortened, none standard, string format is
also accepted. This format allows for missing name and settings sections.

All of the following strings are accepted by the plugin.

  - `fifth:d=4,o=5,b=63:8P,8G5,8G5,8G5,2D#5`
  - `d=4,o=5,b=63:8P,8G5,8G5,8G5,2D#5`
  - `o=5,b=63:8P,8G5,8G5,8G5,2D#5`
  - `8P,8G5,8G5,8G5,2D#5`

Missing settings for duration, octave, and beats per minute will default to
their standard settings of `d=4,o=6,b=63`.

## Requirements

  - Printer with a beeper.
  - Firmware with support for the [M300 G-code][m300].

[rtttl]: http://en.wikipedia.org/wiki/RTTTL "Wikipedia"
[m300]: http://reprap.org/wiki/G-code#M300:_Play_beep_sound "RepRapWiki"
