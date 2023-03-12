# =============================== Title Block ===============================
#
# file name: SRC230223-002 G-code Generator
#
# ---Description---
# Generate G-code for basic toolpaths.
# See "ALG20220411004 Main" for reference.
# Use "TMP20220414001 G-code Parameters" to input parameters
#
# ---Change History---
#
# rev: 01-01-01-06
# date: 12/Mar/2023
# description:
# Added shift operation into dataframe.
#
# rev: 01-01-01-05
# date: 11/Mar/2023
# description:
# Added error text file statements to spiral boss, spiral drill, spiral surface dataframe function.
# update error checks using abort function in spiral boss function.
#
# rev: 01-01-01-04
# date: 08/Mar/2023
# description:
# Added error text file generator
# Added text indent function
#
# rev: 01-01-01-03
# date: 23/Feb/2023
# description:
# Fixed bug on repeat g-code generation in peck drill data frame
# Fixed bug on last_row_detect sheet  = 'main' in main data frame
#
# rev: 01-01-01-02
# date: 23/Feb/2023
# description:
# Incorporated into GitHub
# Added last row detect to peck drill data frame
#
# rev: 01-01-01-01
# date: 23/Feb/2023
# description:
# Identical to "SRC20210420001 Rev01-01-10-12 G-code Generator"
#
# rev: 01-01-10-12
# date: 16/Nov/2022
# description:
# Modified toolpath_data_frame function. Added feed rate to move cutter to start point.
#
# rev: 01-01-10-11
# date: 15/Aug/2022
# description:
# last_row_detect - fixed data frame bug.
# last_row_detect - added active dataframe and active sheet as pass in variables.
#
# rev: 01-01-10-10
# date: 13/Aug/2022
# description:
# Modified toolpath_data_frame function to process seperate linear and trochoidal tabs
# Added rapid function
# Added last_row_detect function
# Gives warning when using data validation drop down list.
#
# rev: 01-01-10-09
# date: 12/Apr/2022
# description:
# Major revision.
# Overhauled main program to import all parameters from excel file.
# changed label and names from "trichoidal" to "trochoidal" and "tri" to "tro"
# removed "test_cut" function.
#
# rev: 01-01-10-08
# date: 07/Apr/2022
# description:
# Changed z ramp in line function and arc function.
# Shifted trichoidal and line data frame variables to excel file.
#
# rev: 01-01-10-07
# date: 31/Mar/2022
# description:
# Added toolpath_data_frame function.
# Removed offset and tool diameter correction from line, arc, tri_slot, tri_arc functions.
# fixed bugs in arc_offset_adjustment
# added decimal round off in linear_offset_adjustment
#
# rev: 01-01-10-06
# date: 24/Oct/2021
# description:
# Changed all depth of cut (doc) variables to absolute convention.
#
# rev: 01-01-10-05
# date: 24/Oct/2021
# description:
# Corrected input variables in spiral surface function.
# Corrected description in spiral surface function.
#
# rev: 01-01-10-04
# date: 11/Oct/2021
# description:
# Added z overshoot compensation in spiral boss function.
# Added chipload and surface speed variables in general variables.
#
# rev: 01-01-10-03
# date: 21/Sep/2021
# description:
# removed round() function for spiral surface function
# Added selectable number of finish cuts and finishing feed rate for spiral surface function
#
# rev: 01-01-10-02
# date: 19/Sep/2021
# description:
#   Added selectable number of finish cuts and finishing feed rate for spiral boss
#   Changed origin from corner of test block to center of test block function
#   Changed variable name of "dia" to "cutter_dia" for diameter of cutter before adjustment.
#   Updated description for spiral boss.
#
# rev: 01-01-10-01
# date: 04/Sep/2021
# description:
#   Fixed spiral End diameter to accommodate cutter dia.
#   Fixed Tri slot cutter position detection.
#   Reorganized clean up text in script.
#   Added spiral boss.
#   Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
#   Added cutter diameter tolerance compensation.
#   Added initial_x, initial_y, terminal_x, terminal_y, clear_z as universal parameters
#   Added linear_offset_adjustment function.
#   Added arc_offset_adjustment function.
#   Added line function
#   Added arc function
#
# ------------------------------
# rev: 01-01-09-01
# date: 13/May/2021
# description:
#
#   Added peck drilling function.
# ------------------------------
# rev: 01-01-09
# date: 12/May/2021
# description:
#
#   Changed name from "Trichoidal Slot and Arc" to "G-code Generator"
#   Added helix drill function
#   Added surfacing function
# ------------------------------
# rev: 01-01-08
# date: 29/Apr/2021
# description:
#
#   line 265 to 268
#       added last position return if block.
#
#   line 443 to 446
#       added last position return if block.
#
#   line 551 to 560
#       added test code
#
#   replace file name variable "dt" with "name"
#
# ---Bug List---
# NA
#
# ===========================================================================

import math
import os
import pandas as pd
import sys
from datetime import datetime
import textwrap

def absolute_angle(start_x, start_y, end_x, end_y, debug = False):
    # calculate absolute angle of a vector with reference to the x axis.
    # input parameters: start_x, start_y, end_x, end_y, debug (optional)
    # returns the absolute angle.
    # angle = absolute_angle(start_x, start_y, end_x, end_y)

    vec_x = end_x - start_x
    vec_y = end_y - start_y
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)
    angle = math.degrees(math.asin(abs(vec_y)/length))
    if vec_x >= 0 and vec_y >= 0:   # angle in the 1st quadrant. from 0deg to 90deg.
        angle = angle
        q=1
    elif vec_x < 0 and vec_y >= 0:   # angle in the 2nd quadrant. from 90deg to 180deg.
        angle = 180 - angle
        q=2
    elif vec_x <= 0 and vec_y < 0:  # angle in the 3rd quadrant. from 180deg to 270deg.
        angle = 180 + angle
        q=3
    elif vec_x > 0 and vec_y < 0:  # angle in the 4th quadrant. from 270deg to 360deg.
        angle = 360 - angle
        q=4
    if debug == True:
        print(f"Q {q}")
        print(f"angle {angle}")
    return angle

def relative_coordinate(datum_x, datum_y, datum_angle, x, y, debug = False):
    # transforms cartesian coordinates relative to a datum point to its absolute coordinates.
    # input parameters: datum_x, datum_y, datum_angle, x, y, debug(optional)
    # absolute_x, absolute_y = relative_coordinate(datum_x, datum_y, datum_angle, x, y, debug)
    # refer to "PRT20210423001 Relative Coordinates Calculator"

    length = math.sqrt(x ** 2 + y ** 2)     # length of position relative to datum.
    angle = absolute_angle(0, 0, x, y, debug)    # angle of position vector relative to datum x axis.
    absolute_x = length * math.cos((datum_angle + angle)/180*math.pi) + datum_x
    absolute_y = length * math.sin((datum_angle + angle)/180*math.pi) + datum_y

    if debug == True:
        print("")
        print(f"datum_x = {datum_x}")
        print(f"datum_y = {datum_y}")
        print(f"datum_angle = {datum_angle}")
        print(f"x = {x}")
        print(f"y = {y}")
        print(f"length = {length}")
        print(f"angle = {angle}")
        print(f"absolute_x = {absolute_x}")
        print(f"absolute_y = {absolute_y}")
        print("")

    return absolute_x, absolute_y

def relative_polar(datum_x, datum_y, datum_angle, length, angle, debug = False):
    # transforms polar coordinates relative to a datum point to its absolute cartesian coordinates.
    # input parameters: datum_x, datum_y, datum_angle, length, angle, debug(optional))
    # absolute_x, absolute_y = relative_polar(datum_x, datum_y, datum_angle, length, angle, debug)
    # refer to "PRT20210423002 Polar Coordinates Calculator"

    absolute_x = length * math.cos((datum_angle + angle)/180*math.pi) + datum_x
    absolute_y = length * math.sin((datum_angle + angle)/180*math.pi) + datum_y

    if debug == True:
        print(f"datum_x = {datum_x}")
        print(f"datum_y = {datum_y}")
        print(f"datum_angle = {datum_angle}")
        print(f"length = {length}")
        print(f"angle = {angle}")
        print(f"absolute_x = {absolute_x}")
        print(f"absolute_y = {absolute_y}")

    return absolute_x, absolute_y

def write_to_file(name, text):
    # open and write text to a text file.
    with open(f'{name}.txt', 'a') as file:  # create new date time stamped file and open for writing
        file.write(text)
    file.close()

def linear_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, mode = None):

    # ---Description---
    # Calculates a straight line adjusted for cutter diameter/slot width and additional offset.
    # returns adjusted position of start and end position.
    # start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted = linear_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, mode)

    # ---Variable List---
    # dia = diameter of cutter/slot
    # offset = additional offset
    # start_x = x start of slot along neutral axis
    # start_y = y start of slot along neutral axis
    # end_x = x end of slot along neutral axis
    # end_y = y end of slot along neutral axis
    # mode = offset mode. 1 = right side of travel, 2 = left side of travel, 3 = on line of travel.

    # ---Return Variable List---
    # start_x_adjusted = adjusted start x position
    # start_y_adjusted = adjusted start y position
    # end_x_adjusted = adjusted end x position
    # end_y_adjusted = adjusted end y position

    # ---Change History---
    # rev: 01-01-10-07
    # round of return values to 4 deicimal places.
    # software test run on 31/Mar/2022
    #
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 13/Sep/2021
    # --------------------

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\nlinear_offset_adjustment\nlinear_offset_adjustment mode undefined\nlinear_offset_adjustment mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        quit()

    if mode == 3:
        start_x_adjusted = start_x
        start_y_adjusted = start_y
        end_x_adjusted = end_x
        end_y_adjusted = end_y
        return (start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted)

    vec_x = end_x - start_x     # x vector length of slot
    vec_y = end_y - start_y     # y vector length of slot
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)     # length of slot

    if mode == 1:
        y_temp = -(dia/2 + offset)  # adjust for right side of travel

    elif mode == 2:
        y_temp = dia/2 + offset  # adjust for left side of travel

    # update adjustment offset position of slot center.
    start_x_temp = start_x
    start_y_temp = start_y
    x1_temp = 0
    x2_temp = length

    angle_temp = absolute_angle(start_x, start_y, end_x, end_y)
    start_x_adjusted, start_y_adjusted = relative_coordinate(start_x_temp, start_y_temp, angle_temp, x1_temp, y_temp, debug=False)
    start_x_adjusted = round(start_x_adjusted, 5)    # round to 5 decimal places.
    start_y_adjusted = round(start_y_adjusted, 5)     # round to 5 decimal places.
    end_x_adjusted, end_y_adjusted = relative_coordinate(start_x_temp, start_y_temp, angle_temp, x2_temp, y_temp, debug=False)
    end_x_adjusted = round(end_x_adjusted, 5)     # round to 5 decimal places.
    end_y_adjusted = round(end_y_adjusted, 5)     # round to 5 decimal places.

    return(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted)

def arc_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode = None):

    # ---Description---
    # Calculates an arc adjusted for cutter diameter/slot width and additional offset.
    # returns adjusted position of start and end position.
    # Refer to 'PRT20210912001 Arc Offset Adjustment' and 'ALG20220401001 Arc Offset Adjustment Algorithm'
    # start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted = arc_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode)

    # ---Variable List---
    # dia = diameter of cutter/slot
    # offset = additional offset
    # start_x = x start of arc along neutral axis
    # start_y = y start of arc along neutral axis
    # end_x = x end of arc along neutral axis
    # end_y = y end of arc along neutral axis
    # rad = radius of arc
    # cw = Boolean. True = clockwise False = counter clockwise.
    # less_180 = Boolean. True: < 180deg False: > 180deg.
    # mode = offset mode. 1 = right side of travel, 2 = left side of travel, 3 = on line of travel.

    # ---Return Variable List---
    # start_x_adjusted = adjusted start x position
    # start_y_adjusted = adjusted start y position
    # end_x_adjusted = adjusted end x position
    # end_y_adjusted = adjusted end y position
    # rad_adjusted = adjusted arc radius

    # ---Change History---
    # rev: 01-01-10-07
    # fixed bug on angle and vector selection for cw and ccw arcs.
    # elaborated comments.
    # fixed bug on pre code check.
    # round of return values to 4 decimal places.
    # software test run on 31/Mar/2022
    #
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 13/Sep/2021
    # --------------------

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\narc_offset_adjustment mode undefined\narc_offset_adjustment mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        quit()

    if mode == 3:   # on line cut. no adjustment
        start_x_adjusted = start_x
        start_y_adjusted = start_y
        end_x_adjusted = end_x
        end_y_adjusted = end_y
        rad_adjusted = rad
        start_x_adjusted = round(start_x_adjusted, 5)  # round to 5 decimal places.
        start_y_adjusted = round(start_y_adjusted, 5)  # round to 5 decimal places.
        end_x_adjusted = round(end_x_adjusted, 5)  # round to 5 decimal places.
        end_y_adjusted = round(end_y_adjusted, 5)  # round to 5 decimal places.
        rad_adjusted = round(rad_adjusted, 5)  # round to 5 decimal places.
        return (start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted)

    # check if cutter radius + offset is larger than arc radius for internal/pocket cut.
    if ((mode == 1 and cw == True) or (mode == 1 and cw == True))and dia/2+offset >= rad:
        print(f"!!script aborted!!\narc_offset_adjustment\ncutter radius + offset is larger than of equal to arc radius for internal/pocket cut\nrad = {rad}\ndia = {dia}\noffset = {offset}")
        text = '''\n(!!script aborted!!)\n(cutter offset larger than of equal to arc)\n'''  # write header for section.
        quit()

    # check if arc radius is <= to 0
    if rad <= 0:
        print(f"!!script aborted!!\narc_offset_adjustment\narc radius <= 0\nrad = {rad}")
        text = '''\n(!!script aborted!!)\n(arc radius <= 0)\n'''  # write header for section.
        quit()

    vec_x = end_x - start_x                         # x vector length of slot
    vec_y = end_y - start_y                         # y vector length of slot
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)     # direct length of start to end point.
    x_temp = length/2                               # determine the projected (x) distance of the center of arc along the vector from the start to end point. Used later to determine center of arc.
    y_temp = math.sqrt(rad ** 2 - x_temp ** 2)      # Determine the perpendicular (y) distance of the center of arc to the vector from the start to end point. Used later to determine center of arc.
    angle_temp = absolute_angle(start_x, start_y, end_x, end_y, debug=False)        # calculate absolute angle of the vector from the start point to end point. Used to determine center of arc
    angle_arc = 2 * math.degrees(math.asin((length/2)/rad))                         # determine angle of arc.

    #if mn
    if cw == True:
        if less_180 == True:
            y_temp = -y_temp        # center is on right side of arc vector for acute clockwise arcs.
            angle_arc = -angle_arc  # arc angle is moving in the negative direction from the start to end point.
        elif less_180 == False:
            y_temp = y_temp         # center is on left side of arc vector for obtuse clockwise arcs.
            angle_arc = angle_arc   # arc angle is moving in the positive direction from the start to end point.
    if cw == False:
        if less_180 == True:
            y_temp = y_temp         # center is on left side of arc vector for acute counter-clockwise arcs.
            angle_arc = angle_arc   # arc angle is moving in the positive direction from the start to end point.
        elif less_180 == False:
            y_temp = -y_temp        # center is on right side of arc vector for acute clockwise arcs.
            angle_arc = -angle_arc  # arc angle is moving in the negative direction from the start to end point.

    x_center, y_center = relative_coordinate(start_x, start_y, angle_temp, x_temp, y_temp, debug = False) # calculate center of arc
    start_angle = absolute_angle(x_center, y_center, start_x, start_y, debug = False)   # calculate absolute angle of datum vector. i.e. vector of arc center to start point

    if cw == True:
        if mode == 1:
            rad_adjusted = rad - (dia/2 + offset)   # calculate adjusted radius for internal/pocket cut
        elif mode == 2:
            rad_adjusted = rad + (dia/2 + offset)    # calculate adjusted radius for external/boss cut
    if cw == False:
        if mode == 1:
            rad_adjusted = rad + (dia/2 + offset)   # calculate adjusted radius for external/boss cut
        elif mode == 2:
            rad_adjusted = rad - (dia/2 + offset)    # calculate adjusted radius for internal/pocket cut
    rad_adjusted = round(rad_adjusted, 5)  # round to 5 decimal places.

    start_x_adjusted, start_y_adjusted = relative_polar(x_center, y_center, start_angle, rad_adjusted, 0, debug=False)        # calculate adjusted start point
    start_x_adjusted = round(start_x_adjusted, 5)    # round to 5 decimal places.
    start_y_adjusted = round(start_y_adjusted, 5)     # round to 5 decimal places.

    end_x_adjusted, end_y_adjusted = relative_polar(x_center, y_center, start_angle, rad_adjusted, angle_arc, debug=False)    # calculate adjusted end point
    end_x_adjusted = round(end_x_adjusted, 5)     # round to 5 decimal places.
    end_y_adjusted = round(end_y_adjusted, 5)     # round to 5 decimal places.

    return(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted)

