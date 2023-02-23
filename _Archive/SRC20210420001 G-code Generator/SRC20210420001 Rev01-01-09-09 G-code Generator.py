# =============================== Title Block ===============================
#
# file name: SRC20210420001 G-code Generator
#
# ---Description---
# This program calculates and prints to a txt file the trichoidal tool path in G code.
# The trichoidal tool path can be made of segments of straight or arc slots.
# start and end points are located at slot arc center points.
# Each segment is defined using the following input parameters:
#   start_x
#   start_y
#   end_x
#   end_y
#   tool step over
#   width of slot
#   tool diameter
#   radius of arc slot (for arc slot)
#   acute or obtuse arc boolean (for arc slot)
#   optional debug boolean for debugging information
#
# ---Change History---
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
# ------------------------------
# rev: 01-01-07
# date: 29/Apr/2021
# description:
#
#   line 400 to 406:
#       Found bug in initial arc loop direction.
#       Added if condition for first loop.
#       changed from G2 to G3 for first loop.
#
#   line 520:
#       G0 Z#103				(Go to safe height)
#       to
#       G0 Z{safe_z}				(Go to safe height)
#
# ------------------------------
#
# rev: 01-01-05
# date: 29/Apr/2021
# description: initial release
# ------------------------------
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

def tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, cutter_x, cutter_y, first_slot=True, last_slot=True, debug = False):
    # Calculates and prints to a txt file the trichoidal tool path in G code of a straight slot.
    # returns last position of cutter and end position of slot.
    # start and end points are located at slot arc center points.
    # assumes that cutter is at cutting depth.
    # does not return to safe z.
    # Each segment is defined using the following input parameters:
    #   start_x
    #   start_y
    #   end_x
    #   end_y
    #   tool step over
    #   width of slot
    #   tool diameter
    #   optional debug boolean for debugging information

    text = '\n(---trichoidal linear slot start---)\n'     # write header for section.
    write_g_code(name, text)

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
                if (delta_x > 0.0001) and (delta_y > 0.0001):       # if cutter is at start point skip else reorient.
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
                last_x = end_x
                next_y = end_y
            else:
                x_temp = length
                y_temp = -rad_arc
                x5, y5 = relative_coordinate(start_x, start_y, angle, x_temp, y_temp, debug)
                line_3 = \
    f'''G03 X{"%.4f" % x1} y{"%.4f" % y1} R{"%.4f" % rad_arc}
    G1 X{"%.4f" % x5} Y{"%.4f" % y5}
    '''
                last_x = x5
                next_y = y5
        else:
            line_3 = \
    f'''G03 X{"%.4f" % x1} y{"%.4f" % y1} R{"%.4f" % rad_arc}
    '''
        write_g_code(name, line_3)

        i = i + 1

    text = '\n(---trichoidal linear slot end---)\n'
    write_g_code(name, text)

    return (end_x, end_y, last_x, next_y)

def tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot=True, last_slot=True, debug = False):
    # ---description---
    # Calculates and prints to a txt file the trichoidal tool path in G code of a counter clockwise arc.
    # returns last position of cutter and end position of arc.
    # refer to "PRT20210421001 Trichoidal Arc Calculator", "MEM20210522001 Trichoidal Arc", "MEM20210429002 Trichoidal Notes", "ALG20210520001 Trichoidal Arc Algorithm"
    # start and end points are located at slot arc center points.
    # assumes that cutter is at cutting depth.
    # does not return to safe z.
    # does not set cutting feed.

    # ---Change History---
    # rev: 01-01-09-08
    # initial release

    # ---notes---
    # performed test cut on XX/May/2021

    text = '\n(---trichoidal arc slot start---)\n'  # write header for section.
    write_g_code(name, text)

    # description
    text = \
    f'''
    (---description---)
    (Calculates and prints to a txt file the trichoidal tool path in G code of a counter clockwise arc.)
    (returns last position of cutter and end position of arc.)
    (refer to "PRT20210421001 Trichoidal Arc Calculator", "MEM20210522001 Trichoidal Arc", "MEM20210429002 Trichoidal Notes")
    (start and end points are located at slot arc center points.)
    (assumes that cutter is at cutting depth.)
    (does not return to safe z.)
    (does not set cutting feed.)
    '''
    write_g_code(name, text)

    # parameters
    text = \
    f'''
    (---parameter---)
    (start X{start_x} Y{start_y})
    (end X{end_x} Y{end_y})
    (cutter position X{cutter_x} Y{cutter_y})
    (first slot : {first_slot})
    (last slot : {last_slot})
    (step : {step})
    (width of slot : {wos})
    (slot radius : {rad_slot})
    (clockwise : {cw})
    (acute angle: {less_180})
    (cutter dia : {dia})
    '''
    write_g_code(name, text)

    # check if width of slot is smaller tool dia
    if wos <= dia:
        print(f"!!script aborted!!\nwidth of slot is smaller tool dia.\nwidth of slot= {wos}\ntool dia = {dia}")
        text = '\n(!!script aborted!!)\n(width of slot is smaller tool dia)\n'  # write header for section.
        write_g_code(name, text)
        quit()

    skip_1 = False   # initialize skip_1 flag

    vec_x = end_x - start_x
    vec_y = end_y - start_y
    linear_length = math.sqrt(vec_x ** 2 + vec_y ** 2)      # calculate linear length from start point to end point

    # check if diameter of arc is larger than linear length
    if rad_slot*2 < linear_length:
        print(f"!!script aborted!!\ndiameter of arc is larger than linear length.\ndiameter of arc = {rad_slot*2}\nlinear length = {linear_length}")
        text = '\n(!!script aborted!!)\n(diameter of arc is larger than linear length)\n'  # write header for section.
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

            #determine if angle between current/now cutter postion and first position (x1, y1) is acute or obtuse
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
            text = f"{dir_1} X{end_x} Y{end_y} R{rad_slot}"
            write_g_code(name, text)
            last_x = end_x
            next_y = end_y
        else:       # advance tool to cutting position for next slot.
            text = f"{dir_1} X{x2} Y{y2} R{rad_slot-rad_arc}"
            write_g_code(name, text)
            last_x = x2
            next_y = y2

    text = '\n(---trichoidal arc slot end---)\n'     # write footer for section.
    write_g_code(name, text)

    return (end_x, end_y, last_x, next_y)

def surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name,  debug = False):
    # ---description---
    # calculates and prints to a txt file the tool path in G code to surface a rectangular part.
    # assumes climb milling.
    # assumes origin at bottom left corner.
    # assumes z=0 at top surface.
    # starts at x = 0, y = -(2 * diameter of cutter) from bottom left corner.
    # cuts in a clockwise direction from the outside to the center.
    # return to origin after surfacing.
    # refer to PRT20210510003 Surfacing Calculator

    # ---notes---
    # performed test cut on 13/May/2021

    text = '\n(---surfacing start---)\n'  # write header for section.
    write_g_code(name, text)

    # description
    text = \
        f'''
    (This program calculates the tool path to surface a rectangular part.)
    (assumes climb milling.)
    (assumes origin at bottom left corner.)
    (assumes z=0 at top surface.)
    (starts at x = 0, y = -(2 * diameter of cutter) from bottom left corner.)
    (cuts in a clockwise direction from the outside to the center.)
    (return to origin after surfacing.)
    '''
    write_g_code(name, text)

    # parameters
    text = \
    f'''
    (---parameter---)
    (origin: X{origin_x} Y{origin_y})
    (length x: {length_x})
    (length y: {length_y})
    (depth of cut: {doc})
    (step: {step})
    (plunge feed: {z_f})
    (cutting feed: {cut_f})
    (safe Z: {safe_z})
    '''
    write_g_code(name, text)

    # initialize starting point
    start_x = origin_x - dia/2 + step
    start_y = origin_y - dia*2

    # starting G code block
    text = \
    f'''
    G0 Z{safe_z}   (Go to safe height)
    G0 X{start_x} Y{start_y}   (Rapid to start point)
    F{z_f}  (set to plunge feed)
    G1 Z-{doc} (go to cut depth)
    F{cut_f}  (set to cutting feed)

    G91 (incremental positioning)
    G1 Y{dia*2} (go to starting corner)
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

        # left length
        length_y, rad, last = length_dec(length_y, step)
        if last == True:
            text = \
    f'''
    G02 X{dia/2} Y{length_y} R{rad}
    G1 X{length_x-step+dia/2}
    G1 Y{-length_y}
    G1 X{-length_x}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 Y{length_y}
    G02 X{dia/2} Y{dia/2} R{dia/2}
    '''
            write_g_code(name, text)

        # top length
        length_x, rad, last = length_dec(length_x, step)
        if last == True:
            text = \
    f'''
    G02 X{length_x} Y{-dia/2} R{rad}
    G1 Y{-(length_y-step+dia/2)}    
    G1 X{-length_x}
    G1 Y{length_y}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 X{length_x}
    G02 X{dia / 2} Y{-dia / 2} R{dia / 2}
    '''
            write_g_code(name, text)

        # right length
        length_y, rad, last = length_dec(length_y, step)
        if last == True:
            text = \
    f'''
    G02 X{-dia/2} Y{-length_y} R{rad}
    G1 X{-(length_x-step+dia/2)}
    G1 Y{length_y}
    G1 X{length_x}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 Y{-length_y}
    G02 X{-dia / 2} Y{-dia / 2} R{dia / 2}
    '''
            write_g_code(name, text)

        # bottom length
        length_x, rad, last = length_dec(length_x, step)
        if last == True:
            text = \
    f'''   
    G02 X{-length_x} Y{dia/2} R{rad}
    G1 Y{length_y-step+dia/2}
    G1 X{length_x}
    G1 Y{-length_y}
    '''
            write_g_code(name, text)
            break
        else:
            text = \
    f'''
    G1 X{-length_x}
    G02 X{-dia / 2} Y{dia / 2} R{dia / 2}
    '''
            write_g_code(name, text)

    text = \
    f'''
    G90 (absolute positioning)
    G0 Z{safe_z}   (Go to safe height)
    G0 X{start_x} Y{start_y}   (Rapid to start point)
    '''
    write_g_code(name, text)
    text = '\n(---surfacing end---)\n'     # write footer for section.
    write_g_code(name, text)

def spiral_drill(origin_x, origin_y, dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name,  debug = False):
    # ---description---
    # calculates and prints to a txt file the tool path in G code of a spiral drilled hole.
    # assumes climb milling.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # starts at right edge of the hole (i.e. x = diameter of hole-dia of cutter, y = 0).
    # cuts in a counter-clockwise direction from the outside to the center.
    # return to origin after surfacing.
    # refer to PRT20210512001 Spiral Drill

    # ---Change History---
    # rev: 01-01-09-01
    # Changed variable name "step" to "step_depth"

    # ---notes---
    # performed test cut on 13/May/2021

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
    (circle center: X{origin_x} Y{origin_y})
    (diameter: {dia_hole})
    (depth: {depth})
    (step_depth: {step_depth})
    (feed: {cut_f})
    (safe Z: {safe_z})
    '''
    write_g_code(name, text)

    # initialize starting point
    start_x = origin_x + dia_hole/2 - dia/2
    start_y = origin_y

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f"!!script aborted!!\nsafe_z below surface\nsafe_z = {safe_z}")
        text = '\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {safe_z})\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # check if hole dia is larger 2x tool dia.
    if dia_hole > dia*2:
        print(f"!!script aborted!!\nhole dia is larger 2x tool dia.\nhole dia = {dia_hole}\ntool dia = {dia}")
        text = '\n(!!script aborted!!)\n(hole dia is larger 2x tool dia)\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # starting G code block
    text = \
    f'''
    (---code---)
    G0 Z{safe_z}   (Go to safe height)
    G0 X{start_x} Y{start_y}   (Rapid to start point)
    F{z_f}  (set to plunge feed)
    G1 Z{0.00} (go to starting height)
    F{cut_f}  (set to cutting feed)
    '''
    write_g_code(name, text)

    z = 0        # initialize current depth

    while depth > 0:
        z = z + step_depth
        depth = depth - step_depth

        if depth > 0:
            text = \
    f'''
    G03 X{start_x} Y{start_y} I{origin_x - start_x} J{origin_y - start_y} Z{-z}
    '''
            write_g_code(name, text)
        else:
            z = z + depth     # calculate remainder cut
            text = \
    f'''
    G03 X{start_x} Y{start_y} I{origin_x - start_x} J{origin_y - start_y} Z{-z}
    G03 X{start_x} Y{start_y} I{origin_x - start_x} J{origin_y - start_y}
    G0 Z{safe_z}    (go to safe Z)
    
    (---spiral drill end---)
    '''
            write_g_code(name, text)
            break           # exit while loop at last cycle

def peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name,  debug = False):

    # ---description---
    # calculates and prints to a txt file the tool path in G code of a peck drilled hole.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after drilling.
    # refer to ALG20210527001 Peck Drilling Algorithm

    # ---Change History---
    # rev: 01-01-09-09
    # changed start height above surface from "1mm or less" to "1mm or peck depth, whichever is greater".
    # reorganized code.
    # added algorithm flow chart ALG20210527001 Rev01 Peck Drilling Algorithm
    #
    # rev: 01-01-09-01
    # initial release

    # ---notes---
    # performed test cut on XX/May/2021

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
    (Center of hole: X{hole_x} Y{hole_y})
    (diameter: {dia_hole})
    (depth: {depth})
    (peck depth: {peck_depth})
    (drilling feed: {z_f})
    (safe Z: {safe_z})
    (dwell: {dwell})
    (retract z: {retract_z})
    '''
    write_g_code(name, text)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f"!!script aborted!!\nsafe_z below surface\nsafe_z = {safe_z}")
        text = '\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {safe_z})\n'  # write header for section.
        write_g_code(name, text)
        quit()

    text = \
    f'''
    G0 Z{safe_z}   (Go to safe height)
    G0 X{hole_x} Y{hole_y}   (Rapid to start point)
    '''
    write_g_code(name, text)

    if peck_depth > 1 :
        text = \
    f'''
    G0 Z{peck_depth} (rapid to peck depth: {peck_depth}mm above surface)
    '''
        write_g_code(name, text)
    else:
        text = \
    f'''
    G0 Z1 (rapid to 1mm above surface)
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
    F{z_f} (set drilling feed)
    '''
    write_g_code(name, text)

    while current_depth >= final_depth:

        if first == True:
            first = False   # clear first flag
        else:
            predrill_depth = current_depth + 0.1 * peck_depth    # skip if first peck
            text = \
    f'''
    G0 Z{"%.4f" % predrill_depth}   (rapid to pre-drill depth)
    '''
            write_g_code(name, text)


        if target_depth < final_depth:

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

def spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, safe_z, name,  debug = False):

    # ---description---
    # calculates and prints to a txt file the tool path in G code of a spiral surface pocket.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.

    # ---Change History---
    # rev: 01-01-09-02
    # initial release

    # ---notes---
    # performed test cut on XX/May/2021

    text = '\n(---spiral surface start---)\n'  # write header for section.
    write_g_code(name, text)

    # description
    text = \
    f'''
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a spiral surface pocket.)
    (assumes origin at center of hole.)
    (assumes z=0 at top surface.)
    (return to safe z after surfacing.)
    '''
    write_g_code(name, text)

    # parameters
    text = \
    f'''
    (---parameter---)
    (origin: X{origin_x} Y{origin_y})
    (pocket diameter: {end_dia})
    (depth of cut: {doc})
    (step: {step})
    (plunge feed: {z_f})
    (cutting feed: {cut_f})
    (safe Z: {safe_z})
    '''
    write_g_code(name, text)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f"!!script aborted!!\nsafe_z below surface\nsafe_z = {safe_z}")
        text = '\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {safe_z})\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # check if start dia is larger than tool dia.
    if end_dia < dia:
        print(f"!!script aborted!!\nhole dia is larger tool dia.\nend dia = {end_dia}\ntool dia = {dia}")
        text = '\n(!!script aborted!!)\n(end dia is larger tool dia)\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # initialize variables
    length = start_dia/2 - dia/2
    i = 1
    last = False

    text = \
    f'''
    G0 Z{safe_z}   (Go to safe height)
    G0 X{origin_x + length} Y{origin_y}   (Rapid to start point)
    F{z_f}      (set plunge feed)
    G1 Z-{doc}  (go to depth of cut)
    F{cut_f}    (set cutting feed)
    '''
    write_g_code(name, text)

    length = length + step*1/360    # increment length

    while length <= end_dia/2 :

        x, y = relative_polar(origin_x, origin_y, 0, length, i) # calculate absolute position
        text = \
    f'''
    G3 X{x} Y{y} R{length}
    '''
        write_g_code(name, text)
        print (f"length : {length}")

        if last == True:
            text = \
            f'''
            G3 X{x} Y{y} I{origin_x-x} J{origin_y-y}
            '''
            write_g_code(name, text)
            break

        length = length + step*1/360
        i = i +1

        if length >= end_dia/2 :
            length = end_dia/2
            last = True

def corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z,name, mode = 0, debug = False):
    # ---description---
    # calculates and prints to a txt file the tool path in G code of a corner slice.
    # start and end points are located at their respective center points.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.
    # return mode: 1. straight, 2. concave, 3. convex
    # refer to PRT20210515001 Corner Slice

    # ---Change History---
    # rev: 01-01-09-05
    # initial release

    # ---notes---
    # performed test cut on XX/May/2021

    text = '\n(---corner slice start---)\n'  # write header for section.
    write_g_code(name, text)

    # description
    text = \
    f'''
    (---description---)
    (calculates and prints to a txt file the tool path in G code of a corner slice.)
    (start and end points are located at their respective center points.)
    (assumes z=0 at top surface.)
    (return to safe z after surfacing.)
    (refer to PRT20210515001 Corner Slice)
    '''
    write_g_code(name, text)

    # parameters
    text = \
    f'''
    (---parameter---)
    (start X{start_x} Y{start_y})
    (end X{end_x} Y{end_y})
    (start rad : {start_rad})
    (end rad : {end_rad})
    (depth of cut: {doc})
    (cutter dia : {dia})
    (step: {step})
    (plunge feed: {z_f})
    (cutting feed: {cut_f})
    (safe Z: {safe_z})
    '''
    write_g_code(name, text)

    # check if safe_z is above surface.
    if safe_z <= 0:
        print(f"!!script aborted!!\nsafe_z below surface\nsafe_z = {safe_z}")
        text = '\n(!!script aborted!!)\n(safe_z below surface)\n(safe_z = {safe_z})\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # check if end dia is larger than tool dia.
    if end_rad*2 < dia:
        print(f"!!script aborted!!\nhole dia is larger tool dia.\nend dia = {end_rad*2}\ntool dia = {dia}")
        text = '\n(!!script aborted!!)\n(end dia is larger tool dia)\n'  # write header for section.
        write_g_code(name, text)
        quit()

    # check if mode is defined.
    if mode != 1 and mode != 2 and mode != 3 :
            print(f"!!script aborted!!\nmode undefined\nmode = {mode}")
            text = '\n(!!script aborted!!)\n(mode undefined)\n'  # write header for section.
            write_g_code(name, text)
            quit()
    # initialize variables
    vec_x = end_x - start_x     # x vector length of slot
    vec_y = end_y - start_y     # y vector length of slot
    length = math.sqrt(vec_x ** 2 + vec_y ** 2)     # length of slot

    # calculate arc angle and dia angle
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
    G0 Z{safe_z}   (Go to safe height)
    G0 X{x1} Y{y1}   (Rapid to start point)
    F{z_f}      (set plunge feed)
    G1 Z-{doc}  (go to depth of cut)
    F{cut_f}    (set cutting feed)
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
    G1 X{x2} Y{y2}
    G3 X{x3} Y{y3} R{rad_2}
    G1 X{x4} Y{y4}
    '''
        write_g_code(name, text)

        if mode == 1 :
            text = f"G1 X{x1} Y{y1}    (straight line return)\n"
            write_g_code(name, text)
        elif mode == 2 :
            text = f"G2 X{x1} Y{y1} R{rad_1} (concave return)\n"
            write_g_code(name, text)
        elif mode == 3 :
            text = f"G3 X{x1} Y{y1} R-{rad_1}  (convex return)\n"
            write_g_code(name, text)

        if last == True:
            text = f"\n(last rad = {rad_2})\n(end rad = {end_rad})"
            write_g_code(name, text)
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

    text = '\n(---corner slice end---)\n'
    write_g_code(name, text)

