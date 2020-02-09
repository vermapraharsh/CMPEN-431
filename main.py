import sys
import pdb
import logging

from project2 import scheduler

def main (args):

    if len(args) != 3:
        print ("Error: Not enough arguments!")
        print ("Usage: python main.py input_file output_file")
        sys.exit(1)

    infilename = args[1]
    outfilename = args[2]

    logging.basicConfig(level=logging.INFO, format='[%(filename)18s:%(lineno)-4d] %(levelname)-5s:  %(message)s')

    logging.getLogger().setLevel(logging.DEBUG)

    ooo = scheduler(infilename, outfilename)
    ooo.schedule()
    ooo.generate_output_file()


if __name__ == "__main__":
    main(sys.argv)