def line(end_x, end_y, name, feed = None, end_z = None):

    # ---Description---
    # Calculates and prints G-code of a straight line.
    # Optional z direction ramp. !! Note: ramp_z is in relative units. !!
    # Optional feed rate.
    # returns cutter position
    # cutter_x, cutter_y, cutter_z, text = line(end_x, end_y, name, feed, end_z)

    # ---Variable List---
    # end_x = x end of line
    # end_y = y end of line
    # name = name of file
    # feed = cutting feed. (Optional)

    # ---Return Variable List---
    # cutter_x = current cutter x position
    # cutter_y = current cutter y position
    # cutter_z = current cutter z position
    # text = G-code text

    # ---Change History---
    # rev: 01-01-10-09
    # removed z ramp from pass in variables.
    #
    # rev: 01-01-10-08
    # date: 07/Apr/2022
    # description:
    # Changed z ramp to end ramp
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # removed dia and offset compensation.
    # added z return parameters.
    # software test run on 12/Mar/2022
    #
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 14/Sep/2021
    # --------------------

    text = f'''G1 X{"%.4f" % end_x} Y{"%.4f" % end_y}'''

    if end_z != None:
        text_temp = f''' Z{"%.4f" % end_z}'''  # optional end_z
        text = text + text_temp

    if feed != None:
        text_temp = f''' F{"%.0f" % feed}'''    # optional feed
        text = text + text_temp

    text = text + "\n"      # new line

    cutter_x = end_x
    cutter_y = end_y
    cutter_z = end_z

    return(cutter_x, cutter_y, cutter_z, text)        # returns cutter position

def arc(end_x, end_y, name, rad, cw, less_180, feed = None, end_z = None):

    # ---Description---
    # Calculates and prints G-code of an arc.
    # Optional z direction ramp. !! Note: ramp_z is in relative units. !!
    # Optional feed rate.
    # returns cutter position
    # cutter_x, cutter_y, cutter_z, text = arc(end_x, end_y, name, rad, cw, less_180, feed, end_z)

    # ---Variable List---
    # end_x = x end of line
    # end_y = y end of line
    # name = name of file
    # rad = radius of arc
    # cw = Boolean. True = clockwise False = counter clockwise.
    # less_180 = Boolean. True: < 180deg False: > 180deg.
    # feed = cutting feed. (Optional)

    # ---Return Variable List---
    # cutter_x = adjusted start x position/ cutter x position
    # cutter_y = adjusted start y position/ cutter y position
    # cutter_z = adjusted start z position/ cutter z position
    # text = G-code text

    # ---Change History---
    # rev: 01-01-10-09
    # removed z ramp from pass in variables.
    # included rad = 0 condition.
    #
    # rev: 01-01-10-08
    # date: 07/Apr/2022
    # description:
    # Changed z ramp to end ramp
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # removed dia and offset compensation.
    # added z return parameters.
    # software test run on 12/Mar/2022
    #
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 14/Sep/2021
    # --------------------

    # check for start_z definition.

    if round(rad, 5)==0:    # round to 5 decimal places. detect rad = zero. returns x, y as point destination.
        text = f'''G1 X{"%.4f" % end_x} Y{"%.4f" % end_y}'''
        cutter_x = end_x
        cutter_y = end_y
        cutter_z = end_z
        return (cutter_x, cutter_y, cutter_z, text)  # returns cutter position

    if less_180 == True:
        rad_adjusted = rad     # acute arc. G-code convention: positive radius = minor arc.
    if less_180 == False:
        rad_adjusted = -rad    # obtuse arc. G-code convention: negative radius = major arc.

    if cw == True:
        dir = '02'
    elif cw == False:
        dir = '03'

    text = f'''G{dir} X{"%.4f" % end_x} Y{"%.4f" % end_y} R{"%.4f" % rad_adjusted}'''

    if end_z != None:
        text_temp = f''' Z{"%.4f" % end_z}'''  # optional end_z
        text = text + text_temp

    if feed != None:
        text_temp = f''' F{"%.0f" % feed}'''    # optional feed
        text = text + text_temp

    text = text + "\n"      # new line

    cutter_x = end_x
    cutter_y = end_y
    cutter_z = end_z

    return(cutter_x, cutter_y, cutter_z, text)        # returns cutter position

def tro_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, cutter_x, cutter_y, first_slot = True, last_slot = True, debug = False):
    
   # ---Description---
   # Calculates and prints to a txt file the trochoidal tool path in G code of a straight slot.
   # returns last position of cutter and end position of slot.
   # start and end points are located along slot arc center/neutral axis.
   # assumes that cutter is at cutting depth.
   # does NOT return to safe z.
   # end_x_original, end_y_original, cutter_x_final, cutter_y_final, text = tro_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, cutter_x, cutter_y, first_slot, last_slot, debug)

   # ---Variable List---
   # start_x = x start of slot along neutral axis
   # start_y = y start of slot along neutral axis
   # end_x = x end of slot along neutral axis
   # end_y = y end of slot along neutral axis
   # step = depth of step per trochoidal slice.
   # wos = width of slot
   # dia = diameter of cutter
   # name = name of file
   # cutter_x = x position of cutter
   # cutter_y = y position of cutter
   # first_slot = boolean. Is this the first slot?
   # last_slot = boolean. Is this the last slot?
   # debug = False (default)

   # ---Return Variable List---
   # end_x_original = x coordinate of end of slot unadjusted
   # end_y_original = y coordinate of end of slot unadjusted
   # cutter_x_final = x coordinate of cutter position
   # cutter_y_final = y coordinate of cutter position
   # text = G-code text
   
   # ---Change History---
   # rev: 01-01-10-09
   # changed label and names from "trichoidal" to "trochoidal" and "tri" to "tro"
   #
   # rev: 01-01-10-07
   # changed from writing G-code directly to txt file to a separate text variable.
   # removed offset compensation.
   # software test run on 12/Mar/2022
   #
   # rev: 01-01-10-01
   # Fixed cutter reorientation detection by changing "and" to "or"
   # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
   # software test run on 07/Sep/2021
   # physical test run on 09/Sep/2021
   # Added slot offset for internal, external or slot cut
   # --------------------

    title_block = \
    f'''
    (---trochoidal linear slot start---)                                                                                                                                                                                                                     
    (---description---)
    (Calculates and prints to a txt file the trochoidal tool path in G code of a straight slot.)                                                                                                         
    (returns last position of cutter and end position of slot)
    (start and end points are located along slot arc center/neutral axis)
    (assumes that cutter is at cutting depth)
    (does NOT return to safe z)
    (---parameters---)                                                                                                          
    (start: X{"%.3f" % start_x} Y{"%.3f" % start_y})
    (end: X{"%.3f" % end_x} Y{"%.3f" % end_y})
    (step over: {"%.3f" % step})
    (width of slot: {"%.3f" % wos})                                                                                            
    (cutter diameter: {"%.3f" % dia})
    (position of cutter: X{"%.4f" % cutter_x} Y{"%.4f" % cutter_y})
    (first slot: {first_slot})
    (last slot: {last_slot})                                                                                                  
    '''
    text = title_block          # initialize text variable

    start_x_original = start_x
    start_y_original = start_y
    end_x_original = end_x
    end_y_original = end_y

    vec_x = end_x - start_x     # x vector length of slot
    vec_y = end_y - start_y     # y vector length of slot
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)     # length of slot
    noc_raw = length / step    # number of cuts-raw
    noc = math.floor(noc_raw)  # number of cuts rounded down
    noc_re = length % step  # calculate remainder
    dia_arc = wos - dia  # diameter of Cut Arc
    rad_arc = dia_arc / 2  # radius of Cut Arc
    angle = absolute_angle(start_x, start_y, end_x, end_y, debug)    # conversion to absolute angle.

    i = 1   # initialize counter

    if noc_re != 0:  # if there is a remainder, increment number of cuts by 1 to include last partial cut.
        noc = noc + 1

    if debug == True:
        print("")
        print("--------------------")
        print("Function: trochoidal")
        print("--------------------")
        print(f"start_x {start_x}")
        print(f"start_y {start_y}")
        print(f"end_x {end_x}")
        print(f"end_y {end_y}")
        print(f"length {length}")
        print(f"noc_raw {noc_raw}")
        print(f"noc {noc}")
        print(f"noc_re {noc_re}")
        print(f"dia_arc {dia_arc}")
        print(f"rad_arc {rad_arc}")
        print(f"angle {angle}")
        print(f"noc {noc}\n")

    while i <= noc:

        if debug == True:
            print(f"i {i}")

        # calculate 1st position. refer to sketch.
        x_temp = (i - 1) * step
        y_temp = -rad_arc
        x1, y1 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
        if debug == True:
            print(f"x1 {x1}")
            print(f"y1 {y1}")

        # calculate 2nd position. refer to sketch.
        if (i == noc) and (noc_re != 0):
            x_temp = (i - 1) * step + noc_re    # cut last loop to the depth of the remainder.
        else:
            x_temp = i * step
        y_temp = -rad_arc
        x2, y2 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
        if debug == True:
            print(f"x2 {x2}")
            print(f"y2 {y2}")

        # calculate 3rd position. refer to sketch.
        if (i == noc) and (noc_re != 0):
            x_temp = (i - 1) * step + noc_re
        else:
            x_temp = i * step
        y_temp = rad_arc
        x3, y3 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
        if debug == True:
            print(f"x3 {x3}")
            print(f"y3 {y3}")

        # calculate 4th position. refer to sketch.
        x_temp = (i - 1) * step
        y_temp = rad_arc
        x4, y4 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
        if debug == True:
            print(f"x4 {x4}")
            print(f"y4 {y4}")

        if i == 1:                                           # for 1st loop only. move tool from arc start position to 1st position.
            if first_slot == True:
                temp = rad_arc / 2
                line_1 = \
    f'''
    G03 X{"%.4f" % x1} Y{"%.4f" % y1} R{"%.4f" % temp}
    '''
                text = text + line_1                # append to text variable
            else:                                           # reorient cutter to starting point of slot.
                delta_x = abs(x1 - cutter_x)
                delta_y = abs(y1 - cutter_y)
                if (delta_x > 0.0001) or (delta_y > 0.0001):       # if cutter is at start point skip else reorient.
                    line_1 = \
    f'''
    G03 X{"%.4f" % x1} Y{"%.4f" % y1} I{"%.4f" % (start_x-cutter_x)} J{"%.4f" % (start_y-cutter_y)}
    '''
                    text = text + line_1            # append to text variable

        # write G code of rest of trochoidal loop
        line_2 = \
    f'''
    G1 X{"%.4f" % x2} Y{"%.4f" % y2}
    G03 X{"%.4f" % x3} Y{"%.4f" % y3} R{"%.4f" % rad_arc}
    G1 X{"%.4f" % x4} Y{"%.4f" % y4}
    '''
        text =text + line_2                 # append to text variable

        if i == noc:        # for last loop only. move tool to be along slot arc.
            if last_slot == True:
                temp = rad_arc / 2
                x_temp = (i - 1) * step
                y_temp = 0
                x5, y5 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
                line_3 = \
    f'''G03 X{"%.4f" % x5} y{"%.4f" % y5} R{"%.4f" % temp}
    G1 X{"%.4f" % end_x} Y{"%.4f" % end_y}
    '''
                cutter_x_final = end_x
                cutter_y_final = end_y
            elif last_slot == False:
                x_temp = length
                y_temp = -rad_arc
                x5, y5 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
                line_3 = \
    f'''G03 X{"%.4f" % x1} y{"%.4f" % y1} R{"%.4f" % rad_arc}
    G1 X{"%.4f" % x5} Y{"%.4f" % y5}
    '''
                cutter_x_final = x5
                cutter_y_final = y5
        else:
            line_3 = \
    f'''G03 X{"%.4f" % x1} y{"%.4f" % y1} R{"%.4f" % rad_arc}
    '''
        text =text + line_3             # append to text variable
        i = i + 1

    text_temp = \
    f'''(---trochoidal linear slot end---)
    '''
    text = text + text_temp         # append to text variable

    return (end_x_original, end_y_original, cutter_x_final, cutter_y_final, text)

