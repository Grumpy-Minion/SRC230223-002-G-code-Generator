# =============================== Title Block ===============================
#
# file name: SRC20210420001 G-code Generator
#
# ---Description---
#   Generate G-code for basic toolpaths.
#
# ---Change History---
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
import sys
from datetime import datetime

def absolute_angle(start_x, start_y, end_x, end_y, debug = False):
    # calculate absolute angle of a vector with reference to the x axis.
    # input parameters: start_x, start_y, end_x, end_y, debug (optional)
    # returns the absolute angle.

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
    # input parameters: datum_x, datum_y, datum_angle, x, y, debug(optional))
    # absolute_x, absolute_y
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
    # absolute_x, absolute_y
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

def write_g_code(name, text):
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
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 13/Sep/2021
    # --------------------

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\nlinear_offset_adjustment\nlinear_offset_adjustment mode undefined\nlinear_offset_adjustment mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        write_g_code(name, text)
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
    end_x_adjusted, end_y_adjusted = relative_coordinate(start_x_temp, start_y_temp, angle_temp, x2_temp, y_temp, debug=False)

    return(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted)

def arc_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode = None):

    # ---Description---
    # Calculates an arc adjusted for cutter diameter/slot width and additional offset.
    # returns adjusted position of start and end position.
    # Refer to PRT20210912001 Rev01 Arc Offset Adjustment
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
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 13/Sep/2021
    # --------------------

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\narc_offset_adjustment mode undefined\narc_offset_adjustment mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    if mode == 3:   # on line cut. no adjustment
        start_x_adjusted = start_x
        start_y_adjusted = start_y
        end_x_adjusted = end_x
        end_y_adjusted = end_y
        rad_adjusted = rad
        return (start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted)

    # check if cutter radius + offset is larger than arc radius for internal/pocket cut.
    if mode == 1 and dia/2+offset > rad:
        print(f"!!script aborted!!\narc_offset_adjustment\ncutter radius + offset is larger than arc radius for internal/pocket cut\nrad = {rad}\ndia = {dia}\noffset = {offset}")
        text = '''\n(!!script aborted!!)\n(cutter offset larger than arc)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if cutter radius + offset is equal to arc radius for internal/pocket cut.
    # this results in a G-code arc command error(G02, G03). end point of arc cannot be same as start point.
    if mode == 1 and dia/2+offset == rad:
        print(f"!!script aborted!!\narc_offset_adjustment\ncutter radius + offset is equal to arc radius for internal/pocket cut\nrad = {rad}\ndia = {dia}\noffset = {offset}")
        text = '''\n(!!script aborted!!)\n(cutter offset same as arc)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if arc radius is <= to 0
    if rad <= 0:
        print(f"!!script aborted!!\narc_offset_adjustment\narc radius <= 0\nrad = {rad}")
        text = '''\n(!!script aborted!!)\n(arc radius <= 0)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    vec_x = end_x - start_x     # x vector length of slot
    vec_y = end_y - start_y     # y vector length of slot
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)     # length of slot
    x_temp = length/2       # calculate relative polar x coordinate from start point. used to determine center of arc
    y_temp = math.sqrt(rad ** 2 - x_temp ** 2)       # calculate relative polar y coordinate from start point. used to determine center of arc
    angle_temp = absolute_angle(start_x, start_y, end_x, end_y, debug=False)       # calculate absolute vector angle of start point to end point. used to determine center of arc
    angle_arc = 2 * math.degrees(math.asin((length/2)/rad))      # angle of arc width

    # center is on right side of arc for minor clockwise arcs.
    if less_180 == True:
        y_temp = -y_temp
        angle_arc = -angle_arc    # angle of arc calculated in negative direction/clockwise
    else:
        y_temp = y_temp
        angle_arc = angle_arc    # angle of arc calculated in positive direction/counter-clockwise

    # center is on opposite arc for counter-clockwise arc.
    # direction of angle of arc is reversed for counter-clockwise arc.
    if cw == True:
        y_temp = y_temp
        angle_arc = angle_arc
    else:
        y_temp = -y_temp
        angle_arc = -angle_arc

    x_center, y_center = relative_coordinate(start_x, start_y, angle_temp, x_temp, y_temp, debug = False) # calculate center of arc
    start_angle = absolute_angle(x_center, y_center, start_x, start_y, debug = False)   # calculate absolute angle of datum vector. i.e. vector of arc center to start point

    if mode == 1:
        rad_adjusted = rad - (dia/2 + offset)   # calculate adjusted radius for internal/pocket cut
    elif mode == 2:
        rad_adjusted = rad + (dia/2 + offset)    # calculate adjusted radius for external/boss cut

    start_x_adjusted, start_y_adjusted = relative_polar(x_center, y_center, (start_angle), rad_adjusted, 0, debug=False)        # calculate adjusted start point
    end_x_adjusted, end_y_adjusted = relative_polar(x_center, y_center, (start_angle), rad_adjusted, angle_arc, debug=False)    # calculate adjusted end point

    if less_180 == True:
        rad_adjusted = rad_adjusted     # acute arc
    else:
        rad_adjusted = -rad_adjusted    # obtuse arc

    return(start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted)

def line(dia, offset, start_x, start_y, end_x, end_y, name, feed = None, ramp_z = None, mode = None):

    # ---Description---
    # Calculates and prints G-code of a straight line adjusted for cutter diameter and additional offset.
    # Optional z direction ramp.
    # Optional feed rate.
    # returns unadjusted end position and cutter position
    # end_x, end_y, cutter_x, cutter_y = line(dia, offset, start_x, start_y, end_x, end_y, name, feed, ramp_z, mode)

    # ---Variable List---
    # dia = diameter of cutter/slot
    # offset = additional offset
    # start_x = x start of line
    # start_y = y start of line
    # end_x = x end of line
    # end_y = y end of line
    # name = name of file
    # feed = cutting feed. (Optional)
    # ramp_z = Z end of line. (Optional)
    # mode = offset mode. 1 = right side of travel, 2 = left side of travel, 3 = on line of travel.

    # ---Return Variable List---
    # end_x = original end x position
    # end_y = original end y position
    # cutter_x = adjusted start x position/ cutter x position
    # cutter_y = adjusted start y position/ cutter y position

    # ---Change History---
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 14/Sep/2021
    # --------------------

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\nline mode undefined\nline mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    if mode == 1 or mode == 2:
        start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted = linear_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, mode)    # adjust offsets.

    elif mode == 3:     # no offset
        start_x_adjusted = start_x
        start_y_adjusted = start_y
        end_x_adjusted = end_x
        end_y_adjusted = end_y

    text = f'''G1 X{"%.4f" % end_x_adjusted} Y{"%.4f" % end_y_adjusted}'''

    if ramp_z != None:
        text_temp = f''' Z{"%.4f" % ramp_z}'''  # optional z ramp
        text = text + text_temp

    if feed != None:
        text_temp = f''' F{"%.0f" % feed}'''    # optional feed
        text = text + text_temp

    text = text + "\n"      # new line
    write_g_code(name, text)    # write g-code

    cutter_x = end_x_adjusted
    cutter_y = end_y_adjusted

    return(end_x, end_y, cutter_x, cutter_y)        # returns unadjusted end position and cutter position

def arc(dia, offset, start_x, start_y, end_x, end_y, name, rad, cw, less_180, feed = None, ramp_z = None, mode = None):

    # ---Description---
    # Calculates and prints G-code of an arc adjusted for cutter diameter and additional offset.
    # Optional z direction ramp.
    # Optional feed rate.
    # returns unadjusted end position and cutter position
    # end_x, end_y, cutter_x, cutter_y = arc(dia, offset, start_x, start_y, end_x, end_y, name, rad, cw, less_180, feed, ramp_z, mode)

    # ---Variable List---
    # dia = diameter of cutter/slot
    # offset = additional offset
    # start_x = x start of line
    # start_y = y start of line
    # end_x = x end of line
    # end_y = y end of line
    # name = name of file
    # rad = radius of arc
    # cw = Boolean. True = clockwise False = counter clockwise.
    # less_180 = Boolean. True: < 180deg False: > 180deg.
    # feed = cutting feed. (Optional)
    # ramp_z = Z end of line. (Optional)
    # mode = offset mode. 1 = right side of travel, 2 = left side of travel, 3 = on line of travel.

    # ---Return Variable List---
    # end_x = original end x position
    # end_y = original end y position
    # cutter_x = adjusted start x position/ cutter x position
    # cutter_y = adjusted start y position/ cutter y position

    # ---Change History---
    # rev: 01-01-10-01
    # Initial release.
    # software test run on 14/Sep/2021
    # --------------------

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\narc\narc mode undefined\narc mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    if mode == 1 or mode == 2:
        start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted, rad_adjusted = arc_offset_adjustment(dia, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode)    # adjust offsets.

    elif mode == 3:     # no offset
        start_x_adjusted = start_x
        start_y_adjusted = start_y
        end_x_adjusted = end_x
        end_y_adjusted = end_y
        rad_adjusted = rad

        if less_180 == True:
            rad_adjusted = rad_adjusted     # positive sign for acute arc
        if less_180 == False:
            rad_adjusted = -rad_adjusted    # negative sign for obtuse arc

    if cw == True:
        dir = '02'
    elif cw == False:
        dir = '03'

    text = f'''G{dir} X{"%.4f" % end_x_adjusted} Y{"%.4f" % end_y_adjusted} R{"%.4f" % rad_adjusted}'''

    if ramp_z != None:
        text_temp = f''' Z{"%.4f" % ramp_z}'''  # optional z ramp
        text = text + text_temp

    if feed != None:
        text_temp = f''' F{"%.0f" % feed}'''    # optional feed
        text = text + text_temp

    text = text + "\n"      # new line
    write_g_code(name, text)    # write g-code

    cutter_x = end_x_adjusted
    cutter_y = end_y_adjusted

    return(end_x, end_y, cutter_x, cutter_y)        # returns unadjusted end position and cutter position

def tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, offset, name, cutter_x, cutter_y, first_slot = True, last_slot = True, mode = None, debug = False):
    
   # ---Description---
   # Calculates and prints to a txt file the trichoidal tool path in G code of a straight slot.
   # returns last position of cutter and end position of slot.
   # start and end points are located along slot arc center/neutral axis.
   # assumes that cutter is at cutting depth.
   # does NOT return to safe z.
   # end_x_original, end_y_original, cutter_x_final, cutter_y_final = tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, offset, name, cutter_x, cutter_y, first_slot, last_slot, mode, debug)

   # ---Variable List---
   # start_x = x start of slot along neutral axis
   # start_y = y start of slot along neutral axis
   # end_x = x end of slot along neutral axis
   # end_y = y end of slot along neutral axis
   # step = depth of step per trichoidal slice.
   # wos = width of slot
   # dia = diameter of cutter
   # offset = offset away from cutting surface
   # name = name of file
   # cutter_x = x position of cutter
   # cutter_y = y position of cutter
   # first_slot = boolean. Is this the first slot?
   # last_slot = boolean. Is this the last slot?
   # mode = offset mode. 1 = right side of travel 2 = left side of travel 3 = on line of travel
   # debug = False (default)

   # ---Return Variable List---
   # end_x_original = x coordinate of end of slot unadjusted
   # end_y_original = y coordinate of end of slot unadjusted
   # cutter_x_final = x coordinate of cutter position
   # cutter_y_final = y coordinate of cutter position
   
   # ---Change History---
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
    (offset: {"%.3f" % offset})
    (position of cutter: X{"%.4f" % cutter_x} Y{"%.4f" % cutter_y})
    (first slot: {first_slot})
    (last slot: {last_slot})
    (mode: {mode})                                                                                                       
    '''
    write_g_code(name, title_block)

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\ntri_slot\ntri_slot mode undefined\ntri_slot mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    start_x_original = start_x
    start_y_original = start_y
    end_x_original = end_x
    end_y_original = end_y

    if mode == 1 or mode == 2:
        start_x, start_y, end_x, end_y = linear_offset_adjustment(wos, offset, start_x, start_y, end_x, end_y, mode)        # adjust for internal or external cut

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
                write_g_code(name, line_1)
            else:                                           # reorient cutter to starting point of slot.
                delta_x = abs(x1 - cutter_x)
                delta_y = abs(y1 - cutter_y)
                if (delta_x > 0.0001) or (delta_y > 0.0001):       # if cutter is at start point skip else reorient.
                    line_1 = \
    f'''
    G03 X{"%.4f" % x1} Y{"%.4f" % y1} I{"%.4f" % (start_x-cutter_x)} J{"%.4f" % (start_y-cutter_y)}
    '''
                    write_g_code(name, line_1)       # write first line

        # write G code of rest of trichoidal loop
        line_2 = \
    f'''
    G1 X{"%.4f" % x2} Y{"%.4f" % y2}
    G03 X{"%.4f" % x3} Y{"%.4f" % y3} R{"%.4f" % rad_arc}
    G1 X{"%.4f" % x4} Y{"%.4f" % y4}
    '''
        write_g_code(name, line_2)

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
            else:
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
        write_g_code(name, line_3)

        i = i + 1

    text = \
    f'''(---trichoidal linear slot end---)
    '''
    write_g_code(name, text)

    return (end_x_original, end_y_original, cutter_x_final, cutter_y_final)

def tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, offset, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot=True, last_slot=True, mode = None, debug = False):

   # ---Description---
   # Calculates and prints to a txt file the trichoidal tool path in G code of a circular arc.
   # returns last position of cutter and end position of arc.
   # refer to "PRT20210421001 Trichoidal Arc Calculator", "MEM20210522001 Trichoidal Arc", "MEM20210429002 Trichoidal Notes", "ALG20210520001 Trichoidal Arc Algorithm"
   # start and end points are located at slot arc center points.
   # assumes that cutter is at cutting depth.
   # does not return to safe z.
   # does not set cutting feed.
   # end_x_original, end_y_original, cutter_x_final, cutter_y_final = tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, offset, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot, last_slot, mode, debug)

   # ---Variable List---
   # start_x = x start of arc along neutral axis
   # start_y = y start of arc along neutral axis
   # end_x = x end of arc along neutral axis
   # end_y = y end of arc along neutral axis
   # step = depth of step per trichoidal slice.
   # wos = width of slot
   # dia = diameter of cutter
   # offset = offset away from cutting surface
   # rad_slot = radius of slot arc.
   # cw = Boolean. True = clockwise False = counter clockwise.
   # less_180 = Boolean. True: < 180deg False: > 180deg.
   # name = name of file
   # cutter_x = x position of cutter
   # cutter_y = y position of cutter
   # first_slot = boolean. Is this the first slot?
   # last_slot = boolean. Is this the last slot?
   # mode = offset mode. 1 = right side of travel 2 = left side of travel 3 = on line of travel
   # debug = False (default)

   # ---Return Variable List---
   # end_x_original = x coordinate of end of slot unadjusted
   # end_y_original = y coordinate of end of slot unadjusted
   # cutter_x_final = x coordinate of cutter position
   # cutter_y_final = y coordinate of cutter position

    # ---Change History---
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
    (offset: {"%.3f" % offset})             
    (position of cutter: X{"%.4f" % cutter_x} Y{"%.4f" % cutter_y}) 
    (first slot: {first_slot})              
    (last slot: {last_slot})                
    (clockwise : {cw})
    (acute angle: {less_180})
    (mode: {mode}) 
    '''
    write_g_code(name, start_block)

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3:
        print(f"!!script aborted!!\ntri_arc\ntri_arc mode undefined\ntri_arc mode = {mode}")
        text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if adjusted minor arc is negative for neutral cut.
    if mode == 3 and wos / 2 > rad_slot:
        print(f"!!script aborted!!\ntri_arc\nadjusted minor arc is negative for neutral cut\nrad_slot = {rad_slot}\nwidth of slot = {wos}")
        text = '''\n(!!script aborted!!)\n(adjusted minor arc is negative for neutral cut)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    start_x_original = start_x
    start_y_original = start_y
    end_x_original = end_x
    end_y_original = end_y

    if mode == 1 or mode == 2:
        rad = rad_slot
        start_x, start_y, end_x, end_y, rad_slot = arc_offset_adjustment(wos, offset, start_x, start_y, end_x, end_y, rad, cw, less_180, mode)   # calculate adjusted arc.
        rad_slot = abs(rad_slot)     # remove negative sign if present.

    # check if width of slot is smaller tool dia
    if wos <= dia:
        print(f'''!!script aborted!!\ntri_arc\nwidth of slot is smaller tool dia.\nwidth of slot= {"%.3f" % wos}\ntool dia = {"%.3f" % dia}''')
        text = '''\n(!!script aborted!!)\n(width of slot is smaller tool dia)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    skip_1 = False   # initialize skip_1 flag

    vec_x = end_x - start_x
    vec_y = end_y - start_y
    linear_length = math.sqrt(vec_x ** 2 + vec_y ** 2)      # calculate linear length from start point to end point

    # check if diameter of arc is larger than linear length
    if rad_slot*2 < linear_length:
        print(f'''!!script aborted!!\ntri_arc\ndiameter of arc is smaller than linear length.\ndiameter of arc = {"%.3f" % (rad_slot*2)}\nlinear length = {"%.3f" % linear_length}''')
        text = '''\n(!!script aborted!!)\n(diameter of arc is smaller than linear length)\n'''  # write header for section.
        write_g_code(name, text)
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
        else:
            vec_angle = vec_angle + 90     # acute angle, ccw
    else:
        if cw == True:
            vec_angle = vec_angle + 90     # obtuse angle, cw
        else:
            vec_angle = vec_angle + 270     # obtuse angle, ccw

    datum_x, datum_y = relative_polar(cen_x, cen_y, 0, cen_length, vec_angle)  # calculate position of datum.
    step_angle = step / (rad_slot*math.pi/180)
    inc_angle = step_angle  # initialize increment angle
    datum_angle = absolute_angle(datum_x, datum_y, start_x, start_y)  # calculate absolute angle of start point with respect to datum (center of slot arc).
    end_angle = slot_angle  # end angle
    if cw == True:
        end_angle = - abs(end_angle)    # angle decrements in cw arc
    else:
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
        else:
            x1, y1 = relative_polar(datum_x, datum_y, datum_angle, major_rad, angle)
            x2, y2 = relative_polar(datum_x, datum_y, datum_angle, major_rad, angle + inc_angle)
            x3, y3 = relative_polar(datum_x, datum_y, datum_angle, minor_rad, angle + inc_angle)
            x4, y4 = relative_polar(datum_x, datum_y, datum_angle, minor_rad, angle)
        x5 = x1
        y5 = y1
        return x1, y1, x2, y2, x3, y3, x4, y4, x5, y5

    def segment_radius(rad_slot, rad_arc, cw):
        # calculate radii. refer to sketch.
        major_rad = rad_slot + rad_arc
        minor_rad = rad_slot - rad_arc
        if cw == True:
            r1 = minor_rad
            r2 = minor_rad
            r4 = major_rad
        else:
            r1 = major_rad
            r2 = major_rad
            r4 = minor_rad
        r3 = rad_arc
        r5 = rad_arc
        return r1, r2, r3, r4, r5

    def angle_increment(angle, step_angle, cw):
        # increment angle. cw: negative direction. ccw: positive direction
        if cw == True:
            angle = angle - step_angle
        else:
            angle = angle + step_angle
        return angle

    def text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw):
        # generate g code. refer to sketch.
        if cw == True:
            dir = 'G02'
            inv_dir = 'G03'
        else:
            dir = 'G03'
            inv_dir = 'G02'

        if skip_1 == False:     # if cutter is at x1y1, skip
            text_01 = \
            f'''
            {dir_1} X{"%.4f" % x1} Y{"%.4f" % y1} R{"%.4f" % r1}
            '''
            write_g_code(name, text_01)

        text_02 = \
            f'''
            {dir} X{"%.4f" % x2} Y{"%.4f" % y2} R{"%.4f" % r2}
            G03 X{"%.4f" % x3} Y{"%.4f" % y3} R{"%.4f" % r3}
            {inv_dir} X{"%.4f" % x4} Y{"%.4f" % y4} R{"%.4f" % r4}
            G03 X{"%.4f" % x5} Y{"%.4f" % y5} R{"%.4f" % r5}
            '''
        write_g_code(name, text_02)

    x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
    r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)
    angle = angle_increment(angle, step_angle, cw)

    # for 1st loop only. move tool from arc start position to 1st position.
    if first_slot == True:      # first slot. assumes cutter at start x y.
        r1 = rad_arc / 2
        dir_1 = 'G03'
    else:   # reorient cutter to starting point of slot if this is not first slot. assumes cutter is along circumference of slot.
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
            else:
                dir_1 = 'G03'

    text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)     # generate first block og g code.
    skip_1 = False  # reset skip_1 flag

    # initialize dir_1 direction.
    if cw == True:
        dir_1 = 'G02'
    else:
        dir_1 = 'G03'

    # generate g code for trichoidal loops except last loop
    while abs(angle) < (abs(end_angle)-abs(step_angle)):
        x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
        r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)
        angle = angle_increment(angle, step_angle, cw)
        text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)

    # generate g code for last loop if present.
    if abs(angle) >= (abs(end_angle)-abs(step_angle)) and abs(angle) < abs(end_angle):
        inc_angle = abs(end_angle) - abs(angle)
        x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = segment_position(datum_x, datum_y, datum_angle, rad_slot, rad_arc, angle, inc_angle, cw)
        r1, r2, r3, r4, r5 = segment_radius(rad_slot, rad_arc, cw)

        # calculate last slot end position
        if last_slot == True:   # calculate x5, y5, r5 to end at midline with the slot path.
            r5 = rad_arc/2
            x5, y5 = relative_polar(datum_x, datum_y, datum_angle, rad_slot, angle)

        text_tri_arc(x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, r1, r2, r3, r4, r5, dir_1, skip_1, cw)

        if last_slot == True:   # advance tool to end position on slot path midline.
            text = \
                f'''
                {dir_1} X{"%.4f" % end_x} Y{"%.4f" % end_y} R{"%.4f" % rad_slot}
                '''
            write_g_code(name, text)
            cutter_x_final = end_x
            cutter_y_final = end_y
        else:       # advance tool to cutting position for next slot.
            rad_temp = rad_slot-rad_arc
            text = f'''{dir_1} X{"%.4f" % x2} Y{"%.4f" % y2} R{"%.4f" % rad_temp}'''
            write_g_code(name, text)
            cutter_x_final = x2
            cutter_y_final = y2

    text = \
    f'''
    (---trichoidal arc slot end---)
    '''
    # write footer for section.
    write_g_code(name, text)

    return (end_x_original, end_y_original, cutter_x_final, cutter_y_final)

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
    # surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name, debug)

    # ---Variable List---
    # origin_x = x of bottom left corner
    # origin_y = y of bottom left corner
    # length_x = x length of rectangle
    # length_y = y length of rectangle
    # doc = depth of cut (scalar. Do NOT use negative sign.)
    # dia = diameter of cutter
    # step = step over per pass.
    # z_f =  z feed
    # cut_f = cutting feed
    # safe_z = safe z
    # name = name of file
    # debug = False (default)

    # ---Change History---
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
    write_g_code(name, start_block)

    # initialize starting point
    start_x = origin_x + length_x + dia*2
    start_y = origin_y - dia/2 + step

    # starting G code block
    text = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}   (Rapid to start point)
    F{"%.1f" % z_f}  (set to plunge feed)
    G1 Z-{"%.4f" % doc} (go to cut depth)
    F{"%.1f" % cut_f}  (set to cutting feed)

    G91 (incremental positioning)
    G1 X{"%.4f" % (-dia*2)} (go to starting corner)
    '''
    write_g_code(name, text)

    # length decremental function
    def length_dec(length, step, debug=False):
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
        length_x, rad, last = length_dec(length_x, step)
        if last == True:
            text = \
                f'''   
        G02 X{"%.4f" % (-length_x)} Y{"%.4f" % (dia / 2)} R{"%.4f" % rad}
        G1 Y{"%.4f" % (length_y - step + dia / 2)}
        G1 X{"%.4f" % length_x}
        G1 Y{"%.4f" % (-length_y)}
        '''
            write_g_code(name, text)
            break
        else:
            text = \
                f'''
        G1 X{"%.4f" % (-length_x)}
        G02 X{"%.4f" % (-dia / 2)} Y{"%.4f" % (dia / 2)} R{"%.4f" % (dia / 2)}
        '''
            write_g_code(name, text)

        # left length
        length_y, rad, last = length_dec(length_y, step)
        if last == True:
            text = \
    f'''
    G02 X{"%.4f" % (dia/2)} Y{"%.4f" % length_y} R{"%.4f" % rad}
    G1 X{"%.4f" % (length_x-step+dia/2)}
    G1 Y{"%.4f" % (-length_y)}
    G1 X{"%.4f" % (-length_x)}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 Y{"%.4f" % length_y}
    G02 X{"%.4f" % (dia/2)} Y{"%.4f" % (dia/2)} R{"%.4f" % (dia/2)}
    '''
            write_g_code(name, text)

        # top length
        length_x, rad, last = length_dec(length_x, step)
        if last == True:
            text = \
    f'''
    G02 X{"%.4f" % length_x} Y{"%.4f" % (-dia/2)} R{"%.4f" % rad}
    G1 Y{"%.4f" % (-(length_y-step+dia/2))}    
    G1 X{"%.4f" % (-length_x)}
    G1 Y{"%.4f" % length_y}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 X{"%.4f" % length_x}
    G02 X{"%.4f" % (dia/2)} Y{"%.4f" % (-dia/2)} R{"%.4f" % (dia/2)}
    '''
            write_g_code(name, text)

        # right length
        length_y, rad, last = length_dec(length_y, step)
        if last == True:
            text = \
    f'''
    G02 X{"%.4f" % (-dia/2)} Y{"%.4f" % (-length_y)} R{"%.4f" % rad}
    G1 X{"%.4f" % (-(length_x-step+dia/2))}
    G1 Y{"%.4f" % length_y}
    G1 X{"%.4f" % length_x}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 Y{"%.4f" % (-length_y)}
    G02 X{"%.4f" % (-dia/2)} Y{"%.4f" % (-dia/2)} R{"%.4f" % (dia/2)}
    '''
            write_g_code(name, text)

    text = \
    f'''
    G90 (absolute positioning)
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}   (Rapid to start point)
    '''
    write_g_code(name, text)
    text = \
    f'''
    (---surfacing end---)
    '''     # write footer for section.
    write_g_code(name, text)

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
    # spiral_drill(origin_x, origin_y, dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name, debug)

    # ---Variable List---
    # origin_x = x of center of hole
    # origin_y = y of center of hole
    # dia_hole = hole diameter
    # depth = depth of hole (scalar. Do NOT use negative sign.)
    # step_depth = step per spiral ramp. (scalar. Do NOT use negative sign.)
    # dia = diameter of cutter
    # z_f =  z feed
    # cut_f = cutting feed
    # safe_z = safe z
    # name = name of file
    # debug = False (default)

    # ---Change History---
    # rev: 01-01-10-01
    # Added variable list
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021
    #
    # rev: 01-01-09-01
    # Changed variable name "step" to "step_depth"

    text = '\n(---spiral drill start---)\n'  # write header for section.
    write_g_code(name, text)

    # description
    text = \
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
    write_g_code(name, text)

    # parameters
    text = \
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
    write_g_code(name, text)

    # initialize starting point
    start_x = origin_x + dia_hole/2 - dia/2
    start_y = origin_y

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f'''!!script aborted!!\nspiral_drill\nsafe_z below surface\nsafe_z = {"%.3f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.3f" % safe_z})\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if hole dia is larger 2x tool dia.
    if dia_hole > dia*2:
        print(f'''!!script aborted!!\nspiral_drill\nhole dia is larger 2x tool dia.\nhole dia = {"%.3f" % dia_hole}\ntool dia = {"%.3f" % dia}''')
        text = '''\n(!!script aborted!!)\n(hole dia is larger 2x tool dia)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # starting G code block
    text = \
    f'''
    (---code---)
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % start_x} Y{"%.4f" % start_y}   (Rapid to start point)
    F{"%.1f" % z_f}  (set to plunge feed)
    G1 Z{"%.4f" % 0} (go to starting height)
    F{"%.1f" % cut_f}  (set to cutting feed)
    '''
    write_g_code(name, text)

    z = 0        # initialize current depth

    while depth > 0:
        z = z + step_depth
        depth = depth - step_depth

        if depth > 0:
            text = \
    f'''
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)} Z{"%.4f" % (-z)}
    '''
            write_g_code(name, text)
        else:
            z = z + depth     # calculate remainder cut
            text = \
    f'''
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)} Z{"%.4f" % (-z)}
    G03 X{"%.4f" % start_x} Y{"%.4f" % start_y} I{"%.4f" % (origin_x - start_x)} J{"%.4f" % (origin_y - start_y)}
    G0 Z{"%.4f" % safe_z}    (go to safe Z)
    
    (---spiral drill end---)
    '''
            write_g_code(name, text)
            break           # exit while loop at last cycle

def peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug = False):

    # ---Description---
    # calculates and prints to a txt file the tool path in G code of a peck drilled hole.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after drilling.
    # refer to ALG20210527001 Peck Drilling Algorithm
    # peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug)

    # ---Variable List---
    # hole_x = x of center of hole
    # hole_y = y of center of hole
    # dia_hole = hole diameter
    # depth = depth of hole (scalar. Do NOT use negative sign.)
    # peck_depth = step per peck. (scalar. Do NOT use negative sign.)
    # z_f =  z feed
    # safe_z = safe z
    # retract_z = retract z after each peck.
    # dwell = dwell time in ms at retract z.
    # name = name of file
    # debug = False (default)

    # ---Change History---
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

    text = '\n(---peck drill start---)\n'  # write header for section.
    write_g_code(name, text)

    # description
    text = \
    f'''
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a peck drilled hole.)
    (assumes origin at center of hole.)
    (assumes z=0 at top surface.)
    (return to safe z after drilling.)
    '''
    write_g_code(name, text)

    # parameters
    text = \
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

    write_g_code(name, text)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f'''!!script aborted!!\npeck_drill\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    text = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % hole_x} Y{"%.4f" % hole_y}   (Rapid to start point)
    '''
    write_g_code(name, text)

    if peck_depth > 1 :
        text = \
    f'''
    G0 Z{retract_z} (rapid to retract height: {"%.4f" % retract_z}mm above surface)
    '''
        write_g_code(name, text)
    else:
        text = \
    f'''
    G0 Z{"%.4f" % 1} (rapid to 1mm above surface)
    '''
        write_g_code(name, text)

    # Initialize variables
    current_depth = 0
    target_depth = -peck_depth
    final_depth = -depth
    first = True
    last = False

    text = \
    f'''
    F{"%.1f" % z_f} (set drilling feed)
    '''
    write_g_code(name, text)

    while current_depth > final_depth:

        if first == True:
            first = False   # clear first flag
        else:
            predrill_depth = current_depth + 0.1 * peck_depth    # skip if first peck
            text = \
    f'''
    G0 Z{"%.4f" % predrill_depth}   (rapid to pre-drill depth)
    '''
            write_g_code(name, text)

        if target_depth <= final_depth:

            target_depth = final_depth
            last = True

        # drill to target depth
        text = \
    f'''
    G1 Z{"%.4f" % target_depth} (drill to peck depth)
    '''
        write_g_code(name, text)

        if debug == True:
            print(f'current depth: {current_depth}')
            print(f'target depth: {target_depth}')
            print('')

        if last == False:

            text = \
    f'''
    G0 Z{"%.4f" % retract_z} (rapid to retract height)
    G04 P{dwell}    (dwell ms)
    '''
            write_g_code(name, text)
            current_depth = target_depth
            target_depth = target_depth - peck_depth

        else:

            text = \
    f'''
    G0 Z{"%.4f" % safe_z} (rapid to safe z)
    (---peck drill end---)
    '''
            write_g_code(name, text)
            break  # exit while loop at last cycle

def spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, safe_z, name, debug = False):

    # ---Description---
    # calculates and prints to a txt file the tool path in G code of a spiral surface pocket.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.
    # spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, debug)
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
    #
    # ---Change History---
    # rev: 01-01-10-03
    # removed round() function
    # Added selectable number of finish cuts and finishing feed rate.

    # rev: 01-01-10-01
    # fixed final OD to accommodate cutter diameter.
    # Added rounding to 4 decimal places for G-code coordinates, 3 for label coordinates, 1 for feeds
    # software test run on 07/Sep/2021
    #
    # ------------------------------
    #
    # rev: 01-01-09-02
    # initial release

    title_block = \
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
    write_g_code(name, title_block)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f'''!!script aborted!!\nspiral_surface\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if start dia is larger than tool dia.
    if end_dia < dia:
        print(f'''!!script aborted!!\nspiral_surface\nhole dia is larger tool dia.\nend dia = {"%.4f" % end_dia}\ntool dia = {"%.4f" % dia}''')
        text = f'\n(!!script aborted!!)\n(end dia is larger tool dia)\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # initialize variables
    length = start_dia/2 - dia/2
    end_length = end_dia/2 - dia/2
    segments = 24   # number of segments per spiral.
    i = 360/segments
    last = False

    text = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % (origin_x + length)} Y{"%.4f" % origin_y}   (Rapid to start point)
    F{"%.1f" % z_f}      (set plunge feed)
    G1 Z{"%.4f" % doc}  (go to depth of cut. Use absolute convention)
    F{"%.1f" % cut_f}    (set cutting feed)
    '''
    write_g_code(name, text)

    length = length + step/segments    # increment length.

    while length <= end_length:

        x, y = relative_polar(origin_x, origin_y, 0, length, i) # calculate absolute position
        text = \
    f'''
    G3 X{"%.4f" % x} Y{"%.4f" % y} R{"%.4f" % length}
    '''
        write_g_code(name, text)
        if debug == True:                   #!!! Added debug statement.
            print (f"length : {length}")

        if last == True:
            i = origin_x-x
            j = origin_y-y
            text = \
                f'''
        G3 X{"%.4f" % x} Y{"%.4f" % y} I{"%.4f" % i} J{"%.4f" % j} F{"%.0f" % finish_f}
        (finish cut)
        '''
            i = 1
            while i <= finish_cuts:  # perform finish cuts
                write_g_code(name, text)
                i = i + 1
            text = \
                f'''
                (---spiral surface end---)
                '''
            write_g_code(name, text)
            break

        length = length + step / segments  # calculate length increment per segment.
        i = i + 360 / segments  # increment step.

        if length >= end_length:
            length = end_length
            last = True

def corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z,name, mode = None, debug = False):

    # ---description---
    # calculates and prints to a txt file the tool path in G code of a corner slice.
    # start and end points are located at their respective center points.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.
    # return mode: 1. straight, 2. concave, 3. convex
    # refer to PRT20210515001 Corner Slice
    # corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z,name, mode, debug)

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

    # ---Change History---
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
    write_g_code(name, start_block)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f'''!!script aborted!!\ncorner_slice\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if end dia is larger than tool dia.
    if end_rad*2 < dia:
        print(f'''!!script aborted!!\ncorner_slice\nhole dia is larger tool dia.\nend dia = {"%.4f" % (end_rad*2)}\ntool dia = {"%.4f" % dia}''')
        text = '''\n(!!script aborted!!)\n(end dia is larger tool dia)\n'''  # write header for section.
        write_g_code(name, text)
        quit()

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3 :
            print(f"!!script aborted!!\ncorner_slice\nmode undefined\nmode = {mode}")
            text = '''\n(!!script aborted!!)\n(mode undefined)\n'''  # write header for section.
            write_g_code(name, text)
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

    text = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % x1} Y{"%.4f" % y1}   (Rapid to start point)
    F{"%.1f" % z_f}      (set plunge feed)
    G1 Z{"%.4f" % doc}  (go to depth of cut)
    F{"%.1f" % cut_f}    (set cutting feed)
    '''
    write_g_code(name, text)

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

        text = \
    f'''
    G1 X{"%.4f" % x2} Y{"%.4f" % y2}
    G3 X{"%.4f" % x3} Y{"%.4f" % y3} R{"%.4f" % rad_2}
    G1 X{"%.4f" % x4} Y{"%.4f" % y4}
    '''
        write_g_code(name, text)

        if mode == 1 :
            text = f'''G1 X{"%.4f" % x1} Y{"%.4f" % y1}    (straight line return)\n'''
            write_g_code(name, text)
        elif mode == 2 :
            text = f'''G2 X{"%.4f" % x1} Y{"%.4f" % y1} R{"%.4f" % rad_1} (concave return)\n'''
            write_g_code(name, text)
        elif mode == 3 :
            text = f'''G3 X{"%.4f" % x1} Y{"%.4f" % y1} R-{"%.4f" % rad_1}  (convex return)\n'''
            write_g_code(name, text)

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

    text = \
    f'''
    (---corner slice end---)
    '''
    write_g_code(name, text)

