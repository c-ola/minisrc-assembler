import argparse
from config import Config
from assembler import Assembler


def setup():
    parser = argparse.ArgumentParser("instrmaker")
    parser.add_argument('-s', "--file_in", type=str,
                        help="The input file to convert into a binary file")
    parser.add_argument('-o', "--file_out", type=str,
                        help="The output file of the resulting binary")
    parser.add_argument('-c', "--instr_config", type=str,
                        help="The configuration for the instructions")
    parser.add_argument('-l', "--single", type=str,
                        help="Used to compile a single instruction")
    parser.add_argument('-b', "--bin", action="store_true",
                        help="Used to compile to binary instead of hex")
    parser.add_argument('-x', "--hex", action="store_true",
                        help="Used to compile to hex")
    parser.add_argument('-v', "--verbose", action="store_true",
                        help="Show outputs when reading file")
    parser.add_argument("-y", "--use-yaml", action="store_true",
                        help="Use yaml as your configuration file")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = setup()
    config = Config(args.instr_config, useyaml=args.use_yaml)

    mode = "binary"
    if args.hex:
        mode = "hex"
    elif args.bin:
        mode = "binnum"
    assembler = Assembler(config, mode, args.verbose)

    if args.single is not None:
        assembler.convert_single(args.single)
    elif args.file_in is not None:
        assembler.convert_text_file(args.file_in, args.file_out)
    else:
        print("use -h to view options")
