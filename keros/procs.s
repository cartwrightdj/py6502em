; Example 6502 code for ca65
 
SYSMEM	= $8000
MAXPROCS = 16                

.export		_switch_vmem, _get_proc_state_base, proc_tbl

.import input_buffer

.struct proc_list
	current_proc		.byte
	active_procs		.byte
.endstruct
	

.struct proc_state
	parent_proc		.byte
	state_flags 	.byte 
	pc_main_lo		.byte 
	pc_main_hi 		.byte
	stack_point		.byte
	reg_a			.byte
	reg_x			.byte
	reg_y			.byte
	proc_flags		.byte
.endstruct


; ---------------------------------------------------------------
; int __near__ main (void)
; ---------------------------------------------------------------


.segment "PROCTBL"
proc_tbl: .res 64

; ---------------------------------------------------------------
; int __near__ get_proc_state_base (void)
; returns pointer to start of proc_tbl
; ---------------------------------------------------------------

.segment "CODE"
.proc	_get_proc_state_base
	lda #<proc_tbl
	ldx #>proc_tbl
	rts
.endproc


.segment "CODE"
.proc _switch_vmem
	tax
	sta	SYSMEM, x
	rts
.endproc

.proc _kvprintf
	nop
.endproc
