# =============================== Title Block ===============================
#
# file name: SRC20210420001 G-code Generator
#
# ---Description---
#   Generate G-code for basic toolpaths.
#
# ---Change History---
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

def line(end_x, end_y, name, feed = None, ramp_z = None, start_z = None):

    # ---Description---
    # Calculates and prints G-code of a straight line.
    # Optional z direction ramp. !! Note: ramp_z is in relative units. !!
    # Optional feed rate.
    # returns cutter position
    # cutter_x, cutter_y, cutter_z, text = line(end_x, end_y, name, feed, ramp_z, start_z)

    # ---Variable List---
    # end_x = x end of line
    # end_y = y end of line
    # name = name of file
    # feed = cutting feed. (Optional)
    # ramp_z = Z end of line. (Optional)

    # ---Return Variable List---
    # cutter_x = current cutter x position
    # cutter_y = current cutter y position
    # cutter_z = current cutter z position
    # text = G-code text

    # ---Change History---
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
    if ramp_z != None and start_z == None:              # check for start_z definition.
        print(f"!!script aborted!!\nline function\nstart_z undefined\nstart_z = {start_z}")
        text = '''\n(!!script aborted!!)\n(start_z undefined)\n'''  # write header for section.
        quit()
    text = f'''G1 X{"%.4f" % end_x} Y{"%.4f" % end_y}'''

    if ramp_z != None:
        end_z = start_z + ramp_z               # calculate absolute z position
        text_temp = f''' Z{"%.4f" % end_z}'''  # optional z ramp
        text = text + text_temp

    if feed != None:
        text_temp = f''' F{"%.0f" % feed}'''    # optional feed
        text = text + text_temp

    text = text + "\n"      # new line

    cutter_x = end_x
    cutter_y = end_y
    if ramp_z == None:
        cutter_z = None
    elif ramp_z != None:
        cutter_z = end_z

    return(cutter_x, cutter_y, cutter_z, text)        # returns cutter position

def arc(end_x, end_y, name, rad, cw, less_180, feed = None, ramp_z = None, start_z = None):

    # ---Description---
    # Calculates and prints G-code of an arc.
    # Optional z direction ramp. !! Note: ramp_z is in relative units. !!
    # Optional feed rate.
    # returns cutter position
    # cutter_x, cutter_y, cutter_z, text = arc(end_x, end_y, name, rad, cw, less_180, feed, ramp_z, start_z)

    # ---Variable List---
    # end_x = x end of line
    # end_y = y end of line
    # name = name of file
    # rad = radius of arc
    # cw = Boolean. True = clockwise False = counter clockwise.
    # less_180 = Boolean. True: < 180deg False: > 180deg.
    # feed = cutting feed. (Optional)
    # ramp_z = Z end of line. (Optional)
    # ramp_z = Z end of line. (Optional)

    # ---Return Variable List---
    # cutter_x = adjusted start x position/ cutter x position
    # cutter_y = adjusted start y position/ cutter y position
    # cutter_z = adjusted start z position/ cutter z position
    # text = G-code text

    # ---Change History---
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
    if ramp_z != None and start_z == None:
        print(f"!!script aborted!!\narc function\nstart_z undefined\nstart_z = {start_z}")
        text = '''\n(!!script aborted!!)\n(start_z undefined)\n'''  # write header for section.
        quit()

    if less_180 == True:
        rad_adjusted = rad     # acute arc. G-code convention: positive radius = minor arc.
    if less_180 == False:
        rad_adjusted = -rad    # obtuse arc. G-code convention: negative radius = major arc.

    if cw == True:
        dir = '02'
    elif cw == False:
        dir = '03'

    text = f'''G{dir} X{"%.4f" % end_x} Y{"%.4f" % end_y} R{"%.4f" % rad_adjusted}'''

    if ramp_z != None:
        end_z = start_z + ramp_z                # calculate absolute z position
        text_temp = f''' Z{"%.4f" % end_z}'''   # optional z ramp
        text = text + text_temp

    if feed != None:
        text_temp = f''' F{"%.0f" % feed}'''    # optional feed
        text = text + text_temp

    text = text + "\n"      # new line

    cutter_x = end_x
    cutter_y = end_y
    if ramp_z == None:
        cutter_z = None
    elif ramp_z != None:
        cutter_z = end_z

    return(cutter_x, cutter_y, cutter_z, text)        # returns cutter position

def tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, cutter_x, cutter_y, first_slot = True, last_slot = True, debug = False):
    
   # ---Description---
   # Calculates and prints to a txt file the trichoidal tool path in G code of a straight slot.
   # returns last position of cutter and end position of slot.
   # start and end points are located along slot arc center/neutral axis.
   # assumes that cutter is at cutting depth.
   # does NOT return to safe z.
   # end_x_original, end_y_original, cutter_x_final, cutter_y_final, text = tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, cutter_x, cutter_y, first_slot, last_slot, debug)

   # ---Variable List---
   # start_x = x start of slot along neutral axis
   # start_y = y start of slot along neutral axis
   # end_x = x end of slot along neutral axis
   # end_y = y end of slot along neutral axis
   # step = depth of step per trichoidal slice.
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
    (---trichoidal linear slot start---)                                                                                                                                                                                                                     
    (---description---)
    (Calculates and prints to a txt file the trichoidal tool path in G code of a straight slot.)                                                                                                         
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
        print("Function: trichoidal")
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

        # write G code of rest of trichoidal loop
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
    f'''(---trichoidal linear slot end---)
    '''
    text = text + text_temp         # append to text variable

    return (end_x_original, end_y_original, cutter_x_final, cutter_y_final, text)

def tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot = True, last_slot = True, debug = False):

   # ---Description---
   # Calculates and prints to a txt file the trichoidal tool path in G code of a circular arc.
   # returns last position of cutter and end position of arc.
   # refer to "PRT20210421001 Trichoidal Arc Calculator", "MEM20210522001 Trichoidal Arc", "MEM20210429002 Trichoidal Notes", "ALG20210520001 Trichoidal Arc Algorithm"
   # start and end points are located at slot arc center points.
   # assumes that cutter is at cutting depth.
   # does not return to safe z.
   # does not set cutting feed.
   # end_x_original, end_y_original, cutter_x_final, cutter_y_final, text = tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot, last_slot, debug)

   # ---Variable List---
   # start_x = x start of arc along neutral axis
   # start_y = y start of arc along neutral axis
   # end_x = x end of arc along neutral axis
   # end_y = y end of arc along neutral axis
   # step = depth of step per trichoidal slice.
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
    f'''(---trichoidal arc slot start---)
    (---description---)
    (Calculates and prints to a txt file the trichoidal tool path in G code of a counter clockwise arc.)
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
        print(f'''!!script aborted!!\ntri_arc\nwidth of slot is smaller tool dia.\nwidth of slot= {"%.3f" % wos}\ntool dia = {"%.3f" % dia}''')
        text = '''\n(!!script aborted!!)\n(width of slot is smaller tool dia)\n'''  # write header for section.
        quit()

    skip_1 = False   # initialize skip_1 flag

    vec_x = end_x - start_x
    vec_y = end_y - start_y
    linear_length = math.sqrt(vec_x ** 2 + vec_y ** 2)      # calculate linear length from start point to end point

    # check if diameter of arc is larger than linear length
    if rad_slot*2 < linear_length:
        print(f'''!!script aborted!!\ntri_arc\ndiameter of arc is smaller than linear length.\ndiameter of arc = {"%.3f" % (rad_slot*2)}\nlinear length = {"%.3f" % linear_length}''')
        text = '''\n(!!script aborted!!)\n(diameter of arc is smaller than linear length)\n'''  # write header for section.
        quit()

    slot_angle = 2 * math.degrees(math.asin(( linear_length / 2) / rad_slot))  # acute arc angle
    if less_180 == False:
        slot_angle = 360 - slot_angle     # obtuse arc angle

    dia_arc = wos - dia  # diameter of Cut Arc
    rad_arc = dia_arc / 2  # radius of Cut Arc

    # -----calculate datum-----
    # the center of slot arc is to be used as the datum point for indexing the trichoidal loops.
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

    def text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw):
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

    text_temp = text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)     # generate first block og g code.
    text = text + text_temp
    skip_1 = False  # reset skip_1 flag

    # initialize dir_1 direction.
    if cw == True:
        dir_1 = 'G02'
    elif cw == False:
        dir_1 = 'G03'

    # generate g code for trichoidal loops except last loop
    while abs(angle) < (abs(end_angle)-abs(step_angle)):
        x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
        r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)
        angle = angle_increment(angle, step_angle, cw)
        text_temp = text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)
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

        text_temp = text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)
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
    (---trichoidal arc slot end---)
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
        print(f'''!!script aborted!!\nspiral_drill\nsafe_z below surface\nsafe_z = {"%.3f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.3f" % safe_z})\n'''  # write header for section.
        quit()

    # check if hole dia is larger 2x tool dia.
    if dia_hole > dia*2:
        print(f'''!!script aborted!!\nspiral_drill\nhole dia is larger 2x tool dia.\nhole dia = {"%.3f" % dia_hole}\ntool dia = {"%.3f" % dia}''')
        text = '''\n(!!script aborted!!)\n(hole dia is larger 2x tool dia)\n'''  # write header for section.
        quit()

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
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)}
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
        print(f'''!!script aborted!!\npeck_drill\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''  # write header for section.
        quit()

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
    # Does not return to safe z after surfacing.
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
        print(f'''!!script aborted!!\nspiral_surface\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
#        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''  # write header for section.
        quit()

    # check if start dia is larger than tool dia.
    if end_dia < dia:
        print(f'''!!script aborted!!\nspiral_surface\nhole dia is larger tool dia.\nend dia = {"%.4f" % end_dia}\ntool dia = {"%.4f" % dia}''')
#        text = f'\n(!!script aborted!!)\n(end dia is larger tool dia)\n'  # write header for section.
        quit()

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
    # return to safe z after surfacing.
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
        print(f'''!!script aborted!!\ncorner_slice\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
#        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''  # write header for section.
        quit()

    # check if end dia is larger than tool dia.
    if end_rad*2 < dia:
        print(f'''!!script aborted!!\ncorner_slice\nhole dia is larger tool dia.\nend dia = {"%.4f" % (end_rad*2)}\ntool dia = {"%.4f" % dia}''')
#        text = '''\n(!!script aborted!!)\n(end dia is larger tool dia)\n'''  # write header for section.
        quit()

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3 :
            print(f"!!script aborted!!\ncorner_slice\nmode undefined\nmode = {mode}")
#            text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
            quit()
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
    # return to safe z after surfacing.
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
        print(f'''!!script aborted!!\nspiral_boss\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
#        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''
#        write_g_code(name, text)
        quit()

    # check if end dia is larger than start dia.
    if start_dia < end_dia:
        print(f'''!!script aborted!!\nspiral_boss\nend dia is larger start dia.\nstart dia = {"%.4f" % start_dia}\nend dia = {"%.4f" % end_dia}''')
#        text = '''\n(!!script aborted!!)\n(end dia is larger start dia)\n'''
        quit()

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

def test_cut(dia, name, length_x = 22, length_y = 22, surface_block = True, hole = True):

    # ---Description---
    # Calculates and prints G-code to cut a square block: 10x10mm depth: 3mm after surfacing and adjusted for cutter diameter.
    # assumes origin at center of block.
    # assumes z=0 at top surface.
    # assumes material is delrin.
    # starting point at x = -(diameter of cutter + 1), y = top of block
    # refer to PRT20210503001 CNC Test Part
    # text = test_cut(dia, name, length_x = 22, length_y = 22, surface_block = True, hole = True)

    # ---Variable List---
    # dia = diameter of cutter
    # name = name of G-code file
    # surface_block = boolean. surface block before cutting.
    # hole = boolean. plunge cut hole in center.

    # ---Return Variable List---
    # text = G-code text

    # ---Change History---
    # rev: 01-01-10-02
    # Changed origin from corner of test block to center of test block
    #
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 14/Sep/2021
    # --------------------

    def surface_test_block(dia, length_x, length_y):

        # ---description---
        # calculates and prints to a txt file the tool path in G code to surface a rectangular part.
        # assumes climb milling.
        # assumes origin at bottom left corner of TEST BLOCK.
        # assumes z=0 at top surface.
        # starts at x = length_x + 2 * diameter of cutter, y = 0  from bottom left corner.
        # cuts in a clockwise direction from the outside to the center.
        # return to origin after surfacing.
        # refer to PRT20210510003 Surfacing Calculator

        # ---Variable List---
        origin_x = -length_x/2
        origin_y = -length_y/2
        doc = -1.0
        step = 2
        z_f = 100
        cut_f = 456.3
        safe_z = 3
        debug = False

        text_temp = surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name, debug)
        return (text_temp)

    def test_block(dia, doc):

        # ---Variable List---

        safe_z = 3.000  # safe z
        cut_f = 357.6  # cutting feed rate
        z_f = 132.8  # plunge feed rate
        finish_f = 100.0  # finish feed rate
#        start_x = -14.00  # x start of slot along neutral axis
#        start_y = 5.00  # y start of slot along neutral axis
        step = 1.0  # depth of step per trichoidal slice.
        wos = 6.000  # width of slot
        offset = 0.1  # offset away from cutting surface
        mode = 2  # internal/pocket: 1, external/boss: 2 or slot: 3

        excel_file = 'vector-01.xlsx'
        sheet = 'Sheet8'
        start_x, start_y, end_x, end_y, cutter_x, cutter_y, text_rough = toolpath_data_frame(dia, offset, step, wos, cut_f, name, excel_file, sheet, True)

        text_temp = \
            f'''
        G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
        G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}                 (Rapid to start point)
        G0 Z{"%.4f" % doc}				(Rapid to cutting height)
        F{cut_f}     (set cutting feed)
        '''
        text = text_temp + text_rough

        excel_file = 'vector-01.xlsx'
        sheet = 'Sheet9'
        offset = 0
        start_x, start_y, end_x, end_y, cutter_x, cutter_y, text_finish = toolpath_data_frame(dia, offset, step, wos, finish_f, name, excel_file, sheet, True)

        text_temp = \
            f'''
        G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
        G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}                 (Rapid to start point)
        G0 Z{"%.4f" % doc}				(Rapid to cutting height)
        F{cut_f}     (set cutting feed)
        '''

        text = text + text_temp + text_finish

        return (text)

    def plunge_drill(depth):

        # ---Description---
        # calculates and prints to a txt file the tool path in G code of a peck drilled hole.
        # assumes origin at center of hole.
        # assumes z=0 at top surface.
        # return to safe z after drilling.
        # refer to ALG20210527001 Peck Drilling Algorithm

        # ---Variable List---
        hole_x = 0
        hole_y = 0
        dia_hole = 3
        depth = depth  # depth of hole (absolute convention. Negative in the downward Z direction.)
        peck_depth = abs(depth)  # step per peck. (scalar. Do NOT use negative sign.)
        z_f = 50.2  # z feed
        safe_z = 3  # safe z
        retract_z = 1.5  # retract z after each peck.
        dwell = 0  # dwell time in ms at retract z.

        text = peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug=False)
        return (text)

    info = \
    f'''
    (---Test Cut---)
    (Calculates and prints G-code to cut a square block: 10x10mm depth: 3mm adjusted for cutter diameter.)
    (assumes origin at center of block.)
    (assumes z=0 at top surface.)
    (assumes material is delrin.)
    (assumes cutter is diameter: 3mm)
    (starting point at x = -(diameter of cutter + 1), y = top of block)
    '''
    text = info     # initialize text.

    if surface_block == True:
        text_temp = surface_test_block(dia, length_x, length_y)
        text = text + text_temp
        doc = -4
    else:
        doc = -3

    text_temp = test_block(dia, doc)
    text = text + text_temp

    if hole == True:
        text_temp = plunge_drill(doc)
        text = text + text_temp

    text_temp = \
    f'''
    (---Test Cut End---)
    '''
    text = text + text_temp
    return (text)

def toolpath_data_frame(dia, offset, step, wos, feed, name, excel_file, sheet, debug = False):
    # ---Description---
    # Imports a 2D dataframe from an excel file, calculates the toolpath adjusted for offset and tool diameter and prints to a txt file the single or trichoidal tool path in G code.
    # returns last position of cutter and end position of arc.
    # refer to "ALG20220329001 Toolpath Data Frame Algorithm"
    # start and end points are located at slot arc center points.
    # assumes that cutter is at cutting depth.
    # does not return to safe z.
    # does not set cutting feed.
    # first_x_adjusted, first_y_adjusted, end_x, end_y, cutter_x, cutter_y, text = toolpath_data_frame(dia, offset, step, wos, feed, name, excel_file, debug)

    # ---Variable List---
    # dia = diameter of cutter
    # offset = offset from cutting edge.
    # step = trichoidal step
    # wos = width of trichodial slot
    # feed = cutting feed
    # name = name of file
    # excel file = excel file name including file extension.

    # ---Return Variable List---
    # end_x_final = x coordinate of end of slot unadjusted
    # end_y_final = y coordinate of end of slot unadjusted
    # cutter_x_final = x coordinate of cutter position
    # cutter_y_final = y coordinate of cutter position

    # ---Change History---
    # rev: 01-01-10-07
    # initial release
    # software test run on 31/Mar/2022

    start_block = \
    f'''
    (---toolpath_data_frame start---)
    (---description---)
    (Imports a 2D dataframe from an excel file, calculates the toolpath adjusted for offset and tool diameter and prints to a txt file the single or trichoidal tool path in G code.)
    (returns last position of cutter and end position of arc.)
    (refer to "ALG20220329001 Toolpath Data Frame Algorithm")
    (start and end points are located at slot arc center points.)
    (assumes that cutter is at cutting depth.)
    (does not return to safe z.)
    (does not set cutting feed.)
    (---parameter---)            
    (cutter diameter: {"%.3f" % dia})        
    (offset: {"%.3f" % offset})
    (excel_file: {excel_file})
    (sheet: {sheet})
    '''
    text = start_block

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

    def format_data_frame_variable(df, var_name, counter, debug = False):
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

        var_raw = df[var_name][counter]  # import variable from dataframe
        var_raw = str(var_raw)  # convert imported variable to string.

        if debug == True:       # debug code
            print(f'row = {counter}')
            print(f'var_name = {var_name}')
            print(f'var_raw = {var_raw}')
            print(f'var_raw type = {type(var_raw)}')

        if var_raw == 'None':
            var_format = None  # None detected.
        elif var_raw == 'False':
            var_format = False  # explicit boolean declaration.
        elif var_raw == 'True':
            var_format = True  # explicit boolean declaration.
        elif is_valid_float(var_raw) == True:       # check for numerical value
            var_format = float(var_raw)
        else:
            var_format = var_raw    # import as string.

        if debug == True:       # debug code
            print(f'var_format = {var_format}')
            print(f'var_format type = {type(var_format)}\n')

        return (var_format)     # return formatted value.

    def extract_row(counter, debug = False):
        # ---Description---
        # Extract and format variables of a single row from the data frame to the explicit variable type.
        # returns formatted row of variables.
        # x, y, z, rad, arc_seg, cw, less_180, tri, ramp_z, mode, type = extract_row(counter)

        # ---Variable List---
        # counter = row counter

        # ---Return Variable List---
        # x = x value.
        # y = y value.
        # z = z value.
        # rad = radius.
        # arc_seg = arc_segment flag.
        # cw = clockwise flag.
        # less_180 = less_180 flag.
        # tri = trichodial flag.
        # ramp_z = ramp_z.
        # mode = offset mode. 1 = right side of travel, 2 = left side of travel, 3 = on line of travel.

        x = format_data_frame_variable(df, 'x', counter, debug)                     # import x value.
        y = format_data_frame_variable(df, 'y', counter, debug)                     # import y value.
        z = format_data_frame_variable(df, 'z', counter, debug)                     # import z value.
        rad = format_data_frame_variable(df, 'rad', counter, debug)                 # import radius.
        arc_seg = format_data_frame_variable(df, 'arc_seg', counter, debug)         # import arc_segment flag.
        cw = format_data_frame_variable(df, 'cw', counter, debug)                   # import clockwise flag.
        less_180 = format_data_frame_variable(df, 'less_180', counter, debug)       # import less_180 flag.
        tri = format_data_frame_variable(df, 'tri', counter, debug)                 # import trichodial flag.
        ramp_z = format_data_frame_variable(df, 'ramp_z', counter, debug)           # import ramp_z.
        mode = format_data_frame_variable(df, 'mode', counter, debug)               # import mode of contour.
        operation = format_data_frame_variable(df, 'operation', counter, debug)     # import operation.

#        typea = 'N/A'
        return (x, y, z, rad, arc_seg, cw, less_180, tri, ramp_z, mode, operation)         # return values

    df = pd.read_excel(excel_file, sheet_name = sheet)      # import excel file into dataframe.

    if debug == True:       # debug
        print(f'{df}\n')

    rows = df.shape[0]      # total number of rows in dataframe.
    last_row = rows - 1     # initialize number of last row
    counter = 0             # initialize counter

    # initialize parameters
    start_x, start_y, start_z, discard, discard, discard, discard, discard, discard, mode, operation = extract_row(counter)   # extract row 0 values.
    counter = counter + 1                                                                                                   # increment counter
    end_x, end_y, start_z, rad, arc_seg, cw, less_180, tri, ramp_z, mode, operation = extract_row(counter)                    # extract row 1 values.

    first_slot = True           # initialize trichodial first slot
    last_slot = False           # initialize trichodial last slot
    end_x_adjusted_pre = None   # Initialize
    end_y_adjusted_pre = None   # Initialize
    rad_adjusted = None         # Initialize

    if tri == True:             # initialize effective width of slot. Trichodial = wos, single line = tool diameter.
        effective_wos = wos
    else:
        effective_wos = dia

    while counter <= last_row:      # recursive loop

        if counter == last_row:
            last_slot = True        # set last_slot = True for trichodial toolpath.

        if arc_seg == False:        # straight line segment
            start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted = linear_offset_adjustment(effective_wos, offset, start_x, start_y,end_x, end_y, mode)     # adjust line for offset and tool diameter.
        elif arc_seg == True:
            start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted = arc_offset_adjustment(effective_wos, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode)     # adjust arc for offset and tool diameter.

        if counter == 1:
            cutter_x = start_x_adjusted
            cutter_y = start_y_adjusted
            first_x_adjusted = start_x_adjusted   # first point of the segment.
            first_y_adjusted = start_y_adjusted   # first point of the segment.

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
            print(f'tri = {tri}')
            print(f'ramp_z = {ramp_z}')
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

            # intialize parameters
            ramp_z = None
            last_slot = False
            end_x_adjusted = start_x_adjusted
            end_y_adjusted = start_y_adjusted
            start_x_adjusted = end_x_adjusted_pre
            start_y_adjusted = end_y_adjusted_pre
            rad_adjusted = effective_wos/2 + offset
            rad_adjusted = round(rad_adjusted, 5)  # round to 5 decimal places.
            less_180 = True
            arc_seg = True
            end_x = start_x     # reset start x value
            end_y = start_y     # reset start y value

            if mode == 1:       # Assumes transition arc on the external/boss profile cuts. !!! Caution !!!: Does not check for overlapping internal/pocket correction.
                cw = False
            elif mode == 2:
                cw = True

        if tri == False:
            if arc_seg == False:
                cutter_x, cutter_y, cutter_z, text_temp = line(end_x_adjusted, end_y_adjusted, name, feed, ramp_z, start_z)  # print G-code for adjusted line segment.
            else:
                cutter_x, cutter_y, cutter_z, text_temp = arc(end_x_adjusted, end_y_adjusted, name, rad_adjusted, cw, less_180, feed, ramp_z, start_z)  # print G-code for adjusted arc segment.
        elif tri == True:
            if arc_seg == False:
                discard, discard, cutter_x, cutter_y, text_temp = tri_slot(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, step, wos, dia, name, cutter_x, cutter_y, first_slot, last_slot)   # print G-code for adjusted trichodial line segment.
            else:
                discard, discard, cutter_x, cutter_y, text_temp = tri_arc(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, step, wos, dia, rad_adjusted, cw, less_180, name, cutter_x, cutter_y, first_slot, last_slot)     # print G-code for adjusted trichodial arc segment.
            first_slot = False      # clear first slot flag
        else:
            print(f'''!!script aborted!!\ntoolpath_data_frame\ninvalid trichoidal selection\nrow = {counter}\ncolumn = tri\ntri = {tri}''')
#            text = f'''\n(!!script aborted!!)\n(invalid trichoidal selection)\n(row = {counter})\n(column = tri)\n'''  # write header for section.
            quit()

        text = text + text_temp      # storage G-code into a text variable before printing to a text file.

        if counter == last_row:
            return (first_x_adjusted, first_y_adjusted, end_x, end_y, cutter_x, cutter_y, text)       # last point. exit function.

        counter = counter + 1                   # increment counter
        end_x_adjusted_pre = end_x_adjusted     # update previous x value
        end_y_adjusted_pre = end_y_adjusted     # update previous y value
        start_x = end_x                         # update start x value
        start_y = end_y                         # update start y value

        end_x, end_y, start_z, rad, arc_seg, cw, less_180, tri, ramp_z, mode, operation = extract_row(counter)

# ---------File Name Variables------------

doc_number = datetime.now().strftime("%Y%m%d-%H%M%S")  # get date time stamp (YYYYMMDD-HHMMSS) for file name.
prefix = 'GCE'
file_name = 'ZT Bracket-02 Post Outline'
rev = '01'
name = prefix + doc_number + f' Rev{rev} ' + file_name   # file name

# ---------General Variables------------

clear_z = 3.000  # safe z
initial_x = 0  # initial x
initial_y = 0  # initial y
start_z = 0.000  # start z
terminal_x = 0  # terminal x
terminal_y = 0  # terminal y
cut_f = 353.8  # cutting feed rate
z_f = 65.9  # plunge feed rate
finish_f = 110.9 # finish feed rate
rpm = 2900  # spindle speed
cutter_dia = 3.0  # diameter of cutter before adjustment
tol = -0.07    # adjustment for cutter tolerance
dia = cutter_dia + tol  # adjust cutter tolerance
loc = 12    # length of cutter
flute = 4   # number of flutes
surface_speed = 15  #Surface Speed (m/min)
chipload = 0.007 # Chipload (mm/tooth)
cutter_material = "HSS"    # material of cutter. e.g. HSS, carbide, cobalt
coating = "None"    # coating of cutter.  e.g. None, AT, TiN
x_origin = "center of right most post"      # x origin e.g. center of part, left edge
y_origin = "center of right most post"    # y origin. e.g. center of part, bottom edge
z_origin = "top surface of part"    # z origin e.g. top surface of part, top surface of vise
part_material = "ABS"   # material of part. e.g. Delrin, ABS, SS304, CoCr
compiler = "(UCCNC v1.2111)\n(DEMO_UC400ETH)"

info = \
f'''
(==========================)    
(file_name: {name})
(==========================)  

