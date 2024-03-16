import argparse

DIRECTIVES = [
    "ORG", ".org", "DB", ".db"
]

INSTRUCTIONS = [
    "ld", "ldi", "st", "add", "sub", "shr", "shra", "shl",
    "ror", "rol", "and", "or", "addi", "andi", "ori",
    "mul", "div", "neg", "not", "brzr", "brnz", "brmi", "brpl",
    "jr", "jal", "in", "out", "mfhi", "mflo", "nop", "halt"
]

INSTR_TO_OP = {}
for i in range(0, len(INSTRUCTIONS)):
    if i >= 0b10011 and i < 0b10011 + 4:
        INSTR_TO_OP[INSTRUCTIONS[i]] = 0b10011
    elif i >= 0b10011 + 4:
        INSTR_TO_OP[INSTRUCTIONS[i]] = i - 3
    else:
        INSTR_TO_OP[INSTRUCTIONS[i]] = i

BRANCH_TO_COND = {
    "brzr": 0b0000,
    "brnz": 0b0001,
    "brpl": 0b0010,
    "brmi": 0b0011,
}

REG_MAP = {}
for i in range(16):
    REG_MAP["r" + str(i)] = i


def convert_to_bits(instruction_text, line_num=0, tags=None):
    instruction = instruction_text.lower().replace(",", "").split()

    if len(instruction) == 0:
        raise ValueError("invalid instruction")

    opcode, ra, rb, rc, c2, c_imm = 0, 0, 0, 0, 0, 0

    opcode = INSTR_TO_OP[instruction[0]]
    if len(instruction) >= 2:
        if instruction[0] == "st":
            ra = REG_MAP[instruction[2]]
        elif instruction[0] != "halt" and instruction[0] != "stop":
            ra = REG_MAP[instruction[1]]

    # need revision for signed
    match instruction[0]:
        case "ld" | "ldi":
            parsed = parse_base(instruction[2])
            rb = REG_MAP[parsed[1]]
            c_imm = parsed[0]
        case "st":
            parsed = parse_base(instruction[1])
            rb = REG_MAP[parsed[1]]
            c_imm = parsed[0]
        case "add" | "sub" | "shr" | "shra" | "shl" | "ror" | "rol" | "and" | "or":
            ra = REG_MAP[instruction[1]]
            rb = REG_MAP[instruction[2]]
            rc = REG_MAP[instruction[3]]
        case "addi" | "andi" | "ori":
            ra = REG_MAP[instruction[1]]
            rb = REG_MAP[instruction[2]]
            c_imm = pint(instruction[3])
        case "mul" | "div" | "neg" | "not":
            ra = REG_MAP[instruction[1]]
            rb = REG_MAP[instruction[2]]
        case "brzr" | "brnz" | "brmi" | "brpl":
            ra = REG_MAP[instruction[1]]
            c2 = BRANCH_TO_COND[instruction[0]]
            res = parse_tag(instruction[2], tags)
            if res is not None:
                c_imm = res
            else:
                c_imm = pint(instruction[2])
        case "jr" | "jal" | "in" | "out" | "mfhi" | "mflo":
            ra = REG_MAP[instruction[1]]
        case "nop" | "halt":
            pass
        case _:
            raise ValueError("invalid instruction")

    instr_numerical = 0
    match instruction[0]:
        case "ld" | "ldi" | "st":
            instr_numerical = (opcode << 27) + (ra << 23) + (rb << 19) + (c_imm & 0x7ffff)
        case "add" | "sub" | "shr" | "shra" | "shl" | "ror" | "rol" | "and" | "or":
            instr_numerical = (opcode << 27) + (ra << 23) + (rb << 19) + (rc << 15)
        case "addi" | "andi" | "ori":
            instr_numerical = (opcode << 27) + (ra << 23) + (rb << 19) + (c_imm & 0x7ffff)
        case "mul" | "div" | "neg" | "not":
            instr_numerical = (opcode << 27) + (ra << 23) + (rb << 19)
        case "brzr" | "brnz" | "brmi" | "brpl":
            instr_numerical = (opcode << 27) + (ra << 23) + (c2 << 19) + (c_imm & 0x7ffff)
        case "jr" | "jal" | "in" | "out" | "mfhi" | "mflo":
            instr_numerical = (opcode << 27) + (ra << 23)
        case "nop" | "halt":
            instr_numerical = (opcode << 27)
        case _:
            instr_numerical = 0

    return instr_numerical


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
    fin = open(file_in, "r")
    out = file_out is not None

    if out:
        fout = open(file_out, "w")

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
    line_num = 0
    # print(repr(tags))
    # print(repr(orgs))
    found_org = False
    for line in lines:
        if ':' in line:
            continue
        for org in orgs:
            if line_num == org[0]:
                found_org = True
                line_num = org[1] + 1
                break
        if found_org:
            found_org = False
            continue
        converted = convert_to_bits(line, line_num, tags)
        out_lines.append(f"{converted:#0{10}x}"[2:])
        print(line_num, ': {:<30} : '.format(line[:len(line)-1]), f"{converted:#0{10}x}")
        if out:
            fout.write(f"{converted:#0{10}x}"[2:] + "\n")
        line_num = line_num + 1
    if out:
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
    if ("(" not in arg):
        return pint(arg), "r0"
    s = arg[0:len(arg)-1].split("(")
    return pint(s[0]), s[1]


def example():
    instructions_example = [
        "ld r2, 0x95",
        "ld r0, 0x38(R2)",
        "ldi r2, 0x95",
        "ldi r0, 0x38(r2)",
        "ldi r1, 0xf",
        "st 0x87, r1",
        "st 0x87(r1), r1",
        "addi r3, r4, -5",
        "andi r3, r4, 0x53",
        "ori r3, r4, 0x53",
        "ldi r5, 0x5",
        "brzr R5, 14",
        "brnz r5, 14",
        "brpl r5, 14",
        "brmi r5, 14",
        "nop",
        "halt",
        "ldi r3, 0xfffa",
        "out r3",
        "in r4",
        "mul r3, r4",
        "mfhi r6",
        "mflo r7",
        "jr R6",
        "jal r6"
    ]
    for instr in instructions_example:
        converted = convert_to_bits(instr)
        print('{:<20} : '.format(instr), f"{converted:#0{10}x}")


if __name__ == "__main__":
    args = setup()
    
    if args.example:
        example()
    elif args.single is not None:
        convert_single(args.single)
    else:
        convert_text_file(args.file_in, args.file_out)
