;  The WOZ Monitor for the Apple 1
;  Written by Steve Wozniak in 1976


STRPTR			= $F
CMDPTR			= $10
STRBUFWRDCNT	= $0300
STR_IN_BUF		= $0301

PROC_SRCH_MODE  = $A

proc_ptr		= $7001
activ_proc		= $03EC
proc_count		= $03EF
PROC_TABLE		= $03F0

KBD             = $D010         ;  PIA.A keyboard input
KBDCR           = $D011         ;  PIA.A keyboard control register
DSP             = $D012         ;  PIA.B display output register
DSPCR           = $D013         ;  PIA.B display control register

MAX_PROCS		= $05


SCR             = $D014         ;  PIA.B display output register
SDR          	= $D015         ;  PIA.B display control register

V_MEMORY_SWITCH	= $8000
PROC_STORE		= $7000




;               .org $EE00

			
kernel:				
					CLC
					SEI
					LDA #$FF
					STA activ_proc
					LDA #<kernel_loop
					LDX #>kernel_loop
					JSR add_proc
					LDX #$0
					STX activ_proc
					LDA #<PROMPT
					LDX #>PROMPT
					JSR add_proc
					LDA #<loopx
					LDX #>loopx
					JSR add_proc
					; Init
					CLI


kernel_loop:					
					CLI
					JMP kernel_loop
					
loopx:				NOP
					NOP
					INY
					BNE loopx
					JMP loopx

hw_irq_handler:		SEI
					CLC
					STA V_MEMORY_SWITCH
					PHA
					TXA
					PHA
					TYA
					PHA
					TSX
					TXA
					ADC #$03
					PHA
					LDX activ_proc
					TXA
					ASL
					ASL
					ASL
					ADC #$04
					TAY
					PLA
					DEY
					STA PROC_TABLE,Y
					INY
					PLA
					STA PROC_TABLE,Y
					INY
					PLA
					STA PROC_TABLE,Y
					INY
					PLA
					STA PROC_TABLE,Y
					LDX activ_proc
					JSR next_active_block
					CPX activ_proc
					BEQ	no_switch
					LDA PROC_TABLE,Y
					AND #$03				; check if active process has been started
					CMP #$03
					BNE start_proc
switch_proc:		TXA
					STX activ_proc
					ASL
					ASL
					ASL
					ADC #$04
					TAY
					DEY 
					LDA PROC_TABLE,Y
					TAX
					TXS
					INY
					LDA PROC_TABLE,Y
					STA $7005
					INY
					LDA PROC_TABLE,Y
					TAX
					INY
					LDA PROC_TABLE,Y
					LDY activ_proc		
					
					STA V_MEMORY_SWITCH,Y
					LDY $7005
											; load saved proc info
no_switch:			CLI
					RTI
					.byte $0

; ------------------------------------------					
add_proc:			STA proc_ptr
					STX proc_ptr+1
					LDX activ_proc
					JSR next_free_block
					CPX activ_proc
					BNE ap_add
					RTS
ap_add:				LDA #$01
					STA PROC_TABLE,Y
					LDA proc_ptr
					INY 
					STA PROC_TABLE,Y
					LDA proc_ptr+1
					INY 
					STA PROC_TABLE,Y
					RTS
; -------------------------------------------
start_proc:			LDA PROC_TABLE,Y
					ORA #$03
					STA PROC_TABLE,Y
					STX activ_proc
					INY
					LDA PROC_TABLE,Y
					STA proc_ptr
					INY
					LDA PROC_TABLE,Y
					STA proc_ptr+1
					LDA #$4C
					STA proc_ptr-1
					TXA
					TAY
					LDX #$FD
					TXS 
					INC proc_count
					STA V_MEMORY_SWITCH,Y
					LDA #$00
					TAX
					TAY
					CLI
					JMP (proc_ptr)

; ------------------------------------------
next_free_block:	;SEI
					PHA
nfb_loop:			JSR next_proc_block
					CPX #MAX_PROCS+1
					BNE nfb_block_stat
					CPX activ_proc
					BNE nfb_block_stat
					PLA
					RTS
					LDX #$FF
					BNE nfb_loop
nfb_block_stat:		LDA PROC_TABLE,Y
					CMP #$00
					BNE nfb_loop
					PLA
					RTS
; ---------------------------
next_active_block:	PHA
nab_loop:			JSR next_proc_block
					CPX #MAX_PROCS+1
					BNE nab_block_stat
					CPX activ_proc
					BNE nab_block_stat
					PLA
					RTS
					LDX #$FF
					
nab_block_stat:		LDA PROC_TABLE,Y
					AND #$01
					CMP #$01
					BNE nab_loop
					PLA
					RTS
		
			

next_proc_block:	;EI
					PHA
npb_loop:			INX
					CPX #MAX_PROCS
					BNE npb_shift
					LDX #$FF
					BNE npb_loop
npb_shift:			TXA
					ASL
					ASL
					ASL
					TAY
					PLA
					RTS		; X will be next proc #, Y will be offset to block
			


PROMPT:			CLI
				LDA #$0D        ; CR.
				JSR PUTCHAR        ; Output it
				LDA #'$'        ; CR.
                JSR PUTCHAR        ; Output it
				LDA #':'        ; CR.
                JSR PUTCHAR        ; Output it
				LDA #$20        ; CR.
                JSR PUTCHAR        ; Output it
				LDY #$FF        ; Reset text index.
				
				JSR GETLINE
				JSR CNT_STRINBUF_WORDS
				LDA STRBUFWRDCNT
				BEQ PROMPT
				JSR PARSE_CMD
				JMP PROMPT
				
				.byte $0

