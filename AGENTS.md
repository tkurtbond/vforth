# AGENTS.md

Notes for coding agents working on VFORTH, a Forth 2012 system for
VAX/VMS V5.5-2 written in VAX MACRO.  README.rst is the user
documentation, including the Forth 2012 implementation-defined options
and ambiguous conditions; keep it in step with the code.

## Layout

- `VF*.MAR` -- the sources, assembled together as one module in the
  order given by `SOURCES` in `descrip.mms`.  `vfmacros.mar` comes first
  (macros, constants, register use, the header layout); `vfmain.mar`
  comes last.  A new source file must be added to both `SOURCES` and
  `DEPS` in `descrip.mms`, and to the Files table in README.rst.
- `vfdbg.mar` -- assembled first, it builds `VFORTHDBG.EXE`, which has
  no condition handler so the VMS debugger sees exceptions itself.
- `tests/` -- quick checks (`smoke.fth`, `float.fth`) and their
  expected output (`*.out`).
- `tools/` -- the build and test scripts that drive the VAX from Linux.
- `forth-standard-test-suite/` -- the Forth 2012 test suite, a git
  submodule.

## Building and testing

There is no Linux build: everything is assembled and run on a SIMH VAX
3900 (VMS V5.5-2H4) at 192.168.2.20, in `DUA1:[USERS.VTIL.VFORTH]`
(`[.VFORTH]` of the `vtil` account).

- `tools/vf-build` copies `descrip.mms` and `vf*.mar` to the VAX by FTP,
  runs `MMS`, and prints the diagnostics.  It takes a minute or more.
- `tools/vf-test script.fth...` copies each script to the VAX, runs it
  as `SYS$INPUT` of VFORTH, and writes the session to `script.out`
  beside it.  Compare `tests/*.out` after a change.
- `tools/vax-put` and `tools/vax-get` copy files to and from `[.VFORTH]`;
  `expect -f tools/vax-dcl.exp 'command'...` runs DCL commands there.
- The full Forth 2012 test suite is the git submodule
  `forth-standard-test-suite` (`git submodule update --init`); it is run
  as described under Testing in README.rst.  Don't edit files in it.  It must still show no
  errors in any word set after a change.

The output from the VAX contains a NUL byte before the `VFDCL>` prompt;
use `grep -a` (or `tr -d '\0'`) when filtering it, or grep will call it
binary and stop.

## Secrets

The VAX login and password are in `~/.netrc-vtil-vax`.  Never print
that file, never put the password on a command line, and never copy it
into a script or log: the tools read it themselves (`curl --netrc-file`,
and `tools/vax-login.tcl` with `log_user 0`).

## Conventions

- Match the existing style: lowercase MACRO, tabs, a `;` comment on most
  lines, a `;+++ ... ;---` block before each word or routine, and
  `newpage <Title>` between sections.
- Names: `v_` variables, `c_` constants, `t_` THROW codes, `s_`
  internal subroutines, `r_` targets reached by branching, `do_` code
  for defined words, `wid_` word lists.
- Built-in words are declared with `defword label,^~NAME~,flags,inl`
  (see `vfmacros.mar`).  Names containing `~` can't go through
  `defword`; write the header out by hand, as `F~` is.
- Registers: R11 data stack, R10 locals frame, R9 floating-point stack
  (G_floating, 8 bytes an item), SP the return stack, R0-R8 scratch.
  Never touch FP or AP: VMS condition handling depends on them.
- Errors are Forth THROW codes (`throw t_xxx`); VMS exceptions are
  turned into THROW codes by the handler in `vfmain.mar`.
- When MACRO reports a branch out of range, widen it with
  `python3 tools/fixbranch.py file.mar line...`.
- Commit or push only when the user asks.

## Pitfalls

Each of these has cost a build-and-test round trip on the slow VAX:

- In a MACRO operand `.` is the address of the operand, not of the
  instruction, so skipping a following `BRW` is `.+4`.
- `MOVL` sets the condition codes.  To restore a register after a
  routine that returns its answer in Z, use `PUSHR`/`POPR`, which don't.
- `^x` constants in macro arguments are taken as delimited arguments;
  write them in decimal.
- RMS `$FIND` by RFA on a Stream_LF file returns RMS-E-EOF unless an LF
  follows the offset.
- The Ctrl/C AST must never signal or unwind; it redirects the
  interrupted PC when the interrupted code is VFORTH's own, and
  otherwise sets `v_intpend` for `s_chkint` to throw later.
- Terminal reads for KEY and EKEY pass an empty terminator mask
  (`v_noterm`) so control characters come back as data.
- PAD belongs to programs: the system's own text goes in its own
  buffers (`v_xbuf`, `v_msgbuf`, the `S"` buffers).
- The VAX has no IEEE arithmetic: no infinities, NaNs, signed zero or
  gradual underflow, and overflow traps (THROW -43).
