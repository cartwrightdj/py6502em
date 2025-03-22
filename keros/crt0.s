; ---------------------------------------------------------------------------
; crt0.s
; ---------------------------------------------------------------------------
;
; Startup code for cc65 (Single Board Computer version)

.include        "zeropage.inc"
.include        "_file.inc"

.export _init, _exit
.import _main, _hwirq, proc_tbl, proc_state
.import __RAM_START__, __RAM_SIZE__       ; Linker generated
.import __IRQ_VECTOR__, __filetab, _kvprintf, NotDone,afterLiteral
.import _stdout, _kvprint

.export   __STARTUP__ : absolute = 1        ; Mark as startup

STDOUT_FILENO   = 1

.struct proc_state
    parent_id      .byte
    state_flags   .byte 
    pc_main_lo    .byte 
    pc_main_hi    .byte
    stack_point   .byte
    reg_a         .byte
    reg_x         .byte
    reg_y         .byte
    proc_flags    .byte
.endstruct

; ---------------------------------------------------------------------------
; Place the startup code in a special segment

.segment  "STARTUP"

; ---------------------------------------------------------------------------
; A little light 6502 housekeeping

_init:    LDX     #$FF                 ; Initialize stack pointer to $01FF
          TXS
          CLD                          ; Clear decimal mode
          SEI
		  LDA #$FF
		  STA proc_tbl + proc_state::state_flags
          LDA #<_main
          STA proc_tbl + proc_state::pc_main_lo
          LDA #>_main
          STA proc_tbl + proc_state::pc_main_hi
          

; Set cc65 argument stack pointer
          LDA     #<(__RAM_START__ + __RAM_SIZE__)
          STA     sp
          LDA     #>(__RAM_START__ + __RAM_SIZE__)
          STA     sp+1


; ---------------------------------------------------------------------------
; Initialize stdout to kVirtualTerminal
        lda #$4c
        sta _stdout+4
        lda #<_kvprint
        sta $1028
        lda #>_kvprint
        sta $1029





; ---------------------------------------------------------------------------
; Call main()

          JSR     _main

; ---------------------------------------------------------------------------
; Back from main (this is also the _exit entry):  force a software break

_exit:    BRK

.segment "VECTORS"
    .word   $0
    .word   _init
    .word   _hwirq