# ---------File Name------------

doc_number = datetime.now().strftime("%Y%m%d-%H%M%S")  # get date time stamp (YYYYMMDD-HHMMSS) for file name.
prefix = 'GCE'
file_name = 'Test'
rev = '01'
name = prefix + doc_number + f' Rev{rev} ' + file_name   # file name

# ---------Input Variables------------

safe_z = 3.000  # safe z
doc = -3.000  # depth of cut
wos = 6.000  # width of slot
start_x = 7  # start x
start_y = 5  # start y
start_z = 0.000  # start z
end_x = start_x  # end x
end_y = start_y  # end y
cut_f = 572.5  # cutting feed rate
z_f = 79.1  # plunge feed rate
finish_f = 77.6 # finish feed rate
step = 0.25  # step over width
rpm = 2900  # spindle speed
dia = 3.0  # diameter of cutter
loc = 12    # length of cutter
flute = 4   # number of flutes
cutter_material = "carbide"    # material of cutter
coating = "AT"    # coating of cutter
x_origin = "left edge of part"      # x origin
y_origin = "bottom edge of part"    # y origin
z_origin = "top surface of part"    # z origin
part_material = "delrin"   # material of part

# description
description = \
f'''
(This program calculates the tool path to surface a rectangular part.)
(assumes climb milling.)
(assumes origin at bottom left corner.)
(assumes z=0 at top surface.)
(starts at x = 0, y = -(2 * diameter of cutter) from bottom left corner.)
(cuts in a clockwise direction from the outside to the center.)
(return to origin after surfacing.)
'''

