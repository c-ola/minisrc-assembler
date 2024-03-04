import argparse

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


def convert_to_bits(instruction_text):
    instruction = instruction_text.lower().replace(",", "").split()

    if len(instruction) == 0:
        raise ValueError("invalid instruction")

    opcode, ra, rb, rc, c2, c_imm = 0, 0, 0, 0, 0, 0

    opcode = INSTR_TO_OP[instruction[0]]
    if len(instruction) >= 2:
        if instruction[0] == "st":
            ra = REG_MAP[instruction[2]]
        else:
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


def setup():
    parser = argparse.ArgumentParser("instrmaker")
    parser.add_argument('-f', "--file_in", type=str, help="The input file to convert into a binary file")
    parser.add_argument('-o', "--file_out", type=str, help="The output file where resulting binary will be placed")
    parser.add_argument('-e', "--example", action="store_true", default=False, help="Prints the example code and its assembled machine code")
    args = parser.parse_args()
    return args


def convert_text_file(file_in, file_out):
    fin = open(file_in, "r")
    out = file_out is not None

    if out:
        fout = open(file_out, "w")

    for line in fin.readlines():
        converted = convert_to_bits(line)
        print('{:<20} : '.format(line[:len(line)-1]), f"{converted:#0{10}x}")
        if out:
            fout.write(f"{converted:#0{10}x}"[2:] + "\n")

    if out:
        fout.close()
    fin.close()
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
        "ldi r3, 0x95",
        "ldi r6, 0x95",
        "mul r3, r6",
        "jr R6",
        "jal r6",
        "mfhi r6",
        "mflo r7",
        "out r3",
        "in r4"
    ]
    for instr in instructions_example:
        converted = convert_to_bits(instr)
        print('{:<20} : '.format(instr), f"{converted:#0{10}x}")


if __name__ == "__main__":
    args = setup()

    if args.example:
        example()
    else:
        convert_text_file(args.file_in, args.file_out)