def tro_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot = True, last_slot = True, debug = False):

   # ---Description---
   # Calculates and prints to a txt file the trochoidal tool path in G code of a circular arc.
   # returns last position of cutter and end position of arc.
   # refer to "PRT20210421001 Trichoidal Arc Calculator", "MEM20210522001 Trichoidal Arc", "MEM20210429002 Trichoidal Notes", "ALG20210520001 Trichoidal Arc Algorithm"
   # start and end points are located at slot arc center points.
   # assumes that cutter is at cutting depth.
   # does not return to safe z.
   # does not set cutting feed.
   # end_x_original, end_y_original, cutter_x_final, cutter_y_final, text = tro_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot, last_slot, debug)

   # ---Variable List---
   # start_x = x start of arc along neutral axis
   # start_y = y start of arc along neutral axis
   # end_x = x end of arc along neutral axis
   # end_y = y end of arc along neutral axis
   # step = depth of step per trochoidal slice.
   # wos = width of slot
   # dia = diameter of cutter
   # rad_slot = radius of slot arc.
   # cw = Boolean. True = clockwise False = counter clockwise.
   # less_180 = Boolean. True: < 180deg False: > 180deg.
   # name = name of file
   # cutter_x = x position of cutter
   # cutter_y = y position of cutter
   # first_slot = boolean. Is this the first slot?
   # last_slot = boolean. Is this the last slot?
   # debug = False (default)

   # ---Return Variable List---
   # end_x_original = x coordinate of end of slot unadjusted
   # end_y_original = y coordinate of end of slot unadjusted
   # cutter_x_final = x coordinate of cutter position
   # cutter_y_final = y coordinate of cutter position
   # text = G-code text

    # ---Change History---
    # rev: 01-01-10-09
    # changed label and names from "trichoidal" to "trochoidal" and "tri" to "tro"
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # changed "else:" to "elif cw == False:" where available.
    # found and fixed bug for cw and ccw arcs regarding adjusted radius for the last arc segments for non last slots.
    # software test run on 04/Apr/2022
    # removed offset compensation.
    # software test run on 12/Mar/2022
    #
    # rev: 01-01-10-01
    # Added variable list
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021
    # physical test run on 09/Sep/2021
    #
    # rev: 01-01-09-08
    # initial release

    start_block = \
    f'''(---trochoidal arc slot start---)
    (---description---)
    (Calculates and prints to a txt file the trochoidal tool path in G code of a counter clockwise arc.)
    (returns last position of cutter and end position of arc.)
    (refer to "PRT20210421001 Trichoidal Arc Calculator", "MEM20210522001 Trichoidal Arc", "MEM20210429002 Trichoidal Notes")
    (start and end points are located at slot arc center points.)
    (assumes that cutter is at cutting depth.)
    (does not return to safe z.)
    (does not set cutting feed.)
    (---parameter---)
    (start: X{"%.3f" % start_x} Y{"%.3f" % start_y})
    (end: X{"%.3f" % end_x} Y{"%.3f" % end_y})
    (step over: {"%.3f" % step})                     
    (width of slot: {"%.3f" % wos}) 
    (slot radius : {"%.3f" % rad_slot})                  
    (cutter diameter: {"%.3f" % dia})        
    (position of cutter: X{"%.4f" % cutter_x} Y{"%.4f" % cutter_y}) 
    (first slot: {first_slot})              
    (last slot: {last_slot})                
    (clockwise : {cw})
    (acute angle: {less_180})
    '''
    text = start_block          # initialize text variable

    start_x_original = start_x
    start_y_original = start_y
    end_x_original = end_x
    end_y_original = end_y

    # check if width of slot is smaller tool dia
    if wos <= dia:
        print(f'''!!script aborted!!\ntro_arc\nwidth of slot is smaller tool dia.\nwidth of slot= {"%.3f" % wos}\ntool dia = {"%.3f" % dia}''')
        text = '''\n(!!script aborted!!)\n(width of slot is smaller tool dia)\n'''  # write header for section.
        quit()

    skip_1 = False   # initialize skip_1 flag

    vec_x = end_x - start_x
    vec_y = end_y - start_y
    linear_length = math.sqrt(vec_x ** 2 + vec_y ** 2)      # calculate linear length from start point to end point

    # check if diameter of arc is larger than linear length
    if rad_slot*2 < linear_length:
        print(f'''!!script aborted!!\ntro_arc\ndiameter of arc is smaller than linear length.\ndiameter of arc = {"%.3f" % (rad_slot*2)}\nlinear length = {"%.3f" % linear_length}''')
        text = '''\n(!!script aborted!!)\n(diameter of arc is smaller than linear length)\n'''  # write header for section.
        quit()

    slot_angle = 2 * math.degrees(math.asin(( linear_length / 2) / rad_slot))  # acute arc angle
    if less_180 == False:
        slot_angle = 360 - slot_angle     # obtuse arc angle

    dia_arc = wos - dia  # diameter of Cut Arc
    rad_arc = dia_arc / 2  # radius of Cut Arc

    # -----calculate datum-----
    # the center of slot arc is to be used as the datum point for indexing the trochoidal loops.
    # the centroid of the geometric model is to be used as the temporary reference point. refer to sketch "MEM20210429002 Notes".
    # vectors are initially resolved relative to the centroid after which absolute positions are determined.
    # there are 2 possible center points (datums) depending on if the arc is acute or obtuse.
    # acute arc (<= 180deg) will have its datum on the left side of the arc vector.
    # obtuse arc (> 180deg) will have its datum on the right side of the arc vector.

    cen_length = math.sqrt(rad_slot**2 - (linear_length/2)**2)    # calculate distance between centroid and arc center.
    vec_angle = absolute_angle(start_x, start_y, end_x, end_y)    # calculate the absolute angle of start point to end point.
    cen_x, cen_y = relative_polar(start_x, start_y, 0, linear_length/2, vec_angle)  # calculate position of centroid.

    if less_180:
        if cw == True:
            vec_angle = vec_angle + 270     # acute angle, cw
        elif cw == False:
            vec_angle = vec_angle + 90     # acute angle, ccw
    else:
        if cw == True:
            vec_angle = vec_angle + 90     # obtuse angle, cw
        elif cw == False:
            vec_angle = vec_angle + 270     # obtuse angle, ccw

    datum_x, datum_y = relative_polar(cen_x, cen_y, 0, cen_length, vec_angle)  # calculate position of datum.
    step_angle = step / (rad_slot*math.pi/180)
    inc_angle = step_angle  # initialize increment angle
    datum_angle = absolute_angle(datum_x, datum_y, start_x, start_y)  # calculate absolute angle of start point with respect to datum (center of slot arc).
    end_angle = slot_angle  # end angle
    if cw == True:
        end_angle = - abs(end_angle)    # angle decrements in cw arc
    elif cw == False:
        end_angle = abs(end_angle)      # angle increments in ccw arc
    angle = 0   # initialize angle

    def segment_position (datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw):
        # calculate positions. refer to sketch.
        major_rad = rad_slot + rad_arc
        minor_rad = rad_slot - rad_arc
        if cw == True:
            x1, y1 = relative_polar(datum_x, datum_y, datum_angle, minor_rad, angle)
            x2, y2 = relative_polar(datum_x, datum_y, datum_angle, minor_rad, angle - inc_angle)
            x3, y3 = relative_polar(datum_x, datum_y, datum_angle, major_rad, angle - inc_angle)
            x4, y4 = relative_polar(datum_x, datum_y, datum_angle, major_rad, angle)
        elif cw == False:
            x1, y1 = relative_polar(datum_x, datum_y, datum_angle, major_rad, angle)
            x2, y2 = relative_polar(datum_x, datum_y, datum_angle, major_rad, angle + inc_angle)
            x3, y3 = relative_polar(datum_x, datum_y, datum_angle, minor_rad, angle + inc_angle)
            x4, y4 = relative_polar(datum_x, datum_y, datum_angle, minor_rad, angle)
        x5 = x1
        y5 = y1
        return (x1, y1, x2, y2, x3, y3, x4, y4, x5, y5)

    def segment_radius(rad_slot, rad_arc, cw):
        # calculate radii. refer to sketch.
        major_rad = rad_slot + rad_arc
        minor_rad = rad_slot - rad_arc
        if cw == True:
            r1 = minor_rad
            r2 = minor_rad
            r4 = major_rad
        elif cw == False:
            r1 = major_rad
            r2 = major_rad
            r4 = minor_rad
        r3 = rad_arc
        r5 = rad_arc
        return (r1, r2, r3, r4, r5)

    def angle_increment(angle, step_angle, cw):
        # increment angle. cw: negative direction. ccw: positive direction
        if cw == True:
            angle = angle - step_angle
        elif cw == False:
            angle = angle + step_angle
        return angle

    def text_tro_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw):
        # generate g code. refer to sketch.

        text = ''   # intialize

        if cw == True:
            dir = 'G02'
            inv_dir = 'G03'
        elif cw == False:
            dir = 'G03'
            inv_dir = 'G02'

        if skip_1 == False:     # if cutter is at x1y1, skip
            text_01 = \
            f'''
            {dir_1} X{"%.4f" % x1} Y{"%.4f" % y1} R{"%.4f" % r1}
            '''
            text = text_01

        text_02 = \
            f'''
            {dir} X{"%.4f" % x2} Y{"%.4f" % y2} R{"%.4f" % r2}
            G03 X{"%.4f" % x3} Y{"%.4f" % y3} R{"%.4f" % r3}
            {inv_dir} X{"%.4f" % x4} Y{"%.4f" % y4} R{"%.4f" % r4}
            G03 X{"%.4f" % x5} Y{"%.4f" % y5} R{"%.4f" % r5}
            '''
        text = text + text_02
        return (text)

    x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
    r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)
    angle = angle_increment(angle, step_angle, cw)

    # for 1st loop only. move tool from arc start position to 1st position.
    if first_slot == True:      # first slot. assumes cutter at start x y.
        r1 = rad_arc / 2
        dir_1 = 'G03'
    elif first_slot == False:   # reorient cutter to starting point of slot if this is not first slot. assumes cutter is along circumference of slot.
        delta_x = abs(x1 - cutter_x)
        delta_y = abs(y1 - cutter_y)
        if (delta_x > 0.0001) or (delta_y > 0.0001):       # if cutter not at start point reorient else skip.

            #determine if angle between current/now cutter position and first position (x1, y1) is acute or obtuse
            temp_angle_now = absolute_angle(start_x, start_y, cutter_x, cutter_y)
            temp_angle_1 = absolute_angle(start_x, start_y, x1, y1)
            temp_angle_diff = temp_angle_1 - temp_angle_now

            if temp_angle_diff <0 :         # if angle overflow add 360
                temp_angle_diff = 360+temp_angle_diff

            if temp_angle_diff <= 180 :
                r1 = rad_arc
            else:
                r1 = - rad_arc
            dir_1 = 'G03'
        else:
            skip_1 = True   # set skip_1 flag
            # initialize dir_1 direction.
            if cw == True:
                dir_1 = 'G02'
            elif cw == False:
                dir_1 = 'G03'

    text_temp = text_tro_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)     # generate first block og g code.
    text = text + text_temp
    skip_1 = False  # reset skip_1 flag

    # initialize dir_1 direction.
    if cw == True:
        dir_1 = 'G02'
    elif cw == False:
        dir_1 = 'G03'

    # generate g code for trochoidal loops except last loop
    while abs(angle) < (abs(end_angle)-abs(step_angle)):
        x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
        r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)
        angle = angle_increment(angle, step_angle, cw)
        text_temp = text_tro_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)
        text = text + text_temp
    # generate g code for last loop if present.
    if abs(angle) >= (abs(end_angle)-abs(step_angle)) and abs(angle) < abs(end_angle):
        inc_angle = abs(end_angle) - abs(angle)
        x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
        r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)

        # calculate last slot end position
        if last_slot == True:   # calculate x5, y5, r5 to end at midline with the slot path.
            r5 = rad_arc/2
            x5, y5 = relative_polar(datum_x, datum_y, datum_angle, rad_slot, angle)

        text_temp = text_tro_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)
        text = text + text_temp

        if last_slot == True:   # advance tool to end position on slot path midline.
            text_temp = \
                f'''
                {dir_1} X{"%.4f" % end_x} Y{"%.4f" % end_y} R{"%.4f" % rad_slot}
                '''
            text = text + text_temp
            cutter_x_final = end_x
            cutter_y_final = end_y
        else:       # advance tool to cutting position for next slot.
            if cw == True:
                rad_temp = rad_slot - rad_arc
            if cw == False:
                rad_temp = rad_slot + rad_arc
            text_temp = f'''{dir_1} X{"%.4f" % x2} Y{"%.4f" % y2} R{"%.4f" % rad_temp}'''
            text = text + text_temp
            cutter_x_final = x2
            cutter_y_final = y2

    text_temp = \
    f'''
    (---trochoidal arc slot end---)
    '''
    # write footer for section.
    text = text + text_temp

    return (end_x_original, end_y_original, cutter_x_final, cutter_y_final, text)

def surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name, debug = False):

    # ---description---
    # calculates and prints to a txt file the tool path in G code to surface a rectangular part.
    # assumes climb milling.
    # assumes origin at bottom left corner.
    # assumes z=0 at top surface.
    # starts at x = length_x + 2 * diameter of cutter, y = 0  from bottom left corner.
    # cuts in a clockwise direction from the outside to the center.
    # return to origin after surfacing.
    # start and ends at safe_z
    # refer to PRT20210510003 Surfacing Calculator
    # text = surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name, debug)

    # ---Variable List---
    # origin_x = x of bottom left corner
    # origin_y = y of bottom left corner
    # length_x = x length of rectangle
    # length_y = y length of rectangle
    # doc = depth of cut (absolute convention. Negative in the downward Z direction.)
    # dia = diameter of cutter
    # step = step over per pass.
    # z_f =  z feed
    # cut_f = cutting feed
    # safe_z = safe z
    # name = name of file
    # debug = False (default)

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    # rev: 01-01-01-05
    # added error checks using abort function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # software test run on 04/04/2022
    #
    # rev: 01-01-10-06
    # changed doc from scalar to absolute convention.
    # physical test run on TBD
    #
    # rev: 01-01-10-01
    # Added variable list
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # physical test run on 09/Sep/2021

    # check if safe_z is above surface.
    if safe_z <= 0:
        abort('safe_z', safe_z, 'safe_z below surface')

    # check if step is larger than tool dia.
    if step > dia:
        abort('step',step,f'step is larger than tool dia.\nstep = {"%.3f" % step}\ntool dia = {"%.3f" % dia}')

    start_block = \
    f'''
    (---surfacing start---)
    (This program calculates the tool path to surface a rectangular part.)
    (assumes climb milling.)
    (assumes origin at bottom left corner.)
    (assumes z=0 at top surface.)
    (starts at x = 0, y = -(2 * diameter of cutter) from bottom left corner.)
    (cuts in a clockwise direction from the outside to the center.)
    (return to origin after surfacing.)
    (---parameter---)
    (origin: X{"%.3f" % origin_x} Y{"%.3f" % origin_y})
    (length x: {"%.3f" % length_x})
    (length y: {"%.3f" % length_y})
    (depth of cut: {"%.3f" % doc})
    (step: {"%.3f" % step})
    (plunge feed: {"%.1f" % z_f})
    (cutting feed: {"%.1f" % cut_f})
    (safe Z: {"%.3f" % safe_z})
    '''
    text = start_block          # initialize text variable

    # initialize starting point
    start_x = origin_x + length_x + dia*2
    start_y = origin_y - dia/2 + step

    # starting G code block
    text_temp = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}   (Rapid to start point)
    F{"%.1f" % z_f}  (set to plunge feed)
    G1 Z{"%.4f" % doc} (go to cut depth)
    F{"%.1f" % cut_f}  (set to cutting feed)

    G91 (incremental positioning)
    G1 X{"%.4f" % (-dia*2)} (go to starting corner)
    '''
    text = text + text_temp

    # length decremental function
    def length_dec(length, step, dia):
        length = length - step
        rad = 0         # initialize rad
        last = False    # initialize/clear last cut flag
        if length <= 0:
            last = True     # set last cut flag
            length = step + length  # calculate end point of length of a remaining cut
            hy = math.sqrt((dia/2)**2+length**2)  # calculate hypotenuse. refer to PRT20210510002 Tangential Curve Caluculator
            ang = math.asin(dia/2/hy)   # calculate angle
            rad = hy/2/math.cos(ang)    # calculate radius of tangential curve tool path

        return (length, rad, last)

    last = False    # initialize last cut flag

    while last == False:

        # bottom length
        length_x, rad, last = length_dec(length_x, step, dia)
        if last == True:
            text_temp = \
                f'''   
        G02 X{"%.4f" % (-length_x)} Y{"%.4f" % (dia / 2)} R{"%.4f" % rad}
        G1 Y{"%.4f" % (length_y - step + dia / 2)}
        G1 X{"%.4f" % length_x}
        G1 Y{"%.4f" % (-length_y)}
        '''
            text = text + text_temp
            break
        else:
            text_temp = \
                f'''
        G1 X{"%.4f" % (-length_x)}
        G02 X{"%.4f" % (-dia / 2)} Y{"%.4f" % (dia / 2)} R{"%.4f" % (dia / 2)}
        '''
            text = text + text_temp

        # left length
        length_y, rad, last = length_dec(length_x, step, dia)
        if last == True:
            text_temp = \
    f'''
    G02 X{"%.4f" % (dia/2)} Y{"%.4f" % length_y} R{"%.4f" % rad}
    G1 X{"%.4f" % (length_x-step+dia/2)}
    G1 Y{"%.4f" % (-length_y)}
    G1 X{"%.4f" % (-length_x)}
    '''
            text = text + text_temp
            break
        else:
            text_temp = \
    f'''
    G1 Y{"%.4f" % length_y}
    G02 X{"%.4f" % (dia/2)} Y{"%.4f" % (dia/2)} R{"%.4f" % (dia/2)}
    '''
            text = text + text_temp

        # top length
        length_x, rad, last = length_dec(length_x, step, dia)
        if last == True:
            text_temp = \
    f'''
    G02 X{"%.4f" % length_x} Y{"%.4f" % (-dia/2)} R{"%.4f" % rad}
    G1 Y{"%.4f" % (-(length_y-step+dia/2))}    
    G1 X{"%.4f" % (-length_x)}
    G1 Y{"%.4f" % length_y}
    '''
            text = text + text_temp
            break
        else:
            text_temp = \
    f'''
    G1 X{"%.4f" % length_x}
    G02 X{"%.4f" % (dia/2)} Y{"%.4f" % (-dia/2)} R{"%.4f" % (dia/2)}
    '''
            text = text + text_temp

        # right length
        length_y, rad, last = length_dec(length_x, step, dia)
        if last == True:
            text_temp = \
    f'''
    G02 X{"%.4f" % (-dia/2)} Y{"%.4f" % (-length_y)} R{"%.4f" % rad}
    G1 X{"%.4f" % (-(length_x-step+dia/2))}
    G1 Y{"%.4f" % length_y}
    G1 X{"%.4f" % length_x}
    '''
            text = text + text_temp
            break
        else:
            text_temp = \
    f'''
    G1 Y{"%.4f" % (-length_y)}
    G02 X{"%.4f" % (-dia/2)} Y{"%.4f" % (-dia/2)} R{"%.4f" % (dia/2)}
    '''
            text = text + text_temp

    text_temp = \
    f'''
    G90 (absolute positioning)
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}   (Rapid to start point)
    '''
    text = text + text_temp

    text_temp = \
    f'''
    (---surfacing end---)
    '''     # write footer for section.
    text = text + text_temp
    return (text)       # return compiled text variable.

def spiral_drill(origin_x, origin_y, dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name, debug = False):

    # ---description---
    # calculates and prints to a txt file the tool path in G code of a spiral drilled hole.
    # assumes climb milling.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # starts at right edge of the hole (i.e. x = diameter of hole-dia of cutter, y = 0).
    # cuts in a counter-clockwise direction from the outside to the center.
    # starts and returns to safe_z
    # return to origin after surfacing.
    # refer to PRT20210512001 Spiral Drill
    # text = spiral_drill(origin_x, origin_y, dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name, debug)

    # ---Variable List---
    # origin_x = x of center of hole
    # origin_y = y of center of hole
    # dia_hole = hole diameter
    # depth = depth of hole (absolute convention. Negative in the downward Z direction.)
    # step_depth = step per spiral ramp. (scalar. Do NOT use negative sign.)
    # dia = diameter of cutter
    # z_f =  z feed
    # cut_f = cutting feed
    # safe_z = safe z
    # name = name of file
    # debug = False (default)

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    # rev: 01-01-01-05
    # update error checks using abort function.
    # added hole dia < tool dia check.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-09
    # added additional finishing cut.
    # software test run on 14/04/2022
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # software test run on 04/04/2022
    #
    # rev: 01-01-10-06
    # changed depth from scalar to absolute convention.
    # physical test run on TBD
    #
    # rev: 01-01-10-01
    # Added variable list
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021
    #
    # rev: 01-01-09-01
    # Changed variable name "step" to "step_depth"

    text = '\n(---spiral drill start---)\n'  # write header for section. initialize text variable.

    # description
    text_temp = \
    f'''
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a spiral drilled hole.)
    (assumes climb milling.)
    (assumes origin at center of hole.)
    (assumes z=0 at top surface.)
    (starts at right edge of the hole (i.e. x = diameter of hole-dia of cutter, y = 0).)
    (cuts in a counter-clockwise direction from the outside to the center.)
    (return to origin after surfacing.)
    (refer to PRT20210512001 Spiral Drill)
    '''
    text = text + text_temp

    # parameters
    text_temp = \
    f'''
    (---parameter---)
    (circle center: X{"%.3f" % origin_x} Y{"%.3f" % origin_y})
    (diameter: {"%.3f" % dia_hole})
    (depth: {"%.3f" % depth})
    (step_depth: {"%.3f" % step_depth})
    (diameter of cutter: {"%.3f" % dia})
    (z feed: {"%.3f" % z_f})
    (cutting feed: {"%.1f" % cut_f})
    (safe Z: {"%.3f" % safe_z})
    '''
    text = text + text_temp

    # initialize starting point
    start_x = origin_x + dia_hole/2 - dia/2
    start_y = origin_y

    # check if safe_z is above surface.
    if safe_z <= 0:
        abort('safe_z', safe_z, 'safe_z below surface')

    # check if hole dia is larger 2x tool dia.
#    if dia_hole >= dia*2:
#        abort('dia_hole',dia_hole,f'hole dia is larger 2x tool dia.\nhole dia = {"%.3f" % dia_hole}\ntool dia = {"%.3f" % dia}')

    # check if hole dia is smaller than tool dia.
    if dia_hole <= dia:
        abort('dia_hole', dia_hole, f'hole dia is smaller than tool dia.\nhole dia = {"%.3f" % dia_hole}\ntool dia = {"%.3f" % dia}')

    # starting G code block
    text_temp = \
    f'''
    (---code---)
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}   (Rapid to start point)
    F{"%.1f" % z_f}  (set to plunge feed)
    G1 Z{"%.4f" % 0} (go to starting height)
    F{"%.1f" % cut_f}  (set to cutting feed)
    '''
    text = text + text_temp

    z = 0        # initialize current depth
    depth = -depth      # convert scalar to absolute convention.

    while depth > 0:
        z = z + step_depth
        depth = depth - step_depth

        if depth > 0:
            text_temp = \
    f'''
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)} Z{"%.4f" % (-z)}
    '''
            text = text + text_temp
        else:
            z = z + depth     # calculate remainder cut
            text_temp = \
    f'''
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)} Z{"%.4f" % (-z)}
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)}   (Finishing cut)
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)}   (Finishing cut)
    G0 Z{"%.4f" % safe_z}    (go to safe Z)
    
    (---spiral drill end---)
    '''
            text = text + text_temp

            return (text)   # exit while loop at last cycle

def peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug = False):

    # ---Description---
    # calculates and prints to a txt file the tool path in G code of a peck drilled hole.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after drilling.
    # refer to ALG20210527001 Peck Drilling Algorithm
    # text = peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug)

    # ---Variable List---
    # hole_x = x of center of hole
    # hole_y = y of center of hole
    # dia_hole = hole diameter
    # depth = depth of hole (absolute convention. Negative in the downward Z direction.)
    # peck_depth = step per peck. (scalar. Do NOT use negative sign.)
    # z_f =  z feed
    # safe_z = safe z
    # retract_z = retract z after each peck.
    # dwell = dwell time in ms at retract z.
    # name = name of file
    # debug = False (default)

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    # rev: 01-01-01-04
    # Added abort function
    # software test run on 08/Mar/2023
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # software test run on 04/04/2022
    #
    # rev: 01-01-10-06
    # changed depth from scalar to absolute convention.
    # physical test run on TBD
    #
    # rev: 01-01-10-01
    # Added variable list
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # Changed last step if statement from < to <= to prevent double cutting in the event where the first cut is the last cut.
    # Changed initial starting height before drilling from "peck height" to "retract height". possible bug correction.
    # software test run on 07/Sep/2021
    # physical test run on 09/Sep/2021
    #
    # rev: 01-01-09-09
    # changed start height above surface from "1mm or less" to "1mm or peck depth, whichever is greater".
    # reorganized code.
    # added algorithm flow chart ALG20210527001 Rev01 Peck Drilling Algorithm
    #
    # rev: 01-01-09-01
    # initial release

    text = '\n(---peck drill start---)\n'  # write header for section. initialize text variable.

    # description
    text_temp = \
    f'''
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a peck drilled hole.)
    (assumes origin at center of hole.)
    (assumes z=0 at top surface.)
    (return to safe z after drilling.)
    '''
    text = text + text_temp

    # parameters
    text_temp = \
    f'''
    (---parameter---)
    (Center of hole: X{"%.4f" % hole_x} Y{"%.4f" % hole_y})
    (hole diameter: {"%.4f" % dia_hole})
    (depth: {"%.4f" % depth})
    (peck depth: {"%.4f" % peck_depth})
    (drilling feed: {"%.1f" % z_f})
    (safe Z: {"%.4f" % safe_z})
    (retract z: {"%.4f" % retract_z})
    (dwell: {dwell} ms)
    '''
    text = text + text_temp

    # check if safe_z is above surface.
    if safe_z <= 0:
        abort('safe_z', safe_z, 'safe_z below surface')

    text_temp = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % hole_x} Y{"%.4f" % hole_y}   (Rapid to start point)
    '''
    text = text + text_temp

    if peck_depth > 1 :
        text_temp = \
    f'''
    G0 Z{retract_z} (rapid to retract height: {"%.4f" % retract_z}mm above surface)
    '''
        text = text + text_temp
    else:
        text_temp = \
    f'''
    G0 Z{"%.4f" % 1} (rapid to 1mm above surface)
    '''
        text = text + text_temp

    # Initialize variables
    current_depth = 0
    target_depth = -peck_depth
    depth = -depth     # convert scalar to absolute convention.
    final_depth = -depth
    first = True
    last = False

    text_temp = \
    f'''
    F{"%.1f" % z_f} (set drilling feed)
    '''
    text = text + text_temp

    while current_depth > final_depth:

        if first == True:
            first = False   # clear first flag
        else:
            predrill_depth = current_depth + 0.1 * peck_depth    # skip if first peck
            text_temp = \
    f'''
    G0 Z{"%.4f" % predrill_depth}   (rapid to pre-drill depth)
    '''
            text = text + text_temp

        if target_depth <= final_depth:

            target_depth = final_depth
            last = True

        # drill to target depth
        text_temp = \
    f'''
    G1 Z{"%.4f" % target_depth} (drill to peck depth)
    '''
        text = text + text_temp

        if debug == True:
            print(f'current depth: {current_depth}')
            print(f'target depth: {target_depth}')
            print('')

        if last == False:

            text_temp = \
    f'''
    G0 Z{"%.4f" % retract_z} (rapid to retract height)
    G04 P{dwell}    (dwell ms)
    '''
            text = text + text_temp
            current_depth = target_depth
            target_depth = target_depth - peck_depth

        else:

            text_temp = \
    f'''
    G0 Z{"%.4f" % safe_z} (rapid to safe z)
    (---peck drill end---)
    '''
            text = text + text_temp
            return (text)       # exit while loop at last cycle

def spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, debug = False):

    # ---Description---
    # calculates and prints to a txt file the tool path in G code of a spiral surface pocket.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # start at safe_z
    # Does NOT return to safe z after surfacing!!!
    # text = spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, debug)

    # ---Variable List---
    # origin_x = x center of circular pocket
    # origin_y = y center of circular pocket
    # start_dia = diameter of entry hole assumes circular hole.
    # end_dia = end diameter circular pocket
    # doc = depth of cut (absolute convention)
    # dia = diameter of cutter
    # step = step of slice per spiral.
    # z_f = z feed
    # cut_f = cutting feed
    # finish_f = finish feed
    # finish_cuts = number of finish cuts
    # safe_z = safe z
    # name = name of file
    # debug = False (default)

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    # rev: 01-01-01-05
    # update error checks using abort function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # software test run on 04/04/2022
    #
    # rev: 01-01-10-03
    # removed round() function
    # Added selectable number of finish cuts and finishing feed rate.
    #
    # rev: 01-01-10-01
    # fixed final OD to accommodate cutter diameter.
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021
    #
    # ------------------------------
    #
    # rev: 01-01-09-02
    # initial release

    # initialize text variable.
    text = \
    f'''
    (---spiral surface start---)
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a spiral surface pocket.)
    (assumes origin at center of hole.)
    (assumes z=0 at top surface.)
    (return to safe z after surfacing.)
    (---parameters---)
    (origin: X{"%.4f" % origin_x} Y{"%.3f" % origin_y})
    (pocket diameter: {"%.3f" % end_dia})
    (depth of cut: {"%.3f" % doc})
    (step: {"%.3f" % step})
    (plunge feed: {"%.1f" % z_f})
    (cutting feed: {"%.1f" % cut_f})
    (safe Z: {"%.3f" % safe_z})
    '''

    # check if safe_z is above surface.
    if safe_z <= 0:
        abort('safe_z', safe_z, 'safe_z below surface')

    # check if start dia is larger than tool dia.
    if end_dia < dia:
        abort('end_dia', end_dia, f'end dia is smaller than tool dia.\nend dia = {"%.4f" % end_dia}\ntool dia = {"%.4f" % dia}')

    # initialize variables
    length = start_dia/2 - dia/2
    end_length = end_dia/2 - dia/2
    segments = 24   # number of segments per spiral.
    i = 360/segments
    last = False

    text_temp = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % (origin_x + length)} Y{"%.4f" % origin_y}   (Rapid to start point)
    F{"%.1f" % z_f}      (set plunge feed)
    G1 Z{"%.4f" % doc}  (go to depth of cut. Use absolute convention)
    F{"%.1f" % cut_f}    (set cutting feed)
    '''
    text = text + text_temp

    length = length + step/segments    # increment length.

    while length <= end_length:

        x, y = relative_polar(origin_x, origin_y, 0, length, i) # calculate absolute position
        text_temp = \
    f'''
    G3 X{"%.4f" % x} Y{"%.4f" % y} R{"%.4f" % length}
    '''
#        write_g_code(name, text)
        text = text + text_temp
        if debug == True:                   #!!! Added debug statement.
            print (f"length : {length}")

        if last == True:
            i = origin_x-x
            j = origin_y-y
            text_temp = \
                f'''
        G3 X{"%.4f" % x} Y{"%.4f" % y} I{"%.4f" % i} J{"%.4f" % j} F{"%.0f" % finish_f}
        (finish cut)
        '''
            i = 1
            while i <= finish_cuts:  # perform finish cuts
                text = text + text_temp
                i = i + 1
            text_temp = \
                f'''
                (---spiral surface end---)
                '''
            text = text + text_temp
            break

        length = length + step / segments  # calculate length increment per segment.
        i = i + 360 / segments  # increment step.

        if length >= end_length:
            length = end_length
            last = True
    return (text)

def corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z, name, mode = None, debug = False):

    # ---description---
    # calculates and prints to a txt file the tool path in G code of a corner slice.
    # start and end points are located at their respective center points.
    # assumes z=0 at top surface.
    # starts and returns to safe z before and after slicing.
    # return mode: 1. straight, 2. concave, 3. convex
    # refer to PRT20210515001 Corner Slice
    # text = corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z,name, mode, debug)

    # ---Variable List---
    # start_x = x center of starting circle.
    # start_y = y center of starting circle.
    # end_x = x center of ending circle.
    # end_y = y center of ending circle.
    # start_rad = starting corner radius.
    # end_rad = ending corner radius.
    # doc = depth of cut (absolute convention)
    # dia = diameter of cutter
    # step = step over per slice.
    # z_f = z feed
    # cut_f = cutting feed
    # safe_z = safe z
    # name = name of file
    # mode = tool path return mode : 1. straight, 2. concave, 3. convex
    # debug = False (default)

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    # rev: 01-01-01-05
    # Added abort function
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # software test run on 04/04/2022
    #
    # rev: 01-01-10-01
    # changed doc from scalar to absolute.
    # round of G-code to 4 decimal places.
    # changed from tool path radius to corner radius.
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021
    #
    # rev: 01-01-09-05
    # initial release

    # write header for section.
    start_block = \
    f'''
    (---corner slice start---)
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a corner slice.)
    (start and end points are located at their respective center points.)
    (assumes z=0 at top surface.)
    (return to safe z after surfacing.)
    (refer to PRT20210515001 Corner Slice)
    (---parameter---)
    (start X{"%.3f" % start_x} Y{"%.3f" % start_y})
    (end X{"%.3f" % end_x} Y{"%.3f" % end_y})
    (start rad : {"%.3f" % start_rad})
    (end rad : {"%.3f" % end_rad})
    (depth of cut: {"%.3f" % doc})
    (cutter dia : {"%.3f" % dia})
    (step: {"%.3f" % step})
    (plunge feed: {"%.1f" % z_f})
    (cutting feed: {"%.1f" % cut_f})
    (safe Z: {"%.3f" % safe_z})
    '''
    text = start_block

    # check if safe_z is above surface.
    if safe_z <= 0:
        abort('safe_z', safe_z, 'safe_z below surface')

    # check if end dia is larger than tool dia.
    if end_rad*2 < dia:
        abort('end_rad', end_rad, f'end dia is smaller than tool dia.\nend dia = {"%.4f" % (end_rad*2)}\ntool dia = {"%.4f" % dia}')

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3 :
        abort('mode', mode, 'mode undefined')

    # initialize variables
    vec_x = end_x - start_x     # x vector length of slot
    vec_y = end_y - start_y     # y vector length of slot
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)     # length of slot

    # calculate arc angle and dia angle
    start_rad = start_rad - dia/2   # calculate toolpath start radius
    end_rad = end_rad - dia/2       # calculate toolpath end radius
    adj = (start_rad-end_rad)
    hyp = math.sqrt(length**2+adj**2)
    angle_dia = math.asin((start_rad-end_rad)/hyp)*180/math.pi
    angle_arc = math.asin((start_rad-end_rad)/length)*180/math.pi

    # calculate datum position, angle and datum-edge length
    hyp = start_rad/math.sin(angle_dia*math.pi/180)
    datum_length = hyp*math.cos(angle_dia*math.pi/180)             # datum_length = length of center of start circle to apex/datum
    angle = absolute_angle(start_x, start_y, end_x, end_y, debug)   # calculate start to end angle
    datum_x = start_x + datum_length*math.cos(angle*math.pi/180)    # x coordinate of datum
    datum_y = start_y + datum_length*math.sin(angle*math.pi/180)    # y coordinate of datum
    datum_angle = angle + 180       # datum angle
    datum_edge_length = datum_length - start_rad    # calculate length from datum to edge of start arc.

    # calculate start position
    datum_length_1 = datum_length
    datum_edge_length_1 = datum_edge_length
    length_1 = datum_length_1 * math.cos(angle_arc * math.pi / 180)
    x1, y1 = relative_polar(datum_x, datum_y, datum_angle, length_1, angle_arc)

    text_temp = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % x1} Y{"%.4f" % y1}   (Rapid to start point)
    F{"%.1f" % z_f}      (set plunge feed)
    G1 Z{"%.4f" % doc}  (go to depth of cut)
    F{"%.1f" % cut_f}    (set cutting feed)
    '''
    text = text + text_temp

    # calculate datum_length_2 and rad_2
    rad_1 = start_rad
    datum_edge_length_2 = datum_edge_length_1 - step
    adj = datum_edge_length_2
    opp = adj * math.tan(angle_dia*math.pi/180)
    rad_2 = opp*adj/(adj-opp)
    datum_length_2 = rad_2 + datum_edge_length_2

    last = False
    while rad_2 >= end_rad:

        length_2 = datum_length_2 * math.cos(angle_arc*math.pi/180)
        x2, y2 = relative_polar(datum_x, datum_y, datum_angle, length_2, angle_arc)

        length_3 = length_2
        x3, y3 = relative_polar(datum_x, datum_y, datum_angle, length_3, -angle_arc)

        length_4 = datum_length_1 * math.cos(angle_arc*math.pi/180)
        x4, y4 = relative_polar(datum_x, datum_y, datum_angle, length_4, -angle_arc)

        length_1 = length_4
        x1, y1 = relative_polar(datum_x, datum_y, datum_angle, length_1, angle_arc)

        text_temp = \
    f'''
    G1 X{"%.4f" % x2} Y{"%.4f" % y2}
    G3 X{"%.4f" % x3} Y{"%.4f" % y3} R{"%.4f" % rad_2}
    G1 X{"%.4f" % x4} Y{"%.4f" % y4}
    '''
        text = text + text_temp

        if mode == 1 :
            text_temp = f'''G1 X{"%.4f" % x1} Y{"%.4f" % y1}    (straight line return)\n'''
            text = text + text_temp
        elif mode == 2 :
            text_temp = f'''G2 X{"%.4f" % x1} Y{"%.4f" % y1} R{"%.4f" % rad_1} (concave return)\n'''
            text = text + text_temp
        elif mode == 3 :
            text_temp = f'''G3 X{"%.4f" % x1} Y{"%.4f" % y1} R-{"%.4f" % rad_1}  (convex return)\n'''
            text = text + text_temp

        if last == True:
            break       # exit loop

        # increment datum_length_1
        rad_1 = rad_2
        datum_edge_length_1 = datum_edge_length_2
        datum_length_1 = datum_edge_length_1 + rad_1

        # increment datum_length_2
        # complementary angles and basic algebra
        datum_edge_length_2 = datum_edge_length_1 - step
        adj_2 = datum_edge_length_2
        opp_2 = adj_2 * math.tan(angle_dia * math.pi / 180)
        rad_2 = opp_2 * adj_2 / (adj_2 - opp_2)
        datum_length_2 = rad_2 + adj_2

        if rad_2 < end_rad:
            rad_2 = end_rad
            datum_length_2 = rad_2 / math.tan(angle_dia * math.pi/180)
            last = True

    text_temp = \
    f'''
    (---corner slice end---)
    '''
    text = text + text_temp
    return (text)

