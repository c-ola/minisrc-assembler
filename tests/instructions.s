ORG 0
    ldi R2, 0x69 ; R2 = 0x69
    ldi R2, 2(R2) ; R2 = 0x6B
    ld R1, 0x47 ; R1 = (0x47) = 0x94
    ldi R1, 1(R1) ; R1 = 0x95
    ld R0, -7(R1) ; R0 = (0x8E) = 0x34
    ldi R3, 3 ; R3 = 3
    ldi R2, 0x43 ; R2 = 0x43
    brmi R2, 3 ; continue with the next instruction (will not branch)
    ldi R2, 6(R2) ; R2 = 0x49
    ld R7, -2(R2) ; R7 = (0x49 - 2) = 0x94
    nop
    brpl R7, target ; continue with the instruction at “target” (will branch)
    ldi R5, 4(R2) ; this instruction will not execute
    ldi R4, -3(R5) ; this instruction will not execute

target:
    add R2, R2, R3 ; R2 = 0x4C
    addi R7, R7, 3 ; R7 = 0x97
    neg R7, R7 ; R7 = 0xFFFFFF69
    not R7, R7 ; R7 = 0x96
    andi R7, R7, 0xF ; R7 = 6
    ror R1, R0, R3 ; R1 = 0x80000006
    ori R7, R1, 9 ; R7 = 0x8000000F
    shra R1, R7, R3 ; R1 = 0xF0000001
    shr R2, R2, R3 ; R2 = 9
    st 0x8E, R2 ; (0x8E) = 9 new value in memory with address 0x58
    rol R2, R0, R3 ; R2 = 0x1A0
    or R4, R3, R0 ; R4 = 0x37
    and R1, R2, R0 ; R1 = 0x20
    st 0x27(R1), R4 ; (0x47) = 0x37 new value in memory with address 0x47
    sub R0, R2, R4 ; R0 = 0x169
    shl R1, R2, R3 ; R1 = 0xD00
    ldi R4, 6 ; R4 = 6
    ldi R5, 0x1B ; R5 = 0x1B
    mul R5, R4 ; HI = 0; LO = 0xA2
    mfhi R7 ; R7 = 0
    mflo R6 ; R6 = 0xA2
    div R5, R4 ; HI = 3, LO = 4
    ldi R10, 1(R4) ; R10 = 7 setting up argument registers
    ldi R11, -2(R5) ; R11 = 0x19 R8, R9, R10, and R11
    ldi R12, 0(R6) ; R12 = 0xA2
    ldi R13, 3(R7) ; R13 = 3
    jal R12 ; address of subroutine subA in R12 - return address in R15
    halt ; upon return, the program halts

ORG 0xA2 ; procedure subA
subA:
    add R9, R10, R12 ; R8 and R9 are return value registers
    sub R8, R11, R13 ; R9 = 0xA9, R8 = 0x16
    sub R9, R9, R8 ; R9 = 0x93
    jr R15 ; return from procedure
