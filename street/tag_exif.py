# source and modified https://gist.github.com/bryanibit/8cba7cd171ac1d93eec15b9ed6b57fbc

import os
from PIL import Image
import piexif
import piexif.helper
from fractions import Fraction


# piexif.GPSIFD.GPSLatitudeRef = 'S' if lat < 0 else 'N'
# piexif.GPSIFD.GPSLatitude = piexif.helper.degToDmsRational(lat)
# piexif.GPSIFD.GPSLongitudeRef = 'W' if lng < 0 else 'E'
# piexif.TagValues.GPSIFD.GPSLongitude = piexif.GPSHelper.degToDmsRational(lng)

# exif_dict = {"0th":zeroth_ifd, "Exif":exif_ifd, "GPS":gps_ifd, "1st":first_ifd, "thumbnail":thumbnail}

def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple

    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    min = int(t1)
    sec = round((t1 - min)* 60, 5)
    return (deg, min, sec, loc_value)


def change_to_rational(number):
    """convert a number to rantional

    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def set_gps_location(file_name, tstamp, lat, lng, altitude):
    """Adds GPS position as EXIF metadata

    Keyword arguments:
    file_name -- image file
    lat -- latitude (as float)
    lng -- longitude (as float)
    altitude -- altitude (as float)

    """
    im = Image.open(file_name)
    width, height = im.size

    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(lng, ["W", "E"])

    exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
    exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

    zeroth_ifd = {piexif.ImageIFD.Make: u"Go Pro HERO8 Black-GPS5",
        piexif.ImageIFD.XResolution: (width, 1),
        piexif.ImageIFD.YResolution: (height, 1),
        piexif.ImageIFD.Software: u"pLitter"
    }
    
    # exif_ifd = {piexif.ExifIFD.DateTimeOriginal: u"2099:09:29 10:10:10",
    #         piexif.ExifIFD.LensMake: u"LensMake",
    #         piexif.ExifIFD.Sharpness: 65535,
    #         piexif.ExifIFD.LensSpecification: ((1, 1), (1, 1), (1, 1), (1, 1)),
    #         }

    A_ref = 1 if altitude < 0 else 0
    altitude = abs(altitude)
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSAltitudeRef: A_ref,
        piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude)),
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: exiv_lat,
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: exiv_lng,
        piexif.GPSIFD.GPSDateStamp: tstamp,
    }

    first_ifd = {piexif.ImageIFD.Make: u"Go Pro HERO8 Black-GPS5",
        piexif.ImageIFD.XResolution: (width, 1),
        piexif.ImageIFD.YResolution: (height, 1),
        piexif.ImageIFD.Software: u"pLitter"
    }



    exif_dict = {"0th":zeroth_ifd, "GPS":gps_ifd, "1st":first_ifd,}
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, file_name)