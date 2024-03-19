# minisrc-assembler
Customizable RISC Assembler.
Made this for ELEC374 Digital Systems Engineering

NOTE: Only outputs to hex

## Usage
```sh
python3 minisrc-asm.py -s <ASM_INPUT_FILE> -o <OUTPUT_FILE>
```
Note: If no output file name is specified, output will only be printed to terminal 

### Single Instruction
```sh
python3 minisrc-asm.py -l "ldi r4, 0x87(r3)"
```

### Example
```sh
python3 minisrc-asm.py -s tests/instructions.s -o tests/instructions.hex
```

### Instruction set Configuration
The configuration for can be (fully?) customized for any different instructions, opcodes, and binary formats.

To interpret a value in a field in a certain way, the field must have a certain string inside of it. The strings are:
- opcode: raw value
- R: as a register
- imm: as an immediate value

An example of a configuration is:
```json
{
    "name": "example",
    "word_size": "32",
    "textformats": [ // the fields must be in the order that they would be in assembly
        {
            "name": "one_reg",
            "fields": [ "opcode", "Ra" ]
        },
        {
            "name": "misc",
            "fields": [ "opcode" ]
        }
    ],
    "conditions": {
        [
            {
                "name": "branch",
                "value": 2 // value that will be placed in spot of condition for instruction with the above name
            }
        ]
    },
    "formats": [ // format for how values will be placed in each word,
        {
            "name": "M",
            "fields": [ // msb and lsb are the range for where the value will be
                {
                    "name": "opcode",
                    "msb": 31,
                    "lsb": 27,
                }
            ]
        },
        {
            "name": "B",
            "fields": [ // msb and lsb are the range for where the value will be
                {
                    "name": "opcode",
                    "msb": 31,
                    "lsb": 27,
                },
                {
                    "name": "condition",
                    "msb": 26,
                    "lsb": 25,
                }
            ]
        },
    ],
    "instruction": [ // list of instructions in the instruction set
        {
            "name": "nop",
            "opcode": 0,
            "format": "M"
        },
        {
            "name": branch,
            "opcode": 1,
            "format": "B"
        }
    ]

}
```
