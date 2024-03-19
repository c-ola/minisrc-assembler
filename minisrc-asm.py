import argparse
import json
from dataclasses import dataclass
from default_config import minisrc


DIRECTIVES = [
    "ORG", ".org", "DB", ".db"
]

# globals

config = None
INSTR_MAP = {}
FORMATS = {}
COND_MAP = {}
TEXTFORMATS = {}


class Assembler:
    config = None

# instruction config parseing
def init_config():
    if config is None:
        raise ValueError("No instruction configuration setup")

    instr_map = {}
    for instr in config["instructions"]:
        instr_map[instr["name"]] = (instr["opcode"], instr["format"], instr["textformat"])

    # initialize format map
    formats = {}
    for format in config["formats"]:
        fields = []
        for field in format["fields"]:
            fields.append(Field(field["name"], field["msb"], field["lsb"]))
        formats[format["name"]] = Format(format["name"], fields)

    cond_map = {}
    for cond in config["conditions"]:
        cond_map[cond["name"]] = cond["value"]

    textformat = {}
    for tf in config["textformats"]:
        textformat[tf["name"]] = Format(tf["name"], tf["fields"])

    return instr_map, formats, cond_map, textformat


@dataclass
class Instruction:
    name: str
    opcode: int
    format: str


@dataclass
class Field:
    name: str
    msb: int
    lsb: int

    def __init__(self, name: str, msb: int, lsb: int):
        self.name = name
        self.msb = msb
        self.lsb = lsb


@dataclass
class Format:
    name: str
    fields: []

    def __init__(self, name: str, fields: []):
        self.name = name
        self.fields = fields


# Assembling
# should have identifiers like op = opcode, RegA = Ra, ImmValC = c
# this would make it so that you have to prefix your fields in the config
# but it would also allow for complete freedom in what instructions you can make
def convert_to_bits(instruction_text, line_num=0, tags=None):
    instruction = instruction_text.lower().replace(",", "").split()

    if len(instruction) == 0:
        raise ValueError("invalid instruction")

    opcode, format, textformat = INSTR_MAP[instruction[0]]
    instr_num = 0
    tf_fields = TEXTFORMATS[textformat].fields
    for field in FORMATS[format].fields:
        mask = ((1 << (field.msb + 1)) - (1 << field.lsb)) >> field.lsb
        # gets the index of the binary field in the text instruction field
        index = None
        for i in range(len(TEXTFORMATS[textformat].fields)):
            textfield = TEXTFORMATS[textformat].fields[i]
            if field.name in textfield:
                index = i

        # no index found, just go next or do branch condition
        if index is None:
            if "condition" == field.name:
                instr_num |= (COND_MAP[instruction[0]] & mask) << field.lsb
            continue

        token = instruction[index]
        if "op" in field.name:
            instr_num |= (opcode & mask) << field.lsb
        elif 'R' in field.name and 'imm' not in tf_fields[index]:
            reg = instruction[index]
            instr_num |= (int(reg.replace('r', '')) & mask) << field.lsb
        elif 'R' in field.name and 'imm' in tf_fields[index]:
            reg = parse_base(instruction[index])[1]
            instr_num |= (int(reg.replace('r', '')) & mask) << field.lsb
        elif 'imm' in field.name:
            res = parse_tag(token, tags)
            if res is not None:
                imm = res - line_num
            else:
                imm = parse_base(token)[0] if chr(40) in token else pint(token)
            instr_num |= (imm & mask) << field.lsb
        else:
            raise ValueError("invalid field in config")

    return instr_num


def parse_tag(val, tags):
    if tags is None:
        return None
    for tag in tags:
        if val == tag[0]:
            return tag[1]
    return None


def find_orgs_and_tags(lines):
    orgs = []
    tags = []
    line_num = 0
    # find all tags
    # tags represent the address of the instruction directly under them
    # put in own function
    for line in lines:
        # removes comments
        for directive in DIRECTIVES:
            if directive in line:
                toks = line.split()
                if toks[0] == "ORG":
                    orgs.append((line_num, pint(toks[1])))
                    line_num = line_num - 1

        if ':' in line:
            if line.replace("\n", "")[-1] == ':':
                tags.append((line[:len(line)-2], line_num))
            else:
                raise ValueError("Invalid Syntax at line: ", line_num, "near: ", line)
        else:  # only increase line number on lines with actual instructions
            line_num = line_num + 1
    return orgs, tags


def remove_comments(lines):
    # remove comments
    i = 0
    while i < len(lines):
        if lines[i] == "\n":
            lines.pop(i)
            continue
        else:
            lines[i] = lines[i].split(";", 1)[0]
        i = i + 1


def convert_text_file(file_in, file_out):
    fin = open(file_in, "r", encoding="utf-8")

    lines = fin.readlines()
    remove_comments(lines)
    orgs, tags = find_orgs_and_tags(lines)

    # branch instructions can have their tags replaced directly
    # convert instructions
    line_num = 0
    out_lines = []
    found_org = False
    for line in lines:
        if ':' in line:
            continue
        for org in orgs:
            if line_num == org[0]:
                found_org = True
                line_num = org[1]
                break
        if found_org:
            found_org = False
            orgs.pop(0)
            continue
        converted = convert_to_bits(line, line_num, tags)

        out_lines.append((line_num, f"{converted:#0{10}x}"[2:]))
        print(f"{line_num:#0{4}x}:", ': {:<30} : '.format(line[:len(line)-1]), f"{converted:#0{10}x}")
        line_num = line_num + 1

    out = file_out is not None
    if out:
        fout = open(file_out, "w", encoding="utf-8")
        i = 0
        for line in out_lines:
            while i < line[0]:
                fout.write("00000000\n")
                i = i + 1
            fout.write(line[1] + "\n")
            i = i + 1

        fout.close()
    fin.close()
    return


def convert_single(instruction):
    converted = convert_to_bits(instruction)
    print('{:<20} : '.format(instruction[:len(instruction)]), f"{converted:#0{10}x}")


def pint(num_str):
    if num_str.startswith("0x"):
        return int(num_str, 16)
    elif num_str.startswith("0b"):
        return int(num_str, 2)
    return int(num_str, 10)


def parse_base(arg):
    if (chr(40) not in arg):
        return pint(arg), "r0"
    s = arg[0:len(arg)-1].split(chr(40))  # fmt bugs out from left brkt
    return (pint(s[0]), s[1])


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
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = setup()

    if args.instr_config is not None:
        f = open(args.instr_config)
        config = json.load(f)
        print(config)
        f.close()
    else:
        config = minisrc
    INSTR_MAP, FORMATS, COND_MAP, TEXTFORMATS = init_config()

    if args.single is not None:
        convert_single(args.single)
    elif args.file_in is not None:
        convert_text_file(args.file_in, args.file_out)
    else:
        print("use -h to view options")