def spiral_boss(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, z_bias_mode=False, z_backlash_bias=0, debug=False):

    # ---Description---
    # calculates and prints to a txt file the tool path in G code of a spiral boss.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # assumes existing clearance around material.
    # return to safe z after surfacing.
    # spiral_boss(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, finish_f, finish_cuts, safe_z, name, z_bias_mode = False, z_backlash_bias = 0, debug = False)

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
    # z_bias_mode = Boolean. Incorporate z backlash biasing toward bottom of backlash. Default: False. !Caution! This will overshoot doc by specified value.
    # z_backlash_bias = Z value to overshoot backlash bias by. Default: 0
    # debug = False (default)

    # ---Change History---
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

    write_g_code(name, title_block)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f'''!!script aborted!!\nspiral_boss\nsafe_z below surface\nsafe_z = {"%.4f" % safe_z}''')
        text = f'''\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {"%.4f" % safe_z})\n'''
        write_g_code(name, text)
        quit()

    # check if end dia is larger than start dia.
    if start_dia < end_dia:
        print(f'''!!script aborted!!\nspiral_boss\nend dia is larger start dia.\nstart dia = {"%.4f" % start_dia}\nend dia = {"%.4f" % end_dia}''')
        text = '''\n(!!script aborted!!)\n(end dia is larger start dia)\n'''
        write_g_code(name, text)
        quit()

    # initialize variables
    length = start_dia/2 + dia/2
    end_length = end_dia/2 + dia/2
    segments = 24   # number of segments per spiral.
    i = -360/segments
    last = False
    x = origin_x + length
    y = origin_y

    text = \
    f'''
    G0 Z{"%.4f" % safe_z}   (Go to safe height)
    G0 X{"%.4f" % x} Y{"%.4f" % y}   (Rapid to start point)
    F{"%.1f" % z_f}      (set plunge feed)
    '''
    write_g_code(name, text)

    if z_bias_mode == True:
        text = \
    f'''
    G1 Z{"%.4f" % (doc+z_backlash_bias)}  (overshoot to z backlash bias)
    '''
        write_g_code(name, text)

    text = \
    f'''
    G1 Z{"%.4f" % doc}  (go to depth of cut. Use absolute convention)
    F{"%.1f" % cut_f}    (set cutting feed)
    '''
    write_g_code(name, text)

    length = length - step/segments    # decrement length.

    while length >= end_length:

        x, y = relative_polar(origin_x, origin_y, 0, length, i) # calculate absolute position
        text = \
    f'''
    G2 X{"%.4f" % x} Y{"%.4f" % y} R{"%.4f" % length}
    '''
        write_g_code(name, text)
        if debug == True:                   #!!! Added debug statement.
            print (f"length : {length}")

        if last == True:
            i = origin_x-x
            j = origin_y-y
            text = \
    f'''
    G2 X{"%.4f" % x} Y{"%.4f" % y} I{"%.4f" % i} J{"%.4f" % j} F{"%.0f" % finish_f}
    (finish cut)
    '''
            i = 1
            while i <= finish_cuts:     # perform finish cuts
                write_g_code(name, text)
                i=i+1
            text = \
    f'''
    (---spiral surface end---)
    '''
            write_g_code(name, text)
            break

        length = length - step/segments     # calculate length decrement per segment.
        i = i - 360/segments                  # increment step.

        if length <= end_length:
            length = end_length
            last = True

