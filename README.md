# minisrc-assembler
Customizable RISC Assembler.
Made this for ELEC374 Digital Systems Engineering

NOTE: Only outputs to hex

## Usage
Flag `-x` (`--hex`) makes the numbers output in hexadecimal to the file in utf-8.
`-b` makes it output binary in utf-8.
No flag (default) will cause it to write to the file as binary (no encoding)
```sh
python3 minisrc-asm.py -s <ASM_INPUT_FILE> -o <OUTPUT_FILE>
```
Note: If no output file name is specified, output will only be printed to terminal 

### Single Instruction
```sh
python3 minisrc-asm.py -l "ldi r4, 0x87(r3)"
```

### Example
`-v` will cause the program to print out each instruction as and its converted format in hex
```sh
python3 minisrc-asm.py -v -s tests/instructions.s -o tests/instructions.hex
```

### Instruction set Configuration
The configuration for can be (fully?) customized for any different instructions, opcodes, and binary formats.

To interpret a value in a field in a certain way, the field must have a certain string inside of it. The strings are:
- opcode: raw value
- R: as a register
- imm: as an immediate value

An example of a configuration is:
```yaml
---
name: example
word_size: 32
textformats: # the fields must be in the order that they would be in assembly
    - name: one_reg
      fields: [opcode, Ra]
    - name: misc
      fields: [opcode]
conditions:
    - name: branch
      value: 2 # value that will be placed in spot of condition for instruction with the above name
formats: # format for how values will be placed in each word
    - name: M
      fields:  # msb and lsb are the range for where the value will be
        - { name: opcode, msb: 31, lsb: 28 }
    - name: B
      fields: 
        - { name: opcode, msb: 31, lsb: 28 }
        - { name: condition, msb: 19, lsb: 16 }
        - { name: Ra, msb: 3, lsb: 0 } 
instructions:  # list of instructions in the instruction sete
  - { name: nop, opcode: 13, format: M, textformat: misc }
  - { name: branch, opcode: 4, format: B, textformat: one_reg }
```

Running with this configurations gives
```sh
python3 minisrc-asm.py -c examples/example.yaml --use-yaml -l "branch r5"
branch r5            :  0x40020005
python3 minisrc-asm.py -c examples/example.yaml --use-yaml -l "branch r5"
nop                  :  0xd0000000
```

This can also be done in json although it is a little longer:
```json
{
    "name": "example",
    "word_size": "32",
    "textformats": [
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
                "value": 2
            }
        ]
    },
    "formats": [
        {
            "name": "M",
            "fields": [
                {
                    "name": "opcode",
                    "msb": 31,
                    "lsb": 28,
                }
            ]
        },
        {
            "name": "B",
            "fields": [
                {
                    "name": "opcode",
                    "msb": 31,
                    "lsb": 28,
                },
                {
                    "name": "condition",
                    "msb": 19,
                    "lsb": 16,
                },
                {
                    "name": "Ra",
                    "msb": 3,
                    "lsb": 0
                }
            ]
        },
    ],
    "instruction": [
        {
            "name": "nop",
            "opcode": 13,
            "format": "M"
        },
        {
            "name": branch,
            "opcode": 4,
            "format": "B"
        }
    ]
}
```