(---Description---)
(This program calculates the tool path to ...)
(Assumes climb milling.)

(TOOL/MILL, dia: {"%.3f" % cutter_dia}, LOC:{"%.3f" % loc}, {flute} Flute, {cutter_material}, {coating})
(--X origin: {x_origin}--)
(--Y origin: {y_origin}--)
(--Z origin: {z_origin}--)
(Part material: {part_material})
(G-code is generated using Python script "{os.path.basename(__file__)}")

(---Compiler---)
{compiler}

(---Change History---)
(NA)    

(---Bug List---)
(NA)
'''

var = \
f'''
(===General variables===)
(clear z             = {"%.3f" % clear_z})
(initial x           = {"%.3f" % initial_x})
(initial y           = {"%.3f" % initial_y})
(start z             = {"%.3f" % start_z})
(terminal x          = {"%.3f" % terminal_x})
(terminal y          = {"%.3f" % terminal_y})
(cut feed            = {"%.1f" % cut_f})
(plunge feed         = {"%.1f" % z_f})
(finish feed         = {"%.1f" % finish_f})
(spindle speed       = {"%.0f" % rpm})
(diameter of cutter  = {"%.3f" % cutter_dia})
(tolerance of cutter = {"%.3f" % tol})
(effective diameter  = {"%.3f" % dia})
(Surface Speed       = {"%.0f" % surface_speed} m/min)
(Chipload            = {"%.3f" % chipload} mm/tooth)
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
text = info + var + start_block     # initialize text variable.
write_to_file(name, text)

