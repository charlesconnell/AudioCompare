import sys


def die(msg):
    print("ERROR: {e}".format(e=msg), file=sys.stderr)
    exit(1)


def warn(msg):
    print("ERROR: {e}".format(e=msg), file=sys.stderr)
