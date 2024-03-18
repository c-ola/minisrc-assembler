import argparse
import json
from dataclasses import dataclass

DIRECTIVES = [
    "ORG", ".org", "DB", ".db"
]

config_file = open("config.json")
config = None
if config_file is not None:
    config = json.load(config_file)
    print(config["instructions"])


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


INSTR_MAP = {}
if config is not None:
    for instr in config["instructions"]:
        INSTR_MAP[instr["name"]] = (instr["opcode"], instr["format"])


# initialize format map
FORMATS = {}
for format in config["formats"]:
    fields = []
    for field in format["fields"]:
        fields.append(Field(field["name"], field["msb"], field["lsb"]))
    FORMATS[format["name"]] = Format(format["name"], fields)


COND_MAP = {}
for cond in config["conditions"]:
    COND_MAP[cond["name"]] = cond["value"]


def convert_to_bits(instruction_text, line_num=0, tags=None):
    instruction = instruction_text.lower().replace(",", "").split()

    if len(instruction) == 0:
        raise ValueError("invalid instruction")

    opcode, format = INSTR_MAP[instruction[0]]
    instr_num = 0
    for field in FORMATS[format].fields:
        mask = ((1 << (field.msb + 1)) - (1 << field.lsb)) >> field.lsb
        match field.name:
            case "opcode":
                instr_num |= (opcode & mask) << field.lsb
            case "Ra":
                # could maybe add something to the config to show where register are in text format
                # first token that starts with 'r' is Ra
                for tok in instruction[1:]:
                    if tok.startswith('r'):
                        instr_num |= (int(tok.replace('r', '')) & mask) << field.lsb
                        break
            case "Rb":
                # either first inside parentheses or second token
                rb = None
                for tok in instruction[1:]:
                    if tok[0].isdigit() or tok[0] == '-':
                        rb = parse_base(tok)[1]
                        break
                if rb is None:
                    rb = instruction[2]
                instr_num |= (int(rb.replace('r', '')) & mask) << field.lsb
            case "Rc":
                rc = instruction[3]
                instr_num |= (int(rc.replace('r', '')) & mask) << field.lsb
            case "C":
                for tok in instruction[1:]:
                    res = parse_tag(tok, tags)
                    if tok[0].isdigit() or tok[0] == '-' or res is not None:
                        imm = 0
                        if res is not None:
                            imm = res - line_num
                        else:
                            imm = parse_base(tok)[0] if chr(40) in tok else pint(tok)

                        instr_num |= (imm & mask) << field.lsb
                        break
            case "condition":
                instr_num |= (COND_MAP[instruction[0]] & mask) << field.lsb
            case _:
                raise ValueError("invalid field in config")

    return instr_num


def parse_tag(val, tags):
    for tag in tags:
        if val == tag[0]:
            return tag[1]
    return None


def setup():
    parser = argparse.ArgumentParser("instrmaker")
    parser.add_argument('-s', "--file_in", type=str, help="The input file to convert into a binary file")
    parser.add_argument('-o', "--file_out", type=str, help="The output file where resulting binary will be placed")
    parser.add_argument('-e', "--example", action="store_true", default=False, help="Prints the example code and its machine code")
    parser.add_argument('-l', "--single", type=str, help="Used to compile a single instruction")
    args = parser.parse_args()
    return args


def convert_text_file(file_in, file_out):
    fin = open(file_in, "r", encoding="utf-8")

    lines = fin.readlines()
    out_lines = []
    tags = []
    line_num = 0
    orgs = []

    # remove comments
    i = 0
    while i < len(lines):
        if lines[i] == "\n":
            lines.pop(i)
            continue
        else:
            lines[i] = lines[i].split(";", 1)[0]
        i = i + 1

    # find all tags
    # tags represent the address of the instruction directly under them

    for line in lines:
        # remove comments
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

    # have to pass in the tags to know the offset from the line number for jump instructions
    # branch instructions can have their tags replaced directly
    # convert instructions
    # print(repr(tags))
    # print(repr(orgs))
    line_num = 0
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
        print(line_num, ': {:<30} : '.format(line[:len(line)-1]), f"{converted:#0{10}x}")
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
    return


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


if __name__ == "__main__":
    args = setup()

    if args.single is not None:
        convert_single(args.single)
    elif args.file_in is not None:
        convert_text_file(args.file_in, args.file_out)
    else:
        print("use -h to view options")