# ===========================================================================
# ================================ G-code start =============================
# ===========================================================================

#text = test_cut(dia, name, length_x = 22, length_y = 22, surface_block = True, hole = True)
#write_to_file(name, text)

# Material clearance
offset = 0
step = 0.5
wos = 6
feed = cut_f
excel_file = 'vector-01.xlsx'
sheet = 'Sheet11'
debug = True

start_x, start_y, end_x, end_y, cutter_x, cutter_y, text_tri = toolpath_data_frame(dia, offset, step, wos, feed, name, excel_file, sheet, debug)

doc= -6

text_temp = \
    f'''
G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}                 (Rapid to start point)
G0 Z{"%.4f" % doc}				(Rapid to cutting height)
F{cut_f}     (set cutting feed)
'''

text = text_temp + text_tri
write_to_file(name, text)

# rough cut

offset = 0.1
step = 0.5
wos = 5.3
feed = cut_f
excel_file = 'vector-01.xlsx'
sheet = 'Sheet10'
debug = True

start_x_tri, start_y_tri, end_x, end_y, cutter_x, cutter_y, text_tri = toolpath_data_frame(dia, offset, step, wos, feed, name, excel_file, sheet, debug)

offset = 0.1
feed = finish_f
excel_file = 'vector-01.xlsx'
sheet = 'Sheet12'
start_x_fin, start_y_fin, end_x, end_y, cutter_x, cutter_y, text_fin = toolpath_data_frame(dia, offset, step, wos, feed, name, excel_file, sheet, debug)