def spiral_boss(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, z_bias_mode = False, z_backlash_bias = 0, debug = False):

    # ---Description---
    # calculates and prints to a txt file the tool path in G code of a spiral boss.
    # assumes origin at center of boss.
    # assumes z=0 at top surface.
    # assumes existing clearance around material.
    # tool enters vertically at the right size of boss.
    # goes to safe z before cutting.
    # does NOT return to safe z after cutting!!!
    # text = spiral_boss(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, z_bias_mode = False, z_backlash_bias = 0, debug = False)

    # ---Variable List---
    # origin_x = x center of round boss
    # origin_y = y center of round boss
    # start_dia = diameter of starting diameter. Assumes round boss.
    # end_dia = diameter of final boss.
    # doc = depth of cut (absolute convention)
    # dia = diameter of cutter
    # step = step of slice per spiral.
    # z_f = z feed
    # cut_f = cutting feed
    # finish_f = finish feed
    # finish_cuts = number of finish cuts
    # safe_z = safe z
    # name = name of file
    # z_bias_mode = Boolean. Incorporate z backlash biasing toward bottom of backlash. Default: False. !Caution! This will overshoot depth of cut by specified value.
    # z_backlash_bias = Z value to overshoot backlash bias by. Default: 0
    # debug = False (default)

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    #
    # rev: 01-01-01-05
    # added comment on tool entry into cut.
    # update error checks using abort function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-07
    # changed from writing G-code directly to txt file to a separate text variable.
    # software test run on 04/04/2022
    #
    # rev: 01-01-10-03
    # Added z overshoot compensation
    #
    # rev: 01-01-10-02
    # Added selectable number of finish cuts and finishing feed rate.
    #
    # Added rounding
    # rev: 01-01-10-01
    # initial release
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021

    title_block = \
    f'''
    (---spiral surface start---)
    
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a spiral boss.)
    (assumes origin at center of hole.)
    (assumes z=0 at top surface.)
    (assumes existing clearance around material.)
    (tool enters vertically at the right size of boss.)
    (return to safe z after surfacing.)
    
    (---parameters---)
    (origin: X{"%.3f" % origin_x} Y{"%.3f" % origin_y})
    (boss start diameter: {"%.3f" % start_dia})
    (boss end diameter: {"%.3f" % end_dia})
    (depth of cut: {"%.3f" % doc})
    (diameter of cutter: {"%.3f" % dia})
    (step: {"%.3f" % step})
    (plunge feed: {"%.1f" % z_f})
    (cutting feed: {"%.1f" % cut_f})
    (safe Z: {"%.3f" % safe_z})
    (z_bias_mode = {z_bias_mode})
    (z_backlash_bias = {"%.3f" % z_backlash_bias})
    '''
    text = title_block

    # check if safe_z is above surface.
    if safe_z <= 0:
        abort('safe_z', safe_z, 'safe_z below surface')

    # check if end dia is larger than start dia.
    if start_dia < end_dia:
        abort('start dia', start_dia, f'end dia is larger start dia\nstart dia = {"%.4f" % start_dia}\nend dia = {"%.4f" % end_dia}')

    # initialize variables
    length = start_dia/2 + dia/2
    end_length = end_dia/2 + dia/2
    segments = 24   # number of segments per spiral.
    i = -360/segments
    last = False
    x = origin_x + length
    y = origin_y

    text_temp = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % x} Y{"%.4f" % y}   (Rapid to start point)
    F{"%.1f" % z_f}      (set plunge feed)
    '''
    text = text + text_temp

    if z_bias_mode == True:
        text_temp = \
    f'''
    G1 Z{"%.4f" % (doc+z_backlash_bias)}  (overshoot to z backlash bias)
    '''
        text = text + text_temp

    text_temp = \
    f'''
    G1 Z{"%.4f" % doc}  (go to depth of cut. Use absolute convention)
    F{"%.1f" % cut_f}    (set cutting feed)
    '''
    text = text + text_temp

    length = length - step/segments    # decrement length.

    while length >= end_length:

        x, y = relative_polar(origin_x, origin_y, 0, length, i) # calculate absolute position
        text_temp = \
    f'''
    G2 X{"%.4f" % x} Y{"%.4f" % y} R{"%.4f" % length}
    '''
        text = text + text_temp

        if debug == True:                   #!!! Added debug statement.
            print (f"length : {length}")

        if last == True:
            i = origin_x-x
            j = origin_y-y
            text_temp = \
    f'''
    G2 X{"%.4f" % x} Y{"%.4f" % y} I{"%.4f" % i} J{"%.4f" % j} F{"%.0f" % finish_f}
    (finish cut)
    '''
            i = 1
            while i <= finish_cuts:     # perform finish cuts
                text = text + text_temp
                i=i+1
            text_temp = \
    f'''
    (---spiral surface end---)
    '''
            text = text + text_temp
            break

        length = length - step/segments     # calculate length decrement per segment.
        i = i - 360/segments                  # increment step.

        if length <= end_length:
            length = end_length
            last = True
    return (text)

def format_data_frame_variable(df, var_name, row, debug=False):
    # ---Description---
    # Formats the variable from the data frame to the explicit variable type.
    # returns formatted variable.
    # var_format = format_data_frame_variable(df, var_name, counter, debug)

    # ---Variable List---
    # df = data frame
    # var_raw = unformatted variable
    # counter = counter/row indicator

    # ---Return Variable List---
    # var_format = formatted variable

    # ---Change History---
    # rev: 01-01-10-10
    # added detection for small caps.
    # software test run on 13/Aug/2022
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    def is_valid_float(element: str) -> bool:
        # ---Description---
        # Checks if contents of string is a numerical float .
        # Returns True if string is a numerical float, False if not.
        # is_valid_float(element)

        # ---Variable List---
        # element = string

        # ---Return Variable List---
        # N/A

        try:
            float(element)
            return True
        except ValueError:
            return False

    var_raw = df[var_name][row]  # import variable from dataframe
    var_raw = str(var_raw)  # convert imported variable to string.

    if debug == True:  # debug code
        print(f'row = {row}')
        print(f'var_name = {var_name}')
        print(f'var_raw = {var_raw}')
        print(f'var_raw type = {type(var_raw)}')

    if var_raw == 'None' or var_raw == 'none':
        var_format = None  # None detected.
    elif var_raw == 'False' or var_raw == 'false':
        var_format = False  # explicit boolean declaration.
    elif var_raw == 'True' or var_raw == 'true':
        var_format = True  # explicit boolean declaration.
    elif is_valid_float(var_raw) == True:  # check for numerical value
        var_format = float(var_raw)
    else:
        var_format = var_raw  # import as string.

    if debug == True:  # debug code
        print(f'var_format = {var_format}')
        print(f'var_format type = {type(var_format)}\n')

    return (var_format)  # return formatted value.

def toolpath_data_frame(name, excel_file, sheet, start_safe_z, return_safe_z, operation, dia, debug = False):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath adjusted for offset and tool diameter and prints to a txt file the linear or trochoidal tool path in G code.
    # returns last position of cutter and end position of arc.
    # refer to "ALG20220329001 Toolpath Data Frame Algorithm"
    # start and end points are located along the midline of slot for trochoidal slots.
    # positions cutter to start point and cutting depth.
    # cut at one depth of cut only for trochoidal pathway.
    # cut at variable depths for linear pathway.
    # calculates offset from edge of part profile.
    # first_x_adjusted, first_y_adjusted, end_x, end_y, cutter_x, cutter_y, text = toolpath_data_frame(name, excel_file, sheet, start_safe_z, return_safe_z, operation, dia, debug)

    # ---Variable List---
    # name = name of file
    # excel file = excel file name including file extension.
    # sheet = active excel sheet
    # start_safe_z = start_safe_z flag
    # return_safe_z = return_safe_z flag
    # operation = line or trochoidal pathway.
    # dia = diameter of cutter

    # ---Return Variable List---
    # end_x_final = x coordinate of end of slot unadjusted
    # end_y_final = y coordinate of end of slot unadjusted
    # cutter_x_final = x coordinate of cutter position
    # cutter_y_final = y coordinate of cutter position

    # ---Change History---
    #
    # rev: 01-01-01-04
    # date: 08/Mar/2023
    # description:
    # Added debug file statements
    # software test run on 08/Mar/2023
    #
    # rev: 01-01-10-12
    # Added feed rate to move cutter to start point.
    #
    # rev: 01-01-10-10
    # changed code to compliment separating line and trochoidal toolpath excel tab/ dataframe.
    # Added static_variables function to read static variables from dataframe.
    # Updated extract row function to support line/trochoidal separation.
    #
    # rev: 01-01-10-09
    # Moved format_data_frame_variable function from inside function to outside.
    # Added optional safe_z starting and ending rapid tool movement.
    #
    # rev: 01-01-10-08
    # Shifted variables to excel sheet.
    #
    # rev: 01-01-10-07
    # initial release
    # software test run on 31/Mar/2022

    def static_variables(df, tro, debug=False):
        # ---Description---
        # Extract and format static variables.
        # returns formatted variables.
        # operation_name, offset, feed, safe_z, z_f, mode, step, wos, doc = static_variables(df, tro, debug=False)

        # ---Variable List---
        # df = dataframe
        # tro = trochoidal toolpath flag.

        # ---Return Variable List---
        # operation_name = name of operation.
        # offset = cutting offset
        # feed = feedrate
        # safe_z = safe z height
        # z_f = z plunge feed
        # mode = 1 -> right side of travel, 2 -> left side of travel, 3 -> on line of travel.
        # step = trochoidal step
        # wos = width of trochoidal slot
        # doc = depth of cut (for trochoidal only)

        df.set_index('static_variable', inplace=True)  # replace index default column with static_variable column

        operation_name = format_data_frame_variable(df, 'static_value', 'operation_name', debug)  # import name of operation.
        offset = format_data_frame_variable(df, 'static_value', 'offset', debug)  # import offset.
        feed = format_data_frame_variable(df, 'static_value', 'feed', debug)  # import feed.
        safe_z = format_data_frame_variable(df, 'static_value', 'safe_z', debug)  # import safe z height.
        z_f = format_data_frame_variable(df, 'static_value', 'z_f', debug)  # import plunge feed.
        mode = format_data_frame_variable(df, 'static_value', 'mode', debug)  # import mode.
        step = None     # null
        wos = None      # null
        doc = None      # null

        if tro == True:
            step = format_data_frame_variable(df, 'static_value', 'step', debug)  # import trochoidal step.
            wos = format_data_frame_variable(df, 'static_value', 'wos', debug)  # import width of trochoidal slot.
            doc = format_data_frame_variable(df, 'static_value', 'doc', debug)  # import depth of cut (for trochoidal only)

            if isinstance(doc, float) == False:  # check if doc is a number, if not issue error.
                abort('doc', doc)

        return (operation_name, offset, feed, safe_z, z_f, mode, step, wos, doc)  # return values

    def extract_row(counter, debug=False):
        # ---Description---
        # Extract and format variables of a single row from the data frame to the explicit variable type.
        # returns formatted row of variables.
        # last_row_flag, x, y, z, arc_seg, rad, cw, less_180 = extract_row(counter)

        # ---Variable List---
        # counter = row counter

        # ---Return Variable List---
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter, debug)  # import last_row_flag value.
        x = format_data_frame_variable(df, 'x', counter, debug)  # import x value.
        y = format_data_frame_variable(df, 'y', counter, debug)  # import y value.
        x, y = shift(x, y, shift_x, shift_y)   # add shift to x, y value.

        if tro == False:
            z = format_data_frame_variable(df, 'z', counter, debug)  # import z value if line toolpath.
        elif tro == True:
            z = None         # null z value if trochoidal toolpath.

        segment = format_data_frame_variable(df, 'segment', counter, debug)  # import segment value.
        rad = format_data_frame_variable(df, 'rad', counter, debug)  # import radius.
        cw = format_data_frame_variable(df, 'cw', counter, debug)  # import clockwise flag.
        less_180 = format_data_frame_variable(df, 'less_180', counter, debug)  # import less_180 flag.

        # set or clear arc_seg flag.
        if segment == 'linear':
            arc_seg = False
        elif segment == 'arc':
            arc_seg = True
        else:
            arc_seg = None

        return (last_row_flag, x, y, z, arc_seg, rad, cw, less_180)  # return values

    if operation == 'line':                 # initialize tro flag.
        tro = False                         # line toolpath.
    elif operation == 'trochoidal':
        tro = True                          # trochoidal toolpath.
    else:
        abort('operation', operation)        # invalid operation value detected.

    df = pd.read_excel(excel_file, sheet_name = sheet, na_filter=False)      # import excel file into dataframe.
    operation_name, offset, feed, safe_z, z_f, mode, step, wos, doc = static_variables(df, tro, debug=False)  # assign static parameters.
    df = pd.read_excel(excel_file, sheet_name = sheet, na_filter=False)      # reimport excel file into dataframe. !!! workaround for restoring index.!!!

    if debug == True:       # debug
        print(f'{df}\n')

    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter

    # print static variables to debug file
    text_debug = f'\n{operation}\n'
    text_debug = text_debug + f'{sheet}\n'
    text_debug = text_debug + f'total rows: {rows}\n\n'
    text_debug = text_debug + f'static variables\n' \
                              f'offset: {offset}\n' \
                              f'feed: {feed}\n' \
                              f'safe_z: {safe_z}\n' \
                              f'z_f: {z_f}\n' \
                              f'mode: {mode}\n'
    if tro == True:
       text_debug = text_debug + f'step: {step}\n' \
                                  f'wos: {wos}\n' \
                                  f'doc: {doc}\n'
    text_debug = text_debug + '\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file


    # initialize parameters
    last_row_flag, start_x, start_y, start_z, arc_seg, rad, cw, less_180 = extract_row(counter)  # extract row 0 values.

    skip_debug = False  # initialize
    if arc_seg == False:
        segment_debug = 'linear'
    else:
        segment_debug = 'arc'
    if tro == False:     # line operation
        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, x: {start_x}, y: {start_y}, z: {start_z}, segment: {segment_debug}, rad: {rad}, cw: {cw}, less_180: {less_180}\n'  # row: 0
    else:
        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, x: {start_x}, y: {start_y}, segment: {segment_debug}, rad: {rad}, cw: {cw}, less_180: {less_180}\n'  # row: 0
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    counter = counter + 1                                           # increment counter
    last_row_flag, end_x, end_y, end_z, arc_seg, rad, cw, less_180 = extract_row(counter)  # extract row 1 values.

    start_block = \
    f'''
    (---toolpath_data_frame start---)
    (---description---)
    (Imports a 2D dataframe from an excel file, calculates the toolpath adjusted for offset and tool diameter and prints to a txt file the single or trochoidal tool path in G code.)
    (returns last position of cutter and end position of toolpath.)
    (refer to "ALG20220329001 Toolpath Data Frame Algorithm")
    (start and end points are located at the center points of toolpath.)
    (does not set cutting feed.)
    (---parameter---)            
    (cutter diameter: {"%.3f" % dia})        
    (offset: {"%.3f" % offset})
    (excel_file: {excel_file})
    (sheet: {sheet})
    '''

    text = start_block

    first_slot = True           # initialize trochodial first slot
    last_slot = False           # initialize trochodial last slot
    end_x_adjusted_pre = None   # Initialize
    end_y_adjusted_pre = None   # Initialize
    rad_adjusted = None         # Initialize

    if tro == True:             # initialize effective width of slot. Trochodial = wos, single line = tool diameter.
        effective_wos = wos
        first_z = doc           # initialize z height of starting point.
    else:
        effective_wos = dia
        first_z = start_z       # initialize z height of starting point.

    while counter <= last_row:      # recursive loop

        if skip_debug == False:  # skip if True.
            skip_debug = False  # initialize
            if arc_seg == False:
                segment_debug = 'linear'
            else:
                segment_debug = 'arc'
            if tro == False:  # line operation
                text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, x: {start_x}, y: {start_y}, z: {start_z}, segment: {segment_debug}, rad: {rad}, cw: {cw}, less_180: {less_180}\n'  # row: 0
            else:
                text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, x: {start_x}, y: {start_y}, segment: {segment_debug}, rad: {rad}, cw: {cw}, less_180: {less_180}\n'  # row: 0
            text_debug = indent(text_debug, 8)
            write_to_file(name_debug, text_debug)  # write to debug file
        elif skip_debug == True:     # reset flag.
            skip_debug = False

        if counter == last_row or last_row_flag == True:
            last_slot = True        # set last_slot = True for trochodial toolpath.

        if arc_seg == False:        # straight line segment
            start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted = linear_offset_adjustment(effective_wos, offset, start_x, start_y,end_x, end_y, mode)     # adjust line for offset and tool diameter.
        elif arc_seg == True:       # arc line segment
            start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted = arc_offset_adjustment(effective_wos, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode)     # adjust arc for offset and tool diameter.

        if counter == 1:
            cutter_x = start_x_adjusted             # initialize cutter position at first adjusted position.
            cutter_y = start_y_adjusted             # initialize cutter position at first adjusted position.
            first_x_adjusted = start_x_adjusted     # first point of the segment.
            first_y_adjusted = start_y_adjusted     # first point of the segment.
#            start_cutter = ''       # initialize
            if start_safe_z == True:
                start_cutter = \
            f'''G0 Z{"%.4f" % safe_z}				(Rapid to safe height)
            G0 X{"%.4f" % first_x_adjusted} Y{"%.4f" % first_y_adjusted}                 (Rapid to start point)
            '''
            else:
                start_cutter = \
            f'''G1 X{"%.4f" % first_x_adjusted} Y{"%.4f" % first_y_adjusted} F{feed}                 (move at cut_f to start point)
            '''

            if isinstance(first_z, float) == True:  # check if start_z is a number, if not skip.
                start_cutter = start_cutter + \
            f'''
            G1 Z{"%.4f" % first_z}	F{"%.4f" % z_f}			(Plunge to cutting height)
            '''
            start_cutter = start_cutter + \
            f'''
            F{feed}     (set cutting feed)
            '''
            text = text + start_cutter

        if debug == True:
            print(f'row/counter = {counter}')
            print(f'end_x_adjusted_pre = {end_x_adjusted_pre}')
            print(f'start_x_adjusted = {start_x_adjusted}')
            print(f'end_y_adjusted_pre = {end_y_adjusted_pre}')
            print(f'start_y_adjusted = {start_y_adjusted}')
            print(f'end_x_adjusted = {end_x_adjusted}')
            print(f'end_y_adjusted = {end_y_adjusted}')
            print(f'rad_adjusted = {rad_adjusted}')
            print(f'arc_seg = {arc_seg}')
            print(f'cw = {cw}')
            print(f'less_180 = {less_180}')
            print(f'tro = {tro}')
            print(f'start_x = {start_x}')
            print(f'start_y = {start_y}')
            print(f'start_z = {start_z}')
            print(f'end_x = {end_x}')
            print(f'end_y = {end_y}')
            print(f'end_z = {end_z}')
            print(f'mode = {mode}')
            print(f'operation = {operation}\n')

        if ((start_x_adjusted != end_x_adjusted_pre) or (start_y_adjusted != end_y_adjusted_pre)) and counter != 1:            # detect acute/non-tangent transition point excluding 1st segment.

            if debug == True:
                print('non-tangent transition detected')
                print(f'row/counter = {counter}')
                print(f'end_x_adjusted_pre = {end_x_adjusted_pre}')
                print(f'start_x_adjusted = {start_x_adjusted}')
                print(f'end_y_adjusted_pre = {end_y_adjusted_pre}')
                print(f'start_y_adjusted = {start_y_adjusted}\n')

            counter = counter - 1   # decrement counter.

            skip_debug = True   # readjustment of non-tangent transition. skip debug statement.

            # intialize parameters for transition arc.
            last_slot = False       # clear last_slot if set.
            last_row_flag = False   # clear last_row_flag if set.
            end_x_adjusted = start_x_adjusted   # intialize x end point of transition arc with start point of next toolpath segment.
            end_y_adjusted = start_y_adjusted   # intialize y end point of transition arc with start point of next toolpath segment.
            start_x_adjusted = end_x_adjusted_pre   # intialize x start point of transition arc with end point of previous toolpath segment.
            start_y_adjusted = end_y_adjusted_pre   # intialize y start point of transition arc with end point of previous toolpath segment.
            rad_adjusted = effective_wos/2 + offset # # intialize rad of transition arc to tangentially transition between the start and end point of previous and next toolpath segment respectively.
            rad_adjusted = round(rad_adjusted, 5)  # round to 5 decimal places.
            less_180 = True     # arc will never be more than 180deg.
            arc_seg = True
            end_x = start_x     # reset start x value
            end_y = start_y     # reset start y value
            end_z = None        # reset start z value. no height change during transition arc.

            if mode == 1:       # !!!! CAUTION!!!! Assumes transition arc on the external/boss profile cuts. Does not check for overlapping internal/pocket correction. !!!!!
                cw = False
            elif mode == 2:
                cw = True

        if tro == False:    # linear toolpath segment
            if arc_seg == False:
                cutter_x, cutter_y, cutter_z, text_temp = line(end_x_adjusted, end_y_adjusted, name, feed, end_z)  # print G-code for adjusted line segment.
            else:
                cutter_x, cutter_y, cutter_z, text_temp = arc(end_x_adjusted, end_y_adjusted, name, rad_adjusted, cw, less_180, feed, end_z)  # print G-code for adjusted arc segment.
        elif tro == True:       # trochoidal toolpath segment
            if arc_seg == False:
                discard, discard, cutter_x, cutter_y, text_temp = tro_slot(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, step, wos, dia, name, cutter_x, cutter_y, first_slot, last_slot)   # print G-code for adjusted trichodial line segment.
            else:
                discard, discard, cutter_x, cutter_y, text_temp = tro_arc(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, step, wos, dia, rad_adjusted, cw, less_180, name, cutter_x, cutter_y, first_slot, last_slot)     # print G-code for adjusted trichodial arc segment.
            first_slot = False      # clear first slot flag

        text = text + text_temp      # store G-code into a text variable before printing to a text file.

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if counter == last_row or break_flag == True:       # detect last row row or last row flag
            if return_safe_z == True:
                end_cutter = \
                f'''
                G0 Z{"%.4f" % safe_z}				(Rapid to safe height)
                '''
                text = text + end_cutter

            text = text + text_temp

            return (first_x_adjusted, first_y_adjusted, end_x, end_y, cutter_x, cutter_y, text)       # last point. exit function.

        counter = counter + 1                   # increment counter
        end_x_adjusted_pre = end_x_adjusted     # update previous x value
        end_y_adjusted_pre = end_y_adjusted     # update previous y value
        start_x = end_x                         # update start x value
        start_y = end_y                         # update start y value

        last_row_flag, end_x, end_y, end_z, arc_seg, rad, cw, less_180 = extract_row(counter)

def parameters_data_frame(excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, formats the text file name, parameters, start and end G-code blocks.
    # start_block, end_block, name, name_debug, clear_z, start_z, cut_f, finish_f, z_f, dia = parameters_data_frame(excel_file, sheet)

    # ---Variable List---
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # start_block = G-code start block
    # end_block = G-code end block
    # name = name of text file
    # clear_z = safe z that clears entire part. Conservative z height.
    # start_z = z height at top of part.
    # cut_f = cutting feed rate
    # finish_f = finish feed rate
    # z_f = plunge feed rate
    # dia = adjusted cutter tolerance

    # ---Change History---
    # rev: 01-01-01-05
    # Added int modifier for rev number.
    # Added written by and written on to parameters function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-01-04
    # Added debug file name generator
    # Added debug statements
    # software test run on 12/0/Mar/2023
    #
    # rev: 01-01-10-10
    # Added template file name into parameter description
    # Added parameter file name into parameter description
    # Added parameter revision number into parameter description
    #direct input of measured cutter diameter.
    # calculate cutter tolerence.
    # added valid doc value detection. must be a numerical float.
    # software test run on 13/Aug/2022
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    # ---------File Name Variables------------

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)  # import excel file into dataframe.
    df.set_index('parameter', inplace=True)  # replace index default column with parameter column
    doc_number = datetime.now().strftime("%Y%m%d-%H%M%S")  # get date time stamp (YYYYMMDD-HHMMSS) for file name.
    prefix = format_data_frame_variable(df, 'value', 'prefix')
    file_name = format_data_frame_variable(df, 'value', 'file name')
    rev = str(df['value']['revision'])
    name = prefix + doc_number + f' Rev{rev} ' + file_name  # file name
    name_debug = name + ' Debug' # debug file name

    # ---------General Variables------------

    clear_z = format_data_frame_variable(df, 'value', 'clear z')  # safe z that clears entire part. Conservative z height.
    initial_x = format_data_frame_variable(df, 'value', 'initial x')  # initial x at start of program.
    initial_y = format_data_frame_variable(df, 'value', 'initial y')  # initial y at start of program.
    start_z = format_data_frame_variable(df, 'value', 'start z')  # z height at top of part.
    terminal_x = format_data_frame_variable(df, 'value', 'terminal x')  # terminal x at end of program.
    terminal_y = format_data_frame_variable(df, 'value', 'terminal y')  # terminal y at end of program.
    cut_f = format_data_frame_variable(df, 'value', 'cutting feed')  # cutting feed rate
    z_f = format_data_frame_variable(df, 'value', 'plunge feed')  # plunge feed rate
    finish_f = format_data_frame_variable(df, 'value', 'finishing feed')  # finish feed rate
    rpm = format_data_frame_variable(df, 'value', 'spindle speed (rpm)')  # spindle speed
    cutter_dia = format_data_frame_variable(df, 'value', 'cutter diameter')  # diameter of cutter as specified.
    dia = format_data_frame_variable(df, 'value', 'measured diameter')  # measured actual cutter diameter.
    tol = dia - cutter_dia      # cutter tolerance (for reference)
    loc = format_data_frame_variable(df, 'value', 'length of cut ')  # length of flutes on cutter.
    flute = format_data_frame_variable(df, 'value', '# of flutes')  # number of flutes
    surface_speed = format_data_frame_variable(df, 'value', 'surface speed')  # Surface Speed (m/min)
    chipload = format_data_frame_variable(df, 'value', 'chipload')  # Chipload (mm/tooth)
    cutter_material = format_data_frame_variable(df, 'value', 'cutter material')  # material of cutter. e.g. HSS, carbide, cobalt
    coating = format_data_frame_variable(df, 'value', 'coating')  # coating of cutter.  e.g. None, AT, TiN
    x_origin = format_data_frame_variable(df, 'value', 'x origin')  # x origin e.g. center of part, left edge
    y_origin = format_data_frame_variable(df, 'value', 'y origin')  # y origin. e.g. center of part, bottom edge
    z_origin = format_data_frame_variable(df, 'value', 'z origin')  # z origin e.g. top surface of part, top surface of vise
    part_material = format_data_frame_variable(df, 'value', 'part material')  # material of part. e.g. Delrin, ABS, SS304, CoCr
    compiler = format_data_frame_variable(df, 'value', 'compiler')  # compiler version
    description = format_data_frame_variable(df, 'value', 'description')  # G-code description
    template_file_name = format_data_frame_variable(df, 'value', 'template file name')  # parameter template excel file name and revision
    parameter_file_name = format_data_frame_variable(df, 'value', 'parameter file name')  # parameter excel file name
    parameter_file_rev = format_data_frame_variable(df, 'value', 'parameter file revision')  # parameter excel file revision
    written_by = format_data_frame_variable(df, 'value', 'written by')  # author name
    written_on = format_data_frame_variable(df, 'value', 'written on')  # date

    text_debug = f'python script: {os.path.basename(__file__)}\n' \
                 f'file: {parameter_file_name}\n' \
                 f'rev: {int(parameter_file_rev)}\n' \
                 f'template: {template_file_name}\n\n'
    write_to_file(name_debug, text_debug)  # write to debug file

    info = \
        f'''
    (==========================)    
    (file_name: {name})
    (==========================)  

    (---Description---)
    ({description})

    (TOOL/MILL, dia: {"%.3f" % cutter_dia}, LOC:{"%.3f" % loc}, {flute} Flute, {cutter_material}, {coating})
    (--X origin: {x_origin}--)
    (--Y origin: {y_origin}--)
    (--Z origin: {z_origin}--)
    (Part material: {part_material})
    (G-code is generated using Python script "{os.path.basename(__file__)}")
    (Parameter File: {parameter_file_name})
    (Revision: {int(parameter_file_rev)})
    (Parameter File Template: {template_file_name})
    (Written by: {written_by})
    (Written on: {written_on})

    (---Compiler---)
    ({compiler})

    (---Change History---)
    (NA)    

    (---Bug List---)
    (NA)
    '''

    var = \
        f'''
    (===General variables===)
    (clear z                = {"%.3f" % clear_z})
    (initial x              = {"%.3f" % initial_x})
    (initial y              = {"%.3f" % initial_y})
    (start z                = {"%.3f" % start_z})
    (terminal x             = {"%.3f" % terminal_x})
    (terminal y             = {"%.3f" % terminal_y})
    (cut feed (default)     = {"%.1f" % cut_f})
    (plunge feed (default)  = {"%.1f" % z_f})
    (finish feed (default)  = {"%.1f" % finish_f})
    (spindle speed (default)= {"%.0f" % rpm})
    (diameter of cutter     = {"%.3f" % cutter_dia})
    (tolerance of cutter    = {"%.3f" % tol})
    (effective diameter     = {"%.3f" % dia})
    (Surface Speed          = {"%.0f" % surface_speed} m/min (reference))
    (Chipload               = {"%.3f" % chipload} mm/tooth (reference))
    '''

    start_block = \
        f'''
    (start block)
    G90			   (Absolute XYZ)
    G21G64G17	   (mm, Best Speed Path, XY Plane)
    M3 S{rpm}      (Spindle Speed)
    G0 Z{"%.4f" % clear_z}   (Go to safe height)
    G0 X{"%.4f" % initial_x} Y{"%.4f" % initial_y}   (Rapid to start point)

    (===Main Start===)
    '''

    text = info + var  # initialize text variable.
    write_to_file(name, text)

    end_block = \
        f'''
    (===Main End===)

    (end block)
    G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
    G0 X{"%.4f" % terminal_x} Y{"%.4f" % terminal_y}        (Rapid to end point)
    M5						    (Spindle Stop)
    M30					        (End & Rewind)
    '''

    return (start_block, end_block, name, name_debug, clear_z, start_z, cut_f, finish_f, z_f, dia)

def peck_drill_data_frame(name, excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for peck drilling multiple holes in G code.
    # starts at safe z.
    # returns to safe z.

    # ---Variable List---
    # name = name of file
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # N/A

    # ---Change History---
    #
    # rev: 01-01-01-04
    # date: 08/Mar/2023
    # description:
    # Added debug file statements
    # software test run on 08/Mar/2023
    #
    # rev: 01-01-01-03
    # date: 23/Feb/2023
    # description:
    # Fixed bug on repeat g-code generation in peck drill data frame
    # software test run on 23/Feb/2023
    #
    # rev: 01-01-01-02
    # Added last row detect
    # software test run on TBD
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)
    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter
    text = ''             # initialize

    text_debug = f'\n{operation}\n'
    text_debug = text_debug + f'{sheet}\n'
    text_debug = text_debug + f'total rows: {rows}\n\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    while counter <= last_row:

        # import parameters from excel file.
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter)
        hole_x = format_data_frame_variable(df, 'x', counter)
        hole_y = format_data_frame_variable(df, 'y', counter)
        dia_hole = format_data_frame_variable(df, 'dia_hole', counter)
        depth = format_data_frame_variable(df, 'depth', counter)
        peck_depth = format_data_frame_variable(df, 'peck_depth', counter)
        z_f = format_data_frame_variable(df, 'z_f', counter)
        safe_z = format_data_frame_variable(df, 'safe_z', counter)
        retract_z = format_data_frame_variable(df, 'retract_z', counter)
        dwell = format_data_frame_variable(df, 'dwell', counter)

        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, x: {hole_x}, y: {hole_y}, dia_hole: {dia_hole}, depth: {depth}, peck_depth: {peck_depth}, z_f: {z_f}, safe_z: {safe_z}, retract_z: {retract_z}, dwell: {dwell}\n'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

        # generate G-code
        text_temp = peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name)
        text = text + text_temp

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if break_flag == True:  # break if last row
            text = text + text_temp
            break

        counter = counter + 1  # increment counter.

    write_to_file(name, text)

def surface_data_frame(name, excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for surfacing a rectangular work piece in G code.
    # starts at safe z.
    # returns to safe z.

    # ---Variable List---
    # name = name of file
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-05
    # Added error text file statements to surface dataframe function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-10
    # added cut_f parameter import from excel file.
    # software test run on 13/Aug/2022
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)
    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter
    text = ''             # initialize

    text_debug = f'\n{operation}\n'\
                 f'{sheet}\n'\
                 f'total rows: {rows}\n\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    while counter <= last_row:

        # import parameters from excel file.
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter)
        origin_x = format_data_frame_variable(df, 'origin_x', counter)
        origin_y = format_data_frame_variable(df, 'origin_y', counter)
        length_x = format_data_frame_variable(df, 'length_x', counter)
        length_y = format_data_frame_variable(df, 'length_y', counter)
        doc = format_data_frame_variable(df, 'doc', counter)
        step = format_data_frame_variable(df, 'step', counter)
        cut_f = format_data_frame_variable(df, 'cut_f', counter)
        safe_z = format_data_frame_variable(df, 'safe_z', counter)

        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, origin_x: {origin_x}, origin_y: {origin_y}, length_x: {length_x}, length_y: {length_y}, doc: {doc}, step: {step}, cut_f: {cut_f}, safe_z: {safe_z}\n'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

        # generate G-code
        text_temp = surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name)
        text = text + text_temp

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if break_flag == True:  # break if last row
            text = text + text_temp
            break

        counter = counter + 1  # increment counter.

    write_to_file(name, text)

def spiral_drill_data_frame(name, excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for spiral drilling multiple holes in G code.
    # starts at safe z.
    # returns to safe z.

    # ---Variable List---
    # name = name of file
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-05
    # Added error text file statements to spiral drill function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)
    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter
    text = ''             # initialize

    text_debug = f'\n{operation}\n'\
                 f'{sheet}\n'\
                 f'total rows: {rows}\n\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    while counter <= last_row:

        # import parameters from excel file.
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter)
        origin_x = format_data_frame_variable(df, 'origin_x', counter)
        origin_y = format_data_frame_variable(df, 'origin_y', counter)
        dia_hole = format_data_frame_variable(df, 'dia_hole', counter)
        depth = format_data_frame_variable(df, 'depth', counter)
        step_depth = format_data_frame_variable(df, 'step_depth', counter)
        cut_f = format_data_frame_variable(df, 'cut_f', counter)
        safe_z = format_data_frame_variable(df, 'safe_z', counter)

        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, origin_x: {origin_x}, origin_y: {origin_y}, dia_hole: {dia_hole}, depth: {depth}, step_depth: {step_depth}, cut_f: {cut_f}, safe_z: {safe_z}\n'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

        # generate G-code
        text_temp = spiral_drill(origin_x, origin_y, dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name)
        text = text + text_temp

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if break_flag == True:  # break if last row
            text = text + text_temp
            break

        counter = counter + 1  # increment counter.

    write_to_file(name, text)

def spiral_surface_data_frame(name, excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for a spiral surfacing a part in G code.
    # starts at safe z.
    # returns to safe z.

    # ---Variable List---
    # name = name of file
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-05
    # Added error text file statements to spiral surface dataframe function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)
    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter
    text = ''             # initialize

    text_debug = f'\n{operation}\n'\
                 f'{sheet}\n'\
                 f'total rows: {rows}\n\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    while counter <= last_row:

        # import parameters from excel file.
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter)
        origin_x = format_data_frame_variable(df, 'origin_x', counter)
        origin_y = format_data_frame_variable(df, 'origin_y', counter)
        start_dia = format_data_frame_variable(df, 'start_dia', counter)
        end_dia = format_data_frame_variable(df, 'end_dia', counter)
        doc = format_data_frame_variable(df, 'doc', counter)
        step = format_data_frame_variable(df, 'step', counter)
        cut_f = format_data_frame_variable(df, 'cut_f', counter)
        finish_f = format_data_frame_variable(df, 'finish_f', counter)
        finish_cuts = format_data_frame_variable(df, 'finish_cuts', counter)
        safe_z = format_data_frame_variable(df, 'safe_z', counter)

        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, origin_x: {origin_x}, origin_y: {origin_y}, start_dia: {start_dia}, end_dia: {end_dia}, doc: {doc}, step: {step}, cut_f: {cut_f}, finish_f: {finish_f}, finish_cuts: {finish_cuts}, safe_z: {safe_z}\n'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

        # generate G-code
        text_temp = spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name)
        text = text + text_temp

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if break_flag == True:  # break if last row
            text = text + text_temp
            break

        counter = counter + 1  # increment counter.

    write_to_file(name, text)

def corner_slice_data_frame(name, excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for corner slicing part in G code.
    # starts at safe z.
    # returns to safe z.

    # ---Variable List---
    # name = name of file
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-05
    # Added error text file statements to spiral surface dataframe function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)
    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter
    text = ''             # initialize

    text_debug = f'\n{operation}\n'\
                 f'{sheet}\n'\
                 f'total rows: {rows}\n\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file


    while counter <= last_row:

        # import parameters from excel file.
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter)
        start_x = format_data_frame_variable(df, 'start_x', counter)
        start_y = format_data_frame_variable(df, 'start_y', counter)
        end_x = format_data_frame_variable(df, 'end_x', counter)
        end_y = format_data_frame_variable(df, 'end_y', counter)
        start_rad = format_data_frame_variable(df, 'start_rad', counter)
        end_rad = format_data_frame_variable(df, 'end_rad', counter)
        doc = format_data_frame_variable(df, 'doc', counter)
        step = format_data_frame_variable(df, 'step', counter)
        cut_f = format_data_frame_variable(df, 'cut_f', counter)
        mode = format_data_frame_variable(df, 'mode', counter)
        safe_z = format_data_frame_variable(df, 'safe_z', counter)

        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}, start_rad: {start_rad}, end_rad: {end_rad}, doc: {doc}, step: {step}, cut_f: {cut_f}, mode: {mode}, safe_z: {safe_z}\n'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

        # generate G-code
        text_temp = corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z, name, mode)
        text = text + text_temp

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if break_flag == True:  # break if last row
            text = text + text_temp
            break

        counter = counter + 1  # increment counter.

    write_to_file(name, text)

def spiral_boss_data_frame(name, excel_file, sheet):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for cutting a spiral boss in G code.
    # starts at safe z.
    # returns to safe z.

    # ---Variable List---
    # name = name of file
    # excel_file = excel file name
    # sheet = excel sheet name

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-05
    # Added error text file statements to spiral boss function.
    # software test run on 11/Mar/2023
    #
    # rev: 01-01-10-09
    # initial release
    # software test run on 14/Apr/2022

    df = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)
    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter
    text = ''             # initialize

    text_debug = f'\n{operation}\n'\
                 f'{sheet}\n'\
                 f'total rows: {rows}\n\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    while counter <= last_row:

        # import parameters from excel file.
        last_row_flag = format_data_frame_variable(df, 'last_row_flag', counter)
        origin_x = format_data_frame_variable(df, 'origin_x', counter)
        origin_y = format_data_frame_variable(df, 'origin_y', counter)
        start_dia = format_data_frame_variable(df, 'start_dia', counter)
        end_dia = format_data_frame_variable(df, 'end_dia', counter)
        doc = format_data_frame_variable(df, 'doc', counter)
        step = format_data_frame_variable(df, 'step', counter)
        cut_f = format_data_frame_variable(df, 'cut_f', counter)
        finish_f = format_data_frame_variable(df, 'finish_f', counter)
        finish_cuts = format_data_frame_variable(df, 'finish_cuts', counter)
        safe_z = format_data_frame_variable(df, 'safe_z', counter)

        text_debug = f'row: {counter}, last_row_flag: {last_row_flag}, origin_x: {origin_x}, origin_y: {origin_y}, start_dia: {start_dia}, end_dia: {end_dia}, doc: {doc}, step: {step}, cut_f: {cut_f}, finish_f: {finish_f}, finish_cuts: {finish_cuts}, safe_z: {safe_z}\n'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

        # generate G-code
        text_temp = spiral_boss(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name)
        text = text + text_temp

        break_flag, text_temp = last_row_detect(df, sheet, last_row_flag, last_row, counter, 8)  # detect last row
        if break_flag == True:  # break if last row
            text = text + text_temp
            break

        counter = counter + 1  # increment counter.

    write_to_file(name, text)

def rapid(name, df_main, counter):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath for a rapid movement in G code.

    # ---Variable List---
    # name = name of file
    # df_main = data frame. main tab
    # counter = row counter

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-06
    # date: 12/Mar/2023
    # description:
    # Added 'None' as a valid variable.
    # detect of x,y,z are all None then do not print g-code G0
    # software test run on 12/Mar/2023
    #
    # rev: 01-01-01-04
    # date: 08/Mar/2023
    # description:
    # Added debug file statements
    # found and fixed variable type check bug
    # software test run on 08/Mar/2023
    #
    # rev: 01-01-10-10
    # initial release
    # software test run on 11/Aug/2022

    operation_debug = format_data_frame_variable(df_main, 'operation', counter)
    text_debug = f'\n{operation_debug}\n'
    text_debug = indent(text_debug, 8)
    write_to_file(name_debug, text_debug)  # write to debug file

    x = format_data_frame_variable(df_main, 'x', counter)
    y = format_data_frame_variable(df_main, 'y', counter)
    z = format_data_frame_variable(df_main, 'z', counter)
    x, y = shift(x, y, shift_x, shift_y)  # add shift to x,y value.

    if x == None and y == None and z ==None:
        text = ''   #
    else:
        text = f'G0 '  # G0 rapid command

    if isinstance(x, float) == True:  # check if x is a number, if not skip.
        text = text + f' X{"%.4f" % x}'  # append x position
        text_debug = f'x: {x}, '
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file
    elif x == None: # check if x is 'None', if not skip.
        text_debug = f'x: {x}, '
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file
    else:
        abort('x', x, 'not float or None')

    if isinstance(y, float) == True:  # check if y is a number, if not skip.
        text = text + f' Y{"%.4f" % y}'  # append y position
        text_debug = f'y:{y}, '
        write_to_file(name_debug, text_debug)  # write to debug file
    elif y == None:  # check if y is 'None', if not skip.
        text_debug = f'y: {y}, '
        write_to_file(name_debug, text_debug)  # write to debug file
    else:
        abort('y', y, 'not float or None')

    if isinstance(z, float) == True:  # check if z is a number, if not skip.
        text = text + f' Z{"%.4f" % z}'  # append z position
        text_debug = f'z:{z}'
        write_to_file(name_debug, text_debug)  # write to debug file
    elif z == None: # check if z is 'None', if not skip.
        text_debug = f'z: {z}'
        write_to_file(name_debug, text_debug)  # write to debug file
    else:
        abort('z', z, 'not float or None')

    text = text + '         (Rapid)\n'
    write_to_file(name, text)       # write g-code

def last_row_detect(df_temp, sheet_temp, last_row_flag, last_row, counter, indent_spacing = 0):
    # ---Description---
    # Detects the last row of dataframe.
    # additionally detects unintentional termination of a dataframe.
    # returns break_flag, comments in G-code, and prints to debug window.
    # break_flag, text = last_row_detect(df_temp, sheet_temp, last_row_flag, last_row, counter, indent_spacing)

    # ---Variable List---
    # df_temp = active data frame
    # sheet_temp = active sheet
    # last_row_flag = last row flag
    # last_row = total number of rows in the dataframe
    # counter = row counter
    # indent_spacing = indent spacing for debug file statements

    # ---Return Variable List---
    # break_flag = flag signalling the detection of the last row.
    # text = returns type of termination

    # ---Change History---
    #
    # rev: 01-01-01-04
    # date: 08/Mar/2023
    # description:
    # Added debug file statements
    # Added debug file indent spacing variable.
    # software test run on 08/Mar/2023
    #
    # rev: 01-01-10-11
    # fixed data frame bug.
    # added active dataframe and active sheet as pass in variables.
    # software test run on 15/Aug/2022
    #
    # rev: 01-01-10-10
    # initial release
    # software test run on 11/Aug/2022

    break_flag = False      # initialize. clear break flag
    text = ''                 # initialize.
    if last_row_flag == True:                                                           # detect last row to terminate program.
        if counter < last_row:
            row = format_data_frame_variable(df_temp, '#', counter)
            print(f'''early termination of row\nsheet: {sheet_temp}\nrow #: {"%.0f" % row}\n''')   # premature program termination
            text = f'''\n(early termination of row)\n(sheet: {sheet_temp})\n(row #: {"%.0f" % row})\n'''  # to G-code text file
            text_debug = 'early termination of row'
            text_debug = indent(text_debug, indent_spacing)
            write_to_file(name_debug, text_debug)                                                # write to debug file
        else:
            print(f'''last row processed\nnormal termination of program\nsheet: {sheet_temp}\n''')    # normal expected program termination
            text = f'''\n(last row processed)\n(normal termination of program)\n(sheet: {sheet_temp})\n'''  # to G-code text file
            text_debug = 'last row processed. normal termination of program.'
            text_debug = indent(text_debug, indent_spacing)
            write_to_file(name_debug, text_debug)                                                # write to debug file
        break_flag = True       # set break flag
    if counter == last_row and break_flag == False:
        print(f'''last row detected and processed\nlast_row_flag not detected!\nunexpected termination of program\nsheet: {sheet_temp}\n''')  # unexpected program termination. last_row_flag not detected
        text = f'''\n(last row detected and processed)\n(last_row_flag not detected!)\n(unexpected termination of program)\n(sheet: {sheet_temp})\n'''  # to G-code text file
        text_debug = 'last row detected and processed. last_row_flag not detected!'
        text_debug = indent(text_debug, indent_spacing)
        write_to_file(name_debug, text_debug)                                                # write to debug file

        break_flag = True       # set break flag
    return (break_flag, text)

