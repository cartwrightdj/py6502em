; Example 6502 code for ca65
 
                
DSP	= $D012
KBD     = $D010
KBDCR   = $D011

;
; File generated by cc65 v 2.19 - Git b05bb4a
;
.include    "zeropage.inc"
.importzp   sp,ptr1,ptr2,ptr3,ptr4,tmp1,tmp2,tmp3,tmp4
.import     pushax, popax
.import     _strlen

.export     _kvprint, input_buffer
.export     _input
.export     _write

; ---------------------------------------------------------------
; int __near__ main (void)
; ---------------------------------------------------------------

.segment	"CODE"

.proc _write
    rts
.endproc

.proc	_putchar
	bit DSP
	bmi _putchar
	sta DSP
	rts
.endproc


; cc65 by default prepends an underscore to C function names.

.segment "CODE"

;----------------------------------------------------------------------------
; _kvprint - Output function for formatted printing routines.                   +--------------+
;                                                                               | OutData (Hi) |   <-- bottom (first pushed)
; Expected stack frame (6 bytes, pushed in order):                              +--------------+
;   [SP+0]  Length low byte                                                     | OutData (Lo) |
;   [SP+1]  Length high byte                                                    +--------------+
;   [SP+2]  Data pointer low byte                                               | Data Ptr (Hi)|   <-- pointer to buffer (e.g. CharArg, Str, or FSave)
;   [SP+3]  Data pointer high byte                                              +--------------+
;   [SP+4]  Output descriptor pointer low byte (ignored)                        | Data Ptr (Lo)|
;   [SP+5]  Output descriptor pointer high byte (ignored)                       +--------------+
;                                                                               | Length (Hi)  |   <-- number of bytes to output
; This routine pops the 6 bytes from the stack, then outputs (using _putchar)   +--------------+
; exactly 'Length' characters from memory at the given Data pointer.            | Length (Lo)  |   <-- top of stack (last pushed)
;                                                                               +--------------+
; Note: _putchar must be provided elsewhere (for example, writing A to a          Lower Memory
; hardware register or OS routine).
;----------------------------------------------------------------------------
;----------------------------------------------------------------------------
; Zero page variables used by _kvprint
; tmp1, tmp2, ptr1
;----------------------------------------------------------------------------

_kvprint:
    ;--- Pop the 16-bit length from the stack ---
    jsr     popax
    sta     tmp1
    stx     tmp2
    

    ;--- Pop the 16-bit data pointer from the stack ---
    jsr     popax
    sta     ptr1
    stx     ptr1+1
    
    nop
    nop
    

    ;--- Pop and discard the output descriptor pointer (2 bytes) ---
    jsr popax

    ;--- Loop until the 16-bit length reaches 0 ---
kvp_loop:
    lda     tmp1      ; Test low byte of length...
    ora     tmp2      ; ...or high byte (if both zero, length is 0)
    beq     kvp_done        ; If zero, we're finished

    ;--- Load one byte from the data pointer ---
    ldy     #0              ; Use Y=0 for zero-page indirect addressing
    lda     (ptr1),y  ; Fetch the character pointed to by kvp_ptr
    beq     kvp_done        ; End on null charachter, regardless of count?
    jsr     _putchar        ; Call the external routine to output the character

    ;--- Increment the 16-bit pointer ---
    inc     ptr1
    bne     kvp_no_inc_hi   ; If low byte didn’t roll over, skip incrementing high byte
    inc     ptr1+1
kvp_no_inc_hi:

    ;--- Decrement the 16-bit length by 1 ---
    lda     tmp1
    beq     dec_with_borrow ; If low byte is zero, a borrow is needed
    dec     tmp1
    jmp     kvp_loop
dec_with_borrow:
    lda     #$FF           ; Low byte was zero, so set it to $FF
    sta     tmp1
    dec     tmp2      ; And decrement the high byte
    jmp     kvp_loop

kvp_done:
    nop
    rts                 ; Return to caller

;----------------------------------------------------------------------------
; _kvprint - Output function reading input from kVirtualTerminal
;
.proc _input
    ; Argument `s` (prompt string) is passed on the stack at SP+2
    jsr     pushax      ; pushax for call to _kvprint
    jsr     _strlen     ; get lenght of prompt string
    jsr     pushax      ; pushax for call to _kvprint
    jsr     _kvprint    

get_input:
    ldx     #0       ; X will be the index into input_buffer

read_loop:
    lda     KBDCR
    bpl     read_loop
    lda     KBD    ; Assume _getc reads a character into A
    cmp     #$0D      ; Check for ENTER key (ASCII 13)
    beq     done_input
    cmp     #00
    beq     done_input
    sta     input_buffer, x ; Store the character in the buffer
    inx
    cpx     #63      ; Prevent buffer overflow
    bne     read_loop

done_input:
    lda #0       ; Null-terminate the string
    sta input_buffer, x

    ; Return pointer to input_buffer
    lda #<input_buffer
    ldx #>input_buffer
    rts
.endproc



.segment    "BSS"
input_buffer: .res 64  ; Reserve a 64-byte buffer for input