doc= -6

# first post

text_temp = \
    f'''
G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
G0 X{"%.4f" % start_x_tri} Y{"%.4f" % start_y_tri}                 (Rapid to start point)
G0 Z{"%.4f" % doc}				(Rapid to cutting height)
F{cut_f}     (set cutting feed)
'''
text = text_temp + text_tri
write_to_file(name, text)

text_temp = \
    f'''
G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
G0 X{"%.4f" % start_x_fin} Y{"%.4f" % start_y_fin}                 (Rapid to start point)
G0 Z{"%.4f" % doc}				(Rapid to cutting height)
F{cut_f}     (set cutting feed)
'''
text = text_temp + text_fin
write_to_file(name, text)

# 2nd & 3rd post
i = 1   # initialize
while i <= 2:

    text_temp = \
        f'''
    G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
    G0 X0 Y0                 (Rapid to zero point)
    G92 X7.9638 Y0       (Offset datum)
    G0 X{"%.4f" % start_x_tri} Y{"%.4f" % start_y_tri}                 (Rapid to start point)
    G0 Z{"%.4f" % doc}				(Rapid to cutting height)
    F{cut_f}     (set cutting feed)
    '''

    text = text_temp + text_tri
    write_to_file(name, text)

    text_temp = \
        f'''
    G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
    G0 X{"%.4f" % start_x_fin} Y{"%.4f" % start_y_fin}                 (Rapid to start point)
    G0 Z{"%.4f" % doc}				(Rapid to cutting height)
    F{cut_f}     (set cutting feed)
    '''
    text = text_temp + text_fin
    write_to_file(name, text)

    i = i+1     # increment counter

text_temp = \
    f'''
G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
G0 X0 Y0                 (Rapid to zero point)
G92 X-15.9276 Y0       (Offset datum)
'''
text = text_temp
write_to_file(name, text)

# ===========================================================================
# ================================ G-code end ===============================
# ===========================================================================

end_block = \
f'''
(===Main End===)

(end block)
G0 Z{"%.4f" % clear_z}				(Rapid to safe height)
G0 X{"%.4f" % terminal_x} Y{"%.4f" % terminal_y}        (Rapid to end point)
M5						    (Spindle Stop)
M30					        (End & Rewind)
'''
text = end_block
write_to_file(name, text)