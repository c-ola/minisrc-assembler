from config import Config


DIRECTIVES = [
    "ORG", ".org", "DB", ".db"
]


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


def parse_tag(val, tags):
    if tags is None:
        return None
    for tag in tags:
        if val == tag[0]:
            return tag[1]
    return None


class Assembler:
    config: Config
    mode: str  # can be binary, binnum, hex
    orgs: list
    tags: list
    verbose: bool

    def __init__(self, config, mode="binary", verbose=False):
        self.config = config
        self.orgs = []
        self.tags = []
        self.mode = mode
        self.verbose = verbose

    def convert_to_bits(self, instruction_text, line_num=0):
        instruction = instruction_text.lower().replace(",", "").split()

        if len(instruction) == 0:
            raise ValueError("invalid instruction")

        opcode, format, textformat = self.config.instr_map[instruction[0]]
        instr_num = 0
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
                    instr_num |= (self.config.cond_map[instruction[0]] & mask) << field.lsb
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
                res = parse_tag(token, self.tags)
                if res is not None:
                    imm = res - line_num
                else:
                    imm = parse_base(token)[0] if chr(40) in token else pint(token)
                instr_num |= (imm & mask) << field.lsb
            else:
                raise ValueError("invalid field in config")

        return instr_num

    def convert_single(self, instr):
        num = self.convert_to_bits(instr)
        if self.mode == "binnum":
            print('{:<20} : '.format(instr[:len(instr)]), f"{num:#0{34}b}")
        elif self.mode == "hex":
            print('{:<20} : '.format(instr[:len(instr)]), f"{num:#0{10}x}")
        else:
            print('{:<20} : '.format(instr[:len(instr)]), f"{num:#0{10}x}")

    def find_orgs_and_tags(self, lines):
        line_num = 0
        # find all self.tags
        # self.tags represent the address of the instruction directly under them
        # put in own function
        for line in lines:
            # removes comments
            for directive in DIRECTIVES:
                if directive in line:
                    toks = line.split()
                    if toks[0] == "ORG":
                        self.orgs.append((line_num, pint(toks[1])))
                        line_num = line_num - 1

            if ':' in line:
                if line.replace("\n", "")[-1] == ':':
                    self.tags.append((line[:len(line)-2], line_num))
                else:
                    raise ValueError("Invalid Syntax at line: ", line_num, "near: ", line)
            else:  # only increase line number on lines with actual instruction
                line_num = line_num + 1

    def remove_comments(self, lines):
        # remove comments
        i = 0
        while i < len(lines):
            if lines[i] == "\n":
                lines.pop(i)
                continue
            else:
                lines[i] = lines[i].split(";", 1)[0]
            i = i + 1

    def convert_text_file(self, file_in, file_out):
        fin = open(file_in, "r", encoding="utf-8")
        lines = fin.readlines()
        fin.close()

        self.remove_comments(lines)
        self.find_orgs_and_tags(lines)

        # branch instructions can have their self.tags replaced directly
        # convert instructions
        line_num = 0
        out_lines = []
        found_org = False
        for line in lines:
            if ':' in line:
                continue
            for org in self.orgs:
                if line_num == org[0]:
                    found_org = True
                    line_num = org[1]
                    break
            if found_org:
                found_org = False
                self.orgs.pop(0)
                continue
            converted = self.convert_to_bits(line, line_num)

            out_lines.append((line_num, converted))

            if self.verbose:
                print(f"{line_num:#0{4}x}:", ': {:<30} : '
                      .format(line[:len(line)-1]),
                      f"{converted:#0{10}x}")

            line_num = line_num + 1

        if file_out:
            self.write_lines(out_lines, file_out)

    def write_lines(self, lines, filename):
        if self.mode == "binary":
            fout = open(filename, "wb")
            i = 0
            for line in lines:
                while i < line[0]:
                    fout.write(b'\x00\x00\x00\x00')
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