GETLINE:        LDA KBDCR       ; Key ready?
                BPL GETLINE    ; Loop until ready.
                LDA KBD         ; Load character. B7 should be ‘1’.
				BEQ GETLINE	; Is this needed for null input??
				INY
				CPY #$FE			; Check for buffer overflow
				BEQ gl_overflow		;
                STA STR_IN_BUF,Y  	; Add to text buffer.
                CMP #$0D        	; CR?
				BNE GETLINE    		; Yes?
				LDA #0				; Then add, Terminating
				STA STR_IN_BUF,Y	; Zero
				RTS
				
gl_overflow:	LDA #0				; Then add, Terminating
				STA STR_IN_BUF,Y	; Zero	
				.byte #$0

; Print String A: lowbyte Y: Highbyte, store in string ptr and read until nul
PRINTSTR:		STA STRPTR
				STY STRPTR+1
				LDY #$FF
prtstr_loop:	INY
				LDA (STRPTR),Y
				BEQ printstr_eol
				JSR PUTCHAR
				JMP prtstr_loop
printstr_eol:	LDA #$13
				JSR PUTCHAR
				RTS

;-----------------------------------------------------------
; CNT_STRINBUF
; Purpose: 
;   - Count the number of words in the 'String in Buffer (STR_IN_BUF)
;   - store in STRBUFWRDCNT
;   - Jump to PROMPT when the parse is complete
; 
; Registers:
;   - A, X, Y used as general 6502 registers
;   - STRBUFWRDCNT (absolute) holds number of tokens
;   - STR_IN_BUF (some memory area) gets the extracted tokens
;
; On exit:
;   - STRBUFWRDCNT = number of tokens (words)
;   - STR_IN_BUF = zero-terminated copies of each token 
;   - Jumps to PROMPT if end of input was reached
;-----------------------------------------------------------
			
CNT_STRINBUF_WORDS:	LDA     #$00			; 1) Clear STRBUFWRDCNT (token counter)
					STA     STRBUFWRDCNT	; 2) X = 0 (index in STR_IN_BUF)
					TAX

;-----------------------------------------------------------
; Skip leading spaces
;-----------------------------------------------------------
					LDY     #$FF
skip_spaces: 		INY	
					LDA STR_IN_BUF,Y
					CMP #$20         		; Check if it's a space
					BNE found_nonspace		; If not branch
					LDX #$0					; reset x since its a space
					CPY #$FF				; else make sure not at end of buffer, 255 is it

					BNE skip_spaces			; if not at end, keep checking for spaces
					RTS						; if yes then it was all spaces, return 
					
;-----------------------------------------------------------
; Found a non-space character: new word
;-----------------------------------------------------------
found_nonspace:		CMP #$0					; Check if XA 
					BEQ end_of_str			; null terminator
					CPX #$0
					BNE skip_spaces
					INC STRBUFWRDCNT       ; We have a new token
					INX
					JMP skip_spaces

end_of_str:			LDA STRBUFWRDCNT
					CLC
					ADC #$30
					JSR PUTCHAR
					RTS
					
; =============================================================
; ============= PARSE COMMAND LINE ============================
; Expects Cmd Line to be in STR_IN_BUF

PARSE_CMD:			LDA #$FF
					TAX
					TAY
pc_loop:			INY
					INX
					LDA CMDTBL,X
					CMP STR_IN_BUF,Y
					BEQ pc_loop
check_unit_sep:		CMP #$1F
					BNE next_tbl_entry
					LDA STR_IN_BUF,Y
					CMP #$0
					BEQ get_cmd_address
					CMP #$20
					BNE pc_loop
get_cmd_address:	INX
					LDA #$4C
					STA CMDPTR
					LDA CMDTBL,X
					STA CMDPTR+1
					INX
					LDA CMDTBL,X
					STA CMDPTR+2
					JMP CMDPTR
					
next_tbl_entry:		DEX		
nte_loop:			INX			
					LDA CMDTBL,X
					CMP #$03
					BEQ cmd_not_found
					CMP #$1E
					BNE nte_loop
					LDY #$FF
					JMP pc_loop

cmd_not_found:		
					NOP
					RTS

				
; Expects A Register to contain character				
PUTCHAR:           	BIT DSP         ; DA bit (B7) cleared yet?
					BMI PUTCHAR        ; No, wait for display.
					STA DSP         ; Output character. Sets DA.
					RTS             ; Return.




CMDTBL:				.byte "HELP",$1F,<HELP_CMD,>HELP_CMD,$1E,"VER",$1F,<VER_CMD,>VER_CMD,$1E,"PS",$1F,<PS_CMD,>PS_CMD,$1E,$03


HELP_CMD:			LDA #<STRINGS
					LDY #>STRINGS
					JSR PRINTSTR
					RTS
					
VER_CMD:			LDA #<KERSTR
					LDY #>KERSTR
					JSR PRINTSTR
					RTS

PC_STRING:			.byte "PROCESS COUNT: ",$0
PS_CMD:				PHA
					TYA
					PHA
					CLC
					LDA #<PC_STRING
					LDY #>PC_STRING
					JSR PRINTSTR
					STA V_MEMORY_SWITCH
					LDX activ_proc
					LDA proc_count
					STA V_MEMORY_SWITCH,X
					ADC #$30
					JSR PUTCHAR
					PLA
					TAY
					PLA
					RTS
					
					LDA proc_count

KERSTR:				.byte "KEROS V. 1.2 (2025)",$0D,$0
STRINGS:			.byte "HELP",$0D,"PS",$0D,"VER",$0D,$0