def test_cut(dia, name, length_x = 22, length_y = 22, surface_block = True, hole = True):

    # ---Description---
    # Calculates and prints G-code to cut a square block: 10x10mm depth: 3mm after surfacing and adjusted for cutter diameter.
    # assumes origin at bottom left corner of block.
    # assumes z=0 at top surface.
    # assumes material is delrin.
    # assumes cutter is diameter: 3mm
    # starting point at x = -(diameter of cutter + 1), y = top of block
    # refer to PRT20210503001 CNC Test Part
    # test_cut(dia, name, length_x = 22, length_y = 22, surface_block = True, hole = True)

    # ---Variable List---
    # dia = diameter of cutter
    # name = name of G-code file
    # surface_block = boolean. surface block before cutting.
    # hole = boolean. plunge cut hole in center.

    # ---Return Variable List---
    # N/A

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
        doc = 1.0
        step = 2
        z_f = 100
        cut_f = 456.3
        safe_z = 3
        debug = False

        surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name, debug)

    def test_block(dia, doc):

        # ---Variable List---

        safe_z = 3.000  # safe z
        cut_f = 357.6  # cutting feed rate
        z_f = 132.8  # plunge feed rate
        finish_f = 100.0  # finish feed rate
        start_x = -14.00  # x start of slot along neutral axis
        start_y = 5.00  # y start of slot along neutral axis
        step = 1.0  # depth of step per trichoidal slice.
        wos = 6.000  # width of slot
        offset = 0.1  # offset away from cutting surface
        mode = 2  # internal/pocket: 1, external/boss: 2 or slot: 3

        text = \
            f'''
        G0 Z{safe_z}				(Go to safe height)
        G0 X{start_x} Y{5 + wos / 2 + offset}     (rapid to start point!!!)
        F{z_f}                      (set plunge feed rate)
        G01 Z{doc}                   (plunge to depth of cut)
        F{cut_f}                    (set cutting feed)
        '''
        write_g_code(name, text)

        next_x, next_y, cutter_x, cutter_y = tri_slot(start_x, start_y, 4.000, 5.000, step, wos, dia, offset, name,
                                                      start_x, start_y, True, False, mode, False)
        next_x, next_y, cutter_x, cutter_y = tri_arc(next_x, next_y, 5.000, 4.000, step, wos, dia, offset, 1.000, True,
                                                     True, name, cutter_x, cutter_y, False, False, mode, debug=False)
        next_x, next_y, cutter_x, cutter_y = tri_slot(next_x, next_y, 5.000, -4.000, step, wos, dia, offset, name,
                                                      cutter_x, cutter_y, False, False, mode, False)
        next_x, next_y, cutter_x, cutter_y = tri_arc(next_x, next_y, 4.000, -5.000, step, wos, dia, offset, 1.000, True,
                                                     True, name, cutter_x, cutter_y, False, False, mode, debug=False)
        next_x, next_y, cutter_x, cutter_y = tri_slot(next_x, next_y, -4.000, -5.000, step, wos, dia, offset, name,
                                                      cutter_x, cutter_y, False, False, mode, False)
        next_x, next_y, cutter_x, cutter_y = tri_arc(next_x, next_y, -5.000, -4.000, step, wos, dia, offset, 1.000, True,
                                                     True, name, cutter_x, cutter_y, False, False, mode, debug=False)
        next_x, next_y, cutter_x, cutter_y = tri_slot(next_x, next_y, -5.000, 4.000, step, wos, dia, offset, name,
                                                      cutter_x, cutter_y, False, False, mode, False)
        next_x, next_y, cutter_x, cutter_y = tri_arc(next_x, next_y, -4.000, 5.000, step, wos, dia, offset, 1.000, True,
                                                     True, name, cutter_x, cutter_y, False, True, mode, debug=False)

        offset = 0
        start_x_adjusted, start_y_adjusted, end_x_adjusted, end_y_adjusted = linear_offset_adjustment(dia, offset,
                                                                                                      -(5 + dia + 1),
                                                                                                      5, -4, 5, mode)

        text = \
            f'''
        (finish pass)
        G0 Z{safe_z}				(Go to safe height)
        G0 X{start_x_adjusted} Y{start_y_adjusted}      (rapid to start point)
        F{z_f}                      (set plunge feed rate)
        G01 Z{doc}                   (plunge to depth of cut)
        F{finish_f}                    (set cutting feed)
        '''
        write_g_code(name, text)

        rad = 1
        cw = True
        less_180 = True
        feed = None
        ramp_z = None

        end_x, end_y, end_x_adjusted, end_y_adjusted = line(dia, offset, -(5 + dia + 1), 5, -4, 5, name, feed, ramp_z,
                                                            mode)

        i = 1
        while i <= 3:  # run 3 finish passes
            text = f'\n(finish pass  #: {i})\n'
            write_g_code(name, text)

            end_x, end_y, end_x_adjusted, end_y_adjusted = line(dia, offset, end_x, end_y, 4, 5, name, feed, ramp_z,
                                                                mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = arc(dia, offset, end_x, end_y, 5, 4, name, rad, cw,
                                                               less_180, feed, ramp_z, mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = line(dia, offset, end_x, end_y, 5, -4, name, feed, ramp_z,
                                                                mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = arc(dia, offset, end_x, end_y, 4, -5, name, rad, cw, less_180,
                                                               feed, ramp_z, mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = line(dia, offset, end_x, end_y, -4, -5, name, feed, ramp_z,
                                                                mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = arc(dia, offset, end_x, end_y, -5, -4, name, rad, cw, less_180,
                                                               feed, ramp_z, mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = line(dia, offset, end_x, end_y, -5, 4, name, feed, ramp_z,
                                                                mode)
            end_x, end_y, end_x_adjusted, end_y_adjusted = arc(dia, offset, end_x, end_y, -4, 5, name, rad, cw,
                                                               less_180, feed, ramp_z, mode)

            i = i + 1

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
        depth = abs(depth)  # depth of hole (scalar. Do NOT use negative sign.)
        peck_depth = depth  # step per peck. (scalar. Do NOT use negative sign.)
        z_f = 50.2  # z feed
        safe_z = 3  # safe z
        retract_z = 1.5  # retract z after each peck.
        dwell = 0  # dwell time in ms at retract z.

        peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug=False)

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
    write_g_code(name,info)

    if surface_block == True:
        surface_test_block(dia, length_x, length_y)
        doc = -4
    else:
        doc = -3

    test_block(dia, doc)

    if hole == True:
        plunge_drill(doc)

    text = \
    f'''
    (---Test Cut End---)
    '''
    write_g_code(name,info)

# ---------File Name Variables------------

doc_number = datetime.now().strftime("%Y%m%d-%H%M%S")  # get date time stamp (YYYYMMDD-HHMMSS) for file name.
prefix = 'GCE'
file_name = 'TBD'
rev = 'TBD'
name = prefix + doc_number + f' Rev{rev} ' + file_name   # file name

# ---------General Variables------------

clear_z = 3.000  # safe z
initial_x = 0  # initial x
initial_y = 0  # initial y
start_z = 0.000  # start z
terminal_x = 0  # terminal x
terminal_y = 0  # terminal y
cut_f = 229.4  # cutting feed rate
z_f = 34.4  # plunge feed rate
finish_f = 77.6 # finish feed rate
rpm = 2900  # spindle speed
cutter_dia = 3.0  # diameter of cutter before adjustment
tol = -0.000    # adjustment for cutter tolerance
dia = cutter_dia + tol  # adjust cutter tolerance
loc = 12    # length of cutter
flute = 4   # number of flutes
surface_speed = 15  #Surface Speed (m/min)
chipload = 0.007 # Chipload (mm/tooth)
cutter_material = "TBD"    # material of cutter. e.g. HSS, carbide, cobalt
coating = "TBD"    # coating of cutter.  e.g. None, AT, TiN
x_origin = "TBD"      # x origin e.g. center of part, left edge
y_origin = "TBD"    # y origin. e.g. center of part, bottom edge
z_origin = "TBD"    # z origin e.g. top surface of part, top surface of vise
part_material = "TBD"   # material of part. e.g. Delrin, ABS, SS304, CoCr
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

write_g_code(name, info)
write_g_code(name, var)
write_g_code(name, start_block)

# ===========================================================================
# ================================ G-code start =============================
# ===========================================================================

test_cut(dia, name, length_x = 22, length_y = 22, surface_block = True, hole = True)

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
write_g_code(name, end_block)