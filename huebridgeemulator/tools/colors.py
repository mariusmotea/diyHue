import math
import colorsys

from typing import Tuple


# pylint: disable=invalid-sequence-index
def color_hs_to_xy(iH: float, iS: float) -> Tuple[float, float]:
    """Convert an hs color to its xy representation."""
    return color_RGB_to_xy(*color_hs_to_RGB(iH, iS))

# pylint: disable=invalid-name, invalid-sequence-index
def color_RGB_to_xy(iR: int, iG: int, iB: int) -> Tuple[float, float]:
    """Convert from RGB color to XY color."""
    return color_RGB_to_xy_brightness(iR, iG, iB)[:2]

# Taken from:
# http://www.developers.meethue.com/documentation/color-conversions-rgb-xy
# License: Code is given as is. Use at your own risk and discretion.
# pylint: disable=invalid-name, invalid-sequence-index
def color_RGB_to_xy_brightness(
        iR: int, iG: int, iB: int) -> Tuple[float, float, int]:
    """Convert from RGB color to XY color."""
    if iR + iG + iB == 0:
        return 0.0, 0.0, 0

    R = iR / 255
    B = iB / 255
    G = iG / 255

    # Gamma correction
    R = pow((R + 0.055) / (1.0 + 0.055),
            2.4) if (R > 0.04045) else (R / 12.92)
    G = pow((G + 0.055) / (1.0 + 0.055),
            2.4) if (G > 0.04045) else (G / 12.92)
    B = pow((B + 0.055) / (1.0 + 0.055),
            2.4) if (B > 0.04045) else (B / 12.92)

    # Wide RGB D65 conversion formula
    X = R * 0.664511 + G * 0.154324 + B * 0.162028
    Y = R * 0.283881 + G * 0.668433 + B * 0.047685
    Z = R * 0.000088 + G * 0.072310 + B * 0.986039

    # Convert XYZ to xy
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)

    # Brightness
    Y = 1 if Y > 1 else Y
    brightness = round(Y * 255)

    return round(x, 3), round(y, 3), brightness

# pylint: disable=invalid-sequence-index
def color_hs_to_RGB(iH: float, iS: float) -> Tuple[int, int, int]:
    """Convert an hsv color into its rgb representation."""
    return color_hsv_to_RGB(iH, iS, 100)

# pylint: disable=invalid-sequence-index
def color_hsv_to_RGB(iH: float, iS: float, iV: float) -> Tuple[int, int, int]:
    """Convert an hsv color into its rgb representation.

    Hue is scaled 0-360
    Sat is scaled 0-100
    Val is scaled 0-100
    """
    fRGB = colorsys.hsv_to_rgb(iH/360, iS/100, iV/100)
    return (int(fRGB[0]*255), int(fRGB[1]*255), int(fRGB[2]*255))

# pylint: disable=invalid-sequence-index
def color_xy_to_hs(vX: float, vY: float) -> Tuple[float, float]:
    """Convert an xy color to its hs representation."""
    h, s, _ = color_RGB_to_hsv(*color_xy_to_RGB(vX, vY))
    return (h, s)


def color_xy_to_RGB(vX: float, vY: float) -> Tuple[int, int, int]:
    """Convert from XY to a normalized RGB."""
    return color_xy_brightness_to_RGB(vX, vY, 255)


# pylint: disable=invalid-sequence-index
def color_RGB_to_hsv(iR: int, iG: int, iB: int) -> Tuple[float, float, float]:
    """Convert an rgb color to its hsv representation.

    Hue is scaled 0-360
    Sat is scaled 0-100
    Val is scaled 0-100
    """
    fHSV = colorsys.rgb_to_hsv(iR/255.0, iG/255.0, iB/255.0)
    return round(fHSV[0]*360, 3), round(fHSV[1]*100, 3), round(fHSV[2]*100, 3)