def indent(text, amount, ch=' '):
    # ---Description---
    # Pads a text variable with defined blank spaces.
    # text = indent(text, amount)

    # ---Variable List---
    # text = import text string
    # amount = number of blank spaces to pad

    # ---Return Variable List---
    # text = import text with padded blank spaces in front

    # ---Change History---
    # rev: 01-01-01-04
    # Initial release
    # software test run on 08/Mar/2023

    return textwrap.indent(text, amount * ch)

def abort(variable_name, variable, error_message = None):
    # ---Description---
    # Aborts the program and print an error message on the debug window, G-code text file and debug text file.
    # abort(variable_name, variable, error_message)

    # ---Variable List---
    # variable_name = name of variable
    # variable = value of variable
    # error_message = optional error message

    # ---Return Variable List---
    # N/A

    # ---Change History---
    # rev: 01-01-01-04
    # Initial release
    # software test run on 08/Mar/2023

    print(f'''!!SCRIPT ABORTED!!\ninvalid {variable_name} value detected.\n{variable_name}: {variable}\n{error_message}''')     # print error message in debug window

    text = f'''\n(!!SCRIPT ABORTED!!)\n(invalid {variable_name} value detected.)\n({variable_name}: {variable})\n'''  # write error message to G-code
    if error_message != None:
        text = text + f'({error_message})'
    write_to_file(name, text)

    text_debug = f'\n!!SCRIPT ABORTED!!\ninvalid {variable_name} value detected.\n{variable_name}: {variable}\n'         # write error message in debug file
    if error_message != None:
        text_debug = text_debug + error_message
    write_to_file(name_debug, text_debug)  # write to debug file

    quit()          # quit program