# -----------------------------------

# create new date time stamped file and open for writing
info = \
f'''
(==========================)    
(file_name: {name})
(==========================)  

(---Description---)
{description}
(TOOL/MILL, dia: {dia}, LOC:{loc}, {flute} Flute, {cutter_material}, {coating})
(--X origin: {x_origin}--)
(--Y origin: {y_origin}--)
(--Z origin: {z_origin}--)
(Part material: {part_material})
(G-code is generated using Python script "{os.path.basename(__file__)}")

(---Compiler---)
(UCCNC v1.2111)
(DEMO_UC400ETH)

(---Change History---)
(NA)    

(---Bug List---)
(NA)
'''

var = \
f'''
(===input variables===)
(safe_z              = {"%.3f" % safe_z})
(depth_of_cut        = {"%.3f" % doc})
(width_of_slot       = {"%.3f" % wos})
(start_x             = {"%.3f" % start_x})
(start_y             = {"%.3f" % start_y})
(start_z             = {"%.3f" % start_z})
(end_x               = {"%.3f" % end_x})
(end_y               = {"%.3f" % end_y})
(cut_feed            = {"%.1f" % cut_f})
(plunge_feed         = {"%.1f" % z_f})
(finish_feed         = {"%.1f" % finish_f})
(diameter_of_cutter  = {"%.1f" % dia})
(stepover_width      = {"%.3f" % step})
(spindle_speed       = {"%.0f" % rpm})
'''

start_block = \
f'''
(===Main Start===)
G90			   (Absolute XYZ)
G21G64G17	   (mm, Best Speed Path, XY Plane)
M3 S{rpm}      (Spindle Speed)
G0 Z{safe_z}   (Go to safe height)
G0 X{start_x} Y{start_y}   (Rapid to start point)
'''

write_g_code(name, info)
write_g_code(name, var)
write_g_code(name, start_block)

# def tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, cutter_x, cutter_y, first_slot=False, last_slot=False, debug = False)
# last_x, next_y = tri_slot(start_x, start_y, end_x, end_y, step, wos, dia, name, debug = False)
# function for cutting straight slot (returns last position)
# step = tool step over
# wos = width of slot
# dia = tool diameter
# name = file name
# debug = optional debug boolean for debugging information

#def tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot=True, last_slot=True, debug = False):
    # ---description---
    # Calculates and prints to a txt file the trichoidal tool path in G code of a counter clockwise arc.
    # returns last position of cutter and end position of arc.
    # refer to "PRT20210421001 Trichoidal Arc Calculator", "PRT20210523001 Trichoidal Arc", "MEM20210522001 Trichoidal Arc Datum", "MEM20210429002 Trichoidal Notes"
    # start and end points are located at slot arc center points.
    # assumes that cutter is at cutting depth.
    # does not return to safe z.
    # does not set cutting feed.

