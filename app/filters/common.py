"""
Common Filters available to templates
"""

def format_time(input):
    # Convert seconds to xxd xxh xxm (IE: 02d 02h 33m)
    try:
        min, sec = divmod(input, 60)
        hour, min = divmod(min, 60)
        day, hour = divmod(hour, 24)
        ret = "{:02d}m".format(min)
        if hour:
            ret = "{:02d}h {}".format(hour, ret)
        if day:
            ret = "{:02d}d {}".format(day, ret)
        return ret
    except:
        return "#error"


def format_hours(input):
    # Convert seconds to hours (IE: 6.09)
    try:
        return "{:02.02f}".format(input / 60 / 60)
    except:
        return "#error"

def format_currency(input):
    # TODO Locale update
    # Convert from cents to dollars
    try:
        return "${:,.2f}".format(input/100)
    except:
        return "#error"


def pick_color(input):
    # Pick a color based on the index provided
    COLORS = [
        "#ef5350",
        "#ec407a",
        "#ab47bc",
        "#7e57c2",
        "#5c6bc0",
        "#42a5f5",
        "#29b6f6",
        "#26c6da",
        "#26a69a",
        "#66bb6a",
        "#9ccc65",
        "#d4e157",
        "#ffee58",
        "#ffca28",
        "#ffa726",
        "#ff7043",
        "#8d6e63",
        "#bdbdbd",
        "#78909c",
    ]

    try:
        return COLORS[int(input) % len(COLORS)]
    except ValueError:
        return "#CCCCCC"
