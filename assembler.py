from config import Config

DIRECTIVES = ["ORG", ".org", "DB", ".db"]


class Token:
    def __init__(self, t_type, value, line_num=None):
        self.t_type = t_type
        self.value = value
        self.line_num = line_num

    def __repr__(self):
        return f"Token({self.t_type}, {self.value}, {self.line_num})"


class Tokenizer:
    def __init__(self):
        self.tokens = []
        self.comments = []

    def parse_tokens(self, file_name=None, text=""):
        if file_name is not None:
            f = open(file_name, "r", encoding="utf-8")
            instructions = f.readlines()
            f.close()
        else:
            instructions = text

        # prepare instructions
        for i, line in enumerate(instructions):
            pline = line.strip(",").split(";", 1)
            if len(pline) > 1:
                comment = (pline[1].strip("\n"), i)
                self.comments.append(comment)

            unparsed_tokens = pline[0].split()
            instruction = []
            for word in unparsed_tokens:
                t_type = "name"
                value = word.strip(",")
                line_num = i
                if word in DIRECTIVES:
                    t_type = "directive"
                elif (num := parse_int(word)) is not None:
                    t_type = "immediate"
                elif "(" in word and ")" in word:
                    t_type = "reg"
                elif ":" in word:
                    t_type = "tag"
                    value = value.strip(':')
                instruction.append(Token(t_type, value, line_num))
            if instruction:
                self.tokens.append(instruction)
        return self.tokens, self.comments


def parse_int(num_str):
    base = 10
    result = None
    if num_str.startswith("0x"):
        base = 16
        num_str = num_str.split("0x")[1]
    elif num_str.startswith("0b"):
        base = 2
        num_str = num_str.split("0b")[1]

    try:
        result = int(num_str, base)
    except ValueError:
        result = None
    return result


def pint(num_str):
    base = 10
    if num_str.startswith("0x"):
        return int(num_str, 16)
    elif num_str.startswith("0b"):
        return int(num_str, 2)
    return int(num_str, 10)


def parse_base(arg):
    if chr(40) not in arg:
        return pint(arg), "r0"
    s = arg[0 : len(arg) - 1].split(chr(40))  # fmt bugs out from left brkt
    return (pint(s[0]), s[1])


class Assembler:
    config: Config
    mode: str  # can be binary, binnum, hex
    orgs: list
    tags: dict
    verbose: bool

    def __init__(self, config, mode="binary", verbose=False):
        self.config = config
        self.orgs = []
        self.tags = {}
        self.mode = mode
        self.verbose = verbose

    def convert_single(self, instr):
        instructions, comments = Tokenizer().parse_tokens(text=instr)
        num = self.get_instr_bin(instructions[0])
        if self.mode == "binnum":
            print("{:<20} : ".format(instr[: len(instr)]), f"{num:#0{34}b}")
        elif self.mode == "hex":
            print("{:<20} : ".format(instr[: len(instr)]), f"{num:#0{10}x}")
        else:
            print("{:<20} : ".format(instr[: len(instr)]), f"{num:#0{10}x}")

    def get_instr_bin(self, instruction):
        instr_num = 0
        opcode, format, textformat = self.config.instr_map[instruction[0].value]
        tf_fields = self.config.textformats[textformat].fields
        for field in self.config.formats[format].fields:
            mask = ((1 << (field.msb + 1)) - (1 << field.lsb)) >> field.lsb
            # gets the index of the binary field in the text instruction field
            index = None
            for i in range(len(self.config.textformats[textformat].fields)):
                textfield = self.config.textformats[textformat].fields[i]
                if field.name in textfield:
                    index = i

            # no index found, just go next or do branch condition
            if index is None:
                if "condition" == field.name:
                    instr_num |= (
                        self.config.cond_map[instruction[0].value] & mask
                    ) << field.lsb
                continue

            token = instruction[index].value.lower()
            if "op" in field.name:
                instr_num |= (opcode & mask) << field.lsb
            elif "R" in field.name and "imm" not in tf_fields[index]:
                reg = token
                instr_num |= (int(reg.replace("r", "")) & mask) << field.lsb
            elif "R" in field.name and "imm" in tf_fields[index]:
                reg = parse_base(token)[1]
                instr_num |= (int(reg.replace("r", "")) & mask) << field.lsb
            elif "imm" in field.name:
                if (res := self.tags.get(token)) is not None:
                    imm = res - instruction[0].line_num
                else:
                    imm = parse_base(token)[0] if chr(40) in token else pint(token)
                instr_num |= (imm & mask) << field.lsb
            else:
                raise ValueError("invalid field in config")
        return instr_num

    def convert_text_file(self, file_in, file_out):
        instructions, comments = Tokenizer().parse_tokens(file_in)
        address = 0

        asm_instructions = []
        for instruction in instructions:
            match instruction[0].t_type:
                case "directive":
                    org = parse_int(instruction[1].value)
                    address = org
                    print(instruction[1])
                    if org is None:
                        raise ValueError("Invalid org value")
                case "name":
                    asm_instructions.append((address, instruction))
                    address = address + 1
                case "tag":
                    self.tags[instruction[0].value] = address + 1

        instructions_binary = []
        for addr, instruction in asm_instructions:
            instr_num = self.get_instr_bin(instruction)
            instructions_binary.append(instr_num)
            instr_str = ""
            for instr in instruction:
                instr_str += instr.value + ' '
            if self.verbose:
                  print(f"{addr:#0{4}x}:", ': {:<30} : '
                      .format(instr_str),
                      f"{instr_num:#0{10}x}")

        if file_out:
            self.write_lines(instructions_binary, file_out)

    def write_lines(self, lines, filename):
        if self.mode == "binary":
            fout = open(filename, "wb")
            i = 0
            for line in lines:
                while i < line[0]:
                    fout.write(b"\x00\x00\x00\x00")
                    i = i + 1
                fout.write(line[1].to_bytes(4, signed=False))
                i = i + 1
            fout.close()
        else:
            fout = open(filename, "w", encoding="utf-8")
            i = 0
            for line in lines:
                while i < line[0]:
                    if self.mode == "binnum":
                        fout.write(f"{0:0{32}b}\n")
                    elif self.mode == "hex":
                        fout.write(f"{00000000:0{8}x}\n")
                    i = i + 1

                if self.mode == "binnum":
                    fout.write(f"{line[1]:0{32}b}\n")
                elif self.mode == "hex":
                    fout.write(f"{line[1]:0{8}x}\n")
                i = i + 1
            fout.close()