#def surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name,  debug = False):
    # calculates and prints to a txt file the tool path in G code to surface a rectangular part.
    # assumes climb milling.
    # assumes origin at bottom left corner.
    # assumes z=0 at top surface.
    # starts at x = 0, y = -(2 * diameter of cutter) from bottom left corner.
    # cuts in a clockwise direction from the outside to the center.
    # return to origin after surfacing.
    # refer to PRT20210510003 Surfacing Calculator

#def spiral_drill(origin_x, origin_y, dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name,  debug = False):
    # calculates and prints to a txt file the tool path in G code of a spiral drilled hole.
    # assumes climb milling.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # starts at right edge of the hole (i.e. x = diameter of hole-dia of cutter, y = 0).
    # cuts in a counter-clockwise direction from the outside to the center.
    # return to origin after surfacing.

#def peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name,  debug = False):
    # calculates and prints to a txt file the tool path in G code of a peck drilled hole.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.

#def spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, safe_z, name,  debug = False):
    # calculates and prints to a txt file the tool path in G code of a spiral surface pocket.
    # assumes origin at center of hole.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.

#def corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z,name, mode = 0, debug = False):
    # ---description---
    # calculates and prints to a txt file the tool path in G code of a corner slice.
    # start and end points are located at their respective center points.
    # assumes z=0 at top surface.
    # return to safe z after surfacing.
    # return mode: 1. straight, 2. concave, 3. convex
    # refer to PRT20210515001 Corner Slice

# ============================================================================
# ================================ code start ================================

origin_x = 0
origin_y = 0
length_x = 18
length_y = 75

doc = 1
dia = 3
step = 1.5
safe_z = 3
cut_f = 316.4
z_f = 79.1
#surface(origin_x, origin_y, length_x, length_y, doc, dia, step, z_f, cut_f, safe_z, name, True)

origin_x = 5
origin_y = 32.5
dia_hole = 6
depth = 12.84531
cut_f = 292.6
finish_f = 27.9
step_depth = 1.5
#spiral_drill(origin_x, origin_y,dia_hole, depth, step_depth, dia, z_f, cut_f, safe_z, name,  False)

hole_x = 0
hole_y = 0
depth = 11.0
peck_depth = 1.5
z_f = 79.1
safe_z = 3
retract_z = 1
dwell = 1000
debug = True
peck_drill(hole_x, hole_y, dia_hole, depth, peck_depth, z_f, safe_z, retract_z, dwell, name, debug)

origin_x = 5
origin_y = 32.5
start_dia = 8
end_dia = 12
doc = 1
dia = 3
step = 1.5
z_f = 27.9
cut_f = 292.6
safe_z = 3
#spiral_surface(origin_x, origin_y, start_dia, end_dia, doc, dia, step, z_f, cut_f, safe_z, name, False)

start_x = 13
start_y = -10
end_x = -8
end_y = -13
start_rad = 11
end_rad = 5
doc = 3
step = 1
dia = 3
z_f = 27.9
cut_f = 292.6
safe_z = 3
mode = 3
#corner_slice(start_x, start_y, end_x, end_y, start_rad, end_rad, doc, dia, step, z_f, cut_f, safe_z, name, mode)

cut_f = 572.5  # cutting feed rate
z_f = 79.1  # plunge feed rate
finish_f = 77.6 # finish feed rate

start_x = 7  # start x
start_y = 5  # start y
end_x = 35 # end x
end_y = 5  # end y
rad_slot = 18.5

step = 1
wos = 15  # width of slot
dia = 3.0  # diameter of cutter
cut_f = 500

cw = False
less_180 = True
first_slot = True
last_slot = True

cutter_x = start_x
cutter_y = start_y

text = f"G0 X{start_x} Y{start_y}   (Rapid to start point)"
text = f"G0 X{cutter_x} Y{cutter_y}"
write_g_code(name, text)
text = f"F{cut_f}"
write_g_code(name, text)

# last_x, next_y, cutter_x, cutter_y = tri_arc(start_x, start_y, end_x, end_y, step, wos, dia, rad_slot, cw, less_180, name, cutter_x, cutter_y, first_slot, last_slot, False)
# ================================ code end =================================
# ===========================================================================

end_block = \
f'''
G0 Z{safe_z}				(Go to safe height)
G0 X{end_x} Y{end_y}
M5						(Spindle Stop)
M30					(End & Rewind)
(===Main End===)
'''
write_g_code(name, end_block)