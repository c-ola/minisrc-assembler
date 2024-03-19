from dataclasses import dataclass
from configs.default import minisrc
import json
import yaml


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


class Config:
    instr_map = {}
    formats = {}
    cond_map = {}
    textformats = {}

    # instruction config parseing
    def __init__(self, filename=None, useyaml=False):
        config = minisrc
        if filename is not None:
            if filename.endswith("yaml") | filename.endswith("yml") | useyaml:
                try:
                    f = open(filename, 'r')
                    config = yaml.safe_load(f)
                    f.close()
                except yaml.YAMLError as exc:
                    print("Error in yaml config file: ", exc)
                    if hasattr(exc, 'problem_mark'):
                        if exc.context is not None:
                            print('  parser says\n' + str(exc.problem_mark))
                            print('   '+str(exc.problem)+' '+str(exc.context))
                            print("Please correct data and retry")
                        else:
                            print('  parser says\n' + str(exc.problem_mark))
                            print('   '+str(exc.problem))
                            print("Please correct data and retry")
                    else:
                        print("Something went wrong while parsing yaml file")

            elif filename.endswith("json") | True:
                f = open(filename)
                config = json.load(f)
                f.close()

        for instr in config["instructions"]:
            self.instr_map[instr["name"]] = (instr["opcode"], instr["format"],
                                             instr["textformat"])

        # initialize format map
        for format in config["formats"]:
            fields = []
            for field in format["fields"]:
                fields.append(Field(field["name"], field["msb"], field["lsb"]))
            self.formats[format["name"]] = Format(format["name"], fields)

        for cond in config["conditions"]:
            self.cond_map[cond["name"]] = cond["value"]

        for tf in config["textformats"]:
            self.textformats[tf["name"]] = Format(tf["name"], tf["fields"])