# Converted to Python from Obj-C, original source from:
# http://www.developers.meethue.com/documentation/color-conversions-rgb-xy
# pylint: disable=invalid-sequence-index
def color_xy_brightness_to_RGB(vX: float, vY: float,
                               ibrightness: int) -> Tuple[int, int, int]:
    """Convert from XYZ to RGB."""
    brightness = ibrightness / 255.
    if brightness == 0:
        return (0, 0, 0)

    Y = brightness

    if vY == 0:
        vY += 0.00000000001

    X = (Y / vY) * vX
    Z = (Y / vY) * (1 - vX - vY)

    # Convert to RGB using Wide RGB D65 conversion.
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    # Apply reverse gamma correction.
    r, g, b = map(
        lambda x: (12.92 * x) if (x <= 0.0031308) else
        ((1.0 + 0.055) * pow(x, (1.0 / 2.4)) - 0.055),
        [r, g, b]
    )

    # Bring all negative components to zero.
    r, g, b = map(lambda x: max(0, x), [r, g, b])

    # If one component is greater than 1, weight components by that value.
    max_component = max(r, g, b)
    if max_component > 1:
        r, g, b = map(lambda x: x / max_component, [r, g, b])

    ir, ig, ib = map(lambda x: int(x * 255), [r, g, b])

    return (ir, ig, ib)


def convert_rgb_xy(red,green,blue):
    red = pow((red + 0.055) / (1.0 + 0.055), 2.4) if red > 0.04045 else red / 12.92
    green = pow((green + 0.055) / (1.0 + 0.055), 2.4) if green > 0.04045 else green / 12.92
    blue = pow((blue + 0.055) / (1.0 + 0.055), 2.4) if blue > 0.04045 else blue / 12.92

#Convert the RGB values to XYZ using the Wide RGB D65 conversion formula The formulas used:
    X = red * 0.664511 + green * 0.154324 + blue * 0.162028
    Y = red * 0.283881 + green * 0.668433 + blue * 0.047685
    Z = red * 0.000088 + green * 0.072310 + blue * 0.986039

#Calculate the xy values from the XYZ values
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    return [x, y]

def convert_xy(x, y, bri): #needed for milight hub that don't work with xy values
    X = x
    Y = y
    Z = 1.0 - x - y

  # sRGB D65 conversion
    r =  X * 3.2406 - Y * 1.5372 - Z * 0.4986
    g = -X * 0.9689 + Y * 1.8758 + Z * 0.0415
    b =  X * 0.0557 - Y * 0.2040 + Z * 1.0570


    r = 12.92 * r if r <= 0.0031308 else (1.0 + 0.055) * pow(r, (1.0 / 2.4)) - 0.055
    g = 12.92 * g if g <= 0.0031308 else (1.0 + 0.055) * pow(g, (1.0 / 2.4)) - 0.055
    b = 12.92 * b if b <= 0.0031308 else (1.0 + 0.055) * pow(b, (1.0 / 2.4)) - 0.055

    if r > b and r > g:
    # red is biggest
        if r > 1:
            g = g / r
            b = b / r
            r = 1
    elif g > b and g > r:
    # green is biggest
        if g > 1:
            r = r / g
            b = b / g
            g = 1

    elif b > r and b > g:
    # blue is biggest
        if b > 1:
            r = r / b
            g = g / b
            b = 1

    r = 0 if r < 0 else r
    g = 0 if g < 0 else g
    b = 0 if b < 0 else b
    return [int(r * bri), int(g * bri), int(b * bri)]

def hsv_to_rgb(h, s, v):
    s = float(s / 254)
    v = float(v / 254)
    c=v*s
    x=c*(1-abs(((h/11850)%2)-1))
    m=v-c
    if h>=0 and h<10992:
        r=c
        g=x
        b=0
    elif h>=10992 and h<21845:
        r=x
        g=c
        b=0
    elif h>=21845 and h<32837:
        r = 0
        g = c
        b = x
    elif h>=32837 and h<43830:
        r = 0
        g = x
        b = c
    elif h>=43830 and h<54813:
        r = x
        g = 0
        b = c
    else:
        r = c
        g = 0
        b = x

    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return r, g, b


def color_temperature_mired_to_kelvin(mired_temperature):
    """Convert absolute mired shift to degrees kelvin."""
    return math.floor(1000000 / mired_temperature)


def color_temperature_kelvin_to_mired(kelvin_temperature):
    """Convert degrees kelvin to mired shift."""
    return math.floor(1000000 / kelvin_temperature)

