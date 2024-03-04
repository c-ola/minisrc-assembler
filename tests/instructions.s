ld r2, 0x95
ld r0, 0x38(r2)
ldi r2, 0x95
ldi r0, 0x38(r2)
st 0x87, r1
st 0x87(r1), r1
addi r3, r4, -5
andi r3, r4, 0x53
ori r3, r4, 0x53
brzr r5, 14
brnz r5, 14
brpl r5, 14
brmi r5, 14
jr r6
jal r6
mfhi r6
mflo r7
out r3
in r4
