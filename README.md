# minisrc-assembler
Assembler for mini-src instructions\
Made this for ELEC374 Digital Systems Engineering

Automatically outputs to hex

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
python3 minisrc-asm.py -e
```
```sh
python3 minisrc-asm.py -s tests/instructions.s -o tests/instructions.hex
```