def shift(x, y, shift_x, shift_y):
    # ---Description---
    # Shift origin point by x and y distance.
    # Shift is accumulative.

    # ---Variable List---
    # x = x value as read.
    # y = y value as read.
    # shift_x = distance to shift x by
    # shift_y = distance to shift y by

    # ---Return Variable List---
    # shifted_x = adjusted/shifted x
    # shifted_y = adjusted/shifted y

    # ---Change History---
    #
    # rev: 01-01-01-06
    # date: 12/Mar/2023
    # description:
    # initial release
    # software test run on 12/Mar/2023

    if x == None or shift_x == None:
        shifted_x = x                  # do nothing
    else:
        shifted_x = x + shift_x         # shift x
    if y == None or shift_y == None:
        shifted_y = y                   # do nothing
    else:
        shifted_y = y + shift_y         # shift y

    return (shifted_x, shifted_y)

# ---------Import Parameters------------

excel_file = 'LOG20220414001 G-code Parameters.xlsx'       # !!!! identify name of excel file to import data from. !!!!
sheet = 'parameters'                # identify name of excel sheet to import data from.
start_block, end_block, name, name_debug, clear_z, start_z, cut_f, finish_f, z_f, dia = parameters_data_frame(excel_file, sheet)        # generate G-code parameters.

text_debug = f'read excel {sheet} tab\n'
write_to_file(name_debug, text_debug)    # write to debug file

write_to_file(name, start_block)    # write G-code start block

text_debug = 'write g-code start_block\n'
write_to_file(name_debug, text_debug)    # write to debug file
# ===========================================================================
# ================================ G-code start =============================
# ===========================================================================

sheet = 'main'
df_main = pd.read_excel(excel_file, sheet_name=sheet, na_filter=False)  # import excel file, main sheet, into dataframe. no na_filter/ blank cell filter.
rows = df_main.shape[0]  # total number of rows in dataframe.
last_row = rows - 1  # initialize number of last row
counter = 0  # initialize counter
shift_x = 0  # initialize shift x
shift_y = 0  # initialize shift y

text_debug = f'read excel "{sheet}" tab\n\n'
write_to_file(name_debug, text_debug)    # write to debug file
text_debug = f'{sheet}\n' \
             f'total rows: {rows}\n'
text_debug = indent(text_debug, 4)
write_to_file(name_debug, text_debug)    # write to debug file

# import content of excel file.
while counter<=last_row:

    operation = format_data_frame_variable(df_main, 'operation', counter)       # import operation from excel file.
    operation_valid_flag = False    # initialize flag

    last_row_flag_debug = format_data_frame_variable(df_main, 'last_row_flag', counter)       # import last_row flag from excel file for debug file.
    sheet_debug = format_data_frame_variable(df_main, 'sheet_name', counter)       # import sheet_name from excel file for debug file.
    text_debug = f'\nrow #: {counter}, last_row flag: {last_row_flag_debug}, operation: {operation}, sheet: {sheet_debug}\n'
    text_debug = indent(text_debug,4)
    write_to_file(name_debug, text_debug)  # write to debug file

    if operation == 'line' or operation == 'trochoidal':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        start_safe_z = format_data_frame_variable(df_main, 'start_safe_z', counter)     # pass start_safe_z to toolpath_data_frame. starts from safe z height if set.
        if isinstance(start_safe_z, bool) == False:  # check if start_safe_z is a boolean, if not issue error.
            abort('start_safe_z', start_safe_z)  # abort. write error message.

        return_safe_z = format_data_frame_variable(df_main, 'return_safe_z', counter)     # pass return_safe_z to toolpath_data_frame. returns to safe z height if set.
        if isinstance(return_safe_z, bool) == False:  # check if return_safe_z is a boolean, if not issue error.
            abort('return_safe_z', return_safe_z)  # abort. write error message.

        first_x_adjusted, first_y_adjusted, end_x, end_y, cutter_x, cutter_y, text = toolpath_data_frame(name, excel_file, sheet, start_safe_z, return_safe_z, operation, dia, debug = False)
        write_to_file(name, text)

    elif operation == 'drill':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        peck_drill_data_frame(name, excel_file, sheet)

    elif operation == 'surface':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        surface_data_frame(name, excel_file, sheet)

    elif operation == 'spiral_drill':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        spiral_drill_data_frame(name, excel_file, sheet)

    elif operation == 'spiral_surface':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        spiral_surface_data_frame(name, excel_file, sheet)

    elif operation == 'corner_slice':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        corner_slice_data_frame(name, excel_file, sheet)

    elif operation == 'spiral_boss':
        operation_valid_flag = True  # set flag
        sheet = format_data_frame_variable(df_main, 'sheet_name', counter)
        spiral_boss_data_frame(name, excel_file, sheet)

    elif operation == 'clear_z':
        operation_valid_flag = True  # set flag
        text = f'G0 Z{clear_z}          (Clear Z)\n'
        write_to_file(name, text)

        text_debug = f'\n{operation}\n' \
                     f'z: {clear_z}'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

    elif operation == 'rapid':
        operation_valid_flag = True  # set flag
        rapid(name, df_main, counter)

    elif operation == 'shift':

        temp_x = format_data_frame_variable(df_main, 'x', counter)
        if temp_x == None:
            shift_x = shift_x    # do nothing
        elif isinstance(temp_x, float) == True:  # check if temp_x is a number
            shift_x = temp_x + shift_x    # distance to adjust x with. accumulative.
        else:
            abort('shift_x', temp_x, 'not float or None')

        temp_y = format_data_frame_variable(df_main, 'y', counter)
        if temp_y == None:
            shift_y = shift_y    # do nothing
        elif isinstance(temp_y, float) == True:  # check if temp_y is a number
            shift_y = temp_y + shift_y    # distance to adjust y with. accumulative.
        else:
            abort('shift_y', temp_y, 'not float or None')

        operation_valid_flag = True  # set flag
        text_debug = f'\n{operation}\n' \
                     f'x: {temp_x}, y: {temp_y}\n' \
                     f'shift_x: {shift_x}, shift_y: {shift_y}'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

    elif operation == 'clear_shift':
        shift_x = 0    # clear shift x value.
        shift_y = 0    # clear shift y value.
        operation_valid_flag = True  # set flag
        text_debug = f'\n{operation}\n' \
                     f'shift_x: {shift_x}, shift_y: {shift_y}'
        text_debug = indent(text_debug, 8)
        write_to_file(name_debug, text_debug)  # write to debug file

    if operation_valid_flag == False:  # check for invalid operation.
        abort('operation', operation)   # abort. write error message.

    last_row_flag = format_data_frame_variable(df_main, 'last_row_flag', counter)       # import last_row flag from excel file.
    sheet = 'main'
    write_to_file(name_debug, '\n')  # empty line for debug file readability.
    break_flag, text = last_row_detect(df_main, sheet, last_row_flag, last_row, counter, 4)        # detect last row in main excel tab
    if break_flag == True:                                                  # break if last row
        write_to_file(name, text)
        break

    counter = counter+1     # increment counter.

# ===========================================================================
# ================================ G-code end ===============================
# ===========================================================================

write_to_file(name, end_block)      # write G-code end block
text_debug = '\n\nwrite g-code end_block\n'
write_to_file(name_debug, text_debug)    # write to debug file