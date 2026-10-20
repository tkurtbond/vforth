VFORTH - a Forth 2012 System for VAX/VMS
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

VFORTH is a Forth 2012 system for VAX/VMS V5.5-2, written in VAX
MACRO.  Like VTIL, the 1988 VAX Threaded Interpretive Language it
takes its lessons from, it is subroutine threaded: a colon
definition is VAX code, mostly ``JSB`` instructions to the words it
uses, with small words like ``DUP`` and ``+`` compiled in line and
constants and variables compiled as literals.

It provides the Core and Core Extension word sets and all of the
optional word sets: Block, Double-Number, Exception, Facility, File
Access, Floating-Point, Locals, Memory-Allocation, Programming-Tools,
Search-Order and String, each with its extensions.  It passes Gerry
Jackson's Forth 2012 test suite with no errors.

.. contents::


Building
========

On the VAX, with the ``VF*.MAR`` files and ``DESCRIP.MMS`` in one
directory::

    $ MMS

builds ``VFORTH.EXE`` and ``VFORTHDBG.EXE`` (the same, linked with
the debugger, and without VFORTH's condition handler, so the debugger
sees exceptions first).  ``MMS CLEAN`` deletes what MMS made.

From Linux, ``tools/vf-build`` copies the sources to
``[.VFORTH]`` of the ``vtil`` account on the VAX by FTP and runs MMS
there; ``tools/vf-test script.fth`` runs a script there with VFORTH
and shows the result.  The account's password is read from
``~/.netrc-vtil-vax``.

To move the sources to a VAX some other way, ``make`` (GNU make)
packs them in ``vforth.zip``; on the VAX, ``UNZIP -a VFORTH.ZIP``
unpacks it as VMS text files, ready for MMS.


Running
=======

::

    $ VFORTH :== $DEV:[DIR]VFORTH
    $ VFORTH                        ! interactive
    $ VFORTH FILE1 FILE2            ! INCLUDE these first

At a terminal VFORTH reads lines with SMG, so the usual VMS line
editing and command recall (up and down arrows) work, and it says
`` ok`` after each line it interprets.  ``Ctrl/C`` interrupts what is
running (``THROW -28``).  ``BYE`` leaves.  When ``SYS$INPUT`` is a
file, VFORTH reads its lines and stops at its end.

An uncaught error shows where it happened, the word, and the message::

    DUA1:[USERS.VTIL.VFORTH]TEST.FTH;1, line 12: FOO: undefined word

then the line it was in, if it came from a file, empties the stacks,
abandons any definition being compiled, sets ``BASE`` back to
decimal, and goes back to the terminal.


Files
=====

=================  ===============================================
``VFMACROS.MAR``   macros, constants, register use, the header layout
``VFDATA.MAR``     variables and the stacks
``VFCORE.MAR``     stack, arithmetic, logic and memory words
``VFTERM.MAR``     terminal input and output, the Facility word set
``VFNUM.MAR``      number conversion
``VFINTERP.MAR``   the text interpreter, ``EVALUATE``, ``CATCH``/``THROW``, ``QUIT``
``VFCOMP.MAR``     the compiler, defining words, control structures
``VFLOCALS.MAR``   the Locals word set
``VFSEARCH.MAR``   the Search-Order word set, ``ENVIRONMENT?``
``VFSTRING.MAR``   the String word set
``VFDOUBLE.MAR``   the Double-Number and Memory-Allocation word sets
``VFTOOLS.MAR``    the Programming-Tools word set, ``SEE``, ``DUMP``
``VFFILE.MAR``     the File-Access word set
``VFBLOCK.MAR``    the Block word set
``VFFLOAT.MAR``    the Floating-Point word set
``VFMAIN.MAR``     the condition handler and the main procedure
``VFDBG.MAR``      put first, it makes ``VFORTHDBG``
=================  ===============================================


Testing
=======

``tests/smoke.fth`` and ``tests/float.fth`` are quick checks.

Gerry Jackson's test suite
(https://github.com/Forth-Standard/forth-standard-test-suite) is the
git submodule ``forth-standard-test-suite``; fetch it with ``git
submodule update --init``.  To run it, copy its ``src`` files to the
VAX (``tools/vax-put forth-standard-test-suite/src/*``) and run, as
``SYS$INPUT``::

    S" tester.fr" INCLUDED
    S" core.fr" INCLUDED
    a line for the ACCEPT test to read
    S" coreplustest.fth" INCLUDED
    S" utilities.fth" INCLUDED
    S" errorreport.fth" INCLUDED
    S" coreexttest.fth" INCLUDED
    ... and so on, in the order of runtests.fth ...
    REPORT-ERRORS

The result is no errors in any word set.

Of the floating-point tests in ``src/fp``, ``ak-fp-test.fth`` and
``to-float-test.4th`` pass; ``fpzero-test.4th`` sees no signed zero
and skips itself; ``paranoia.4th`` finds that the arithmetic rounds
correctly and has a guard digit, reports the VAX's lack of a sticky
bit and of gradual underflow, and stops at the overflow test, since
G_floating overflow traps (``THROW -43``) rather than giving an
infinity.  ``fpio-test.4th``, ``ieee-*.fs`` and ``fatan2-test.fs``
depend on IEEE formats, infinities and NaNs, which the VAX doesn't
have.


How it works
============

Registers: R11 is the data stack pointer (it grows down; the top
item is at ``(R11)``); SP is the return stack; R10 points at the
current definition's locals; R9 is the floating-point stack pointer.
R0-R8 are scratch.  FP and AP are left alone: VMS's condition
handling depends on FP.

A header is a link to the previous word, a length byte (with a
hidden bit), the name, and a flags byte (immediate, compile-only, and
the length of the code to compile in line).  The execution token is
the address of the code just after it.

The stacks are in VFORTH's own memory, each with no-access guard
pages on both sides; an access violation in a guard page becomes the
stack's overflow or underflow ``THROW``.  Each colon definition
starts by reading 12 Kbytes below SP, so runaway recursion hits the
guard while there is still stack for the exception.

VMS exceptions (access violations, integer and floating division by
zero, floating overflow, reserved operands, errors signaled by the
run-time library) go to a condition handler that turns them into
``THROW`` codes: if the exception happened in VFORTH's code, it
changes the PC in the signal array and continues; if it happened in a
procedure VFORTH called, it unwinds to the main procedure.

The Ctrl/C AST cancels a terminal read, or else changes the
interrupted PC it was given to the code that does ``THROW -28``.  (It
must not signal, since unwinding out of an AST leaves later ASTs
blocked.)  If the interrupted code was a library routine or system
service, it sets a flag that the output routines and ``MS`` check.

Files are byte streams.  Stream_LF, Stream, Stream_CR, undefined
and 512-byte fixed-length record files are read and written with RMS
block I/O; other record formats (variable-length records, as made by
EDT and most VMS utilities) are read a record at a time, each with an
LF after it, and written a line at a time.  ``CREATE-FILE`` makes
Stream_LF files.  ``RESIZE-FILE`` shortens a file with ``$TRUNCATE``.


Documentation required by the standard
======================================

Implementation-defined options
------------------------------

Aligned addresses
    4-byte (cell) alignment, though the VAX doesn't need it.  A
    character-aligned address is any address.  Floats are aligned like
    cells.

Address unit, cell, character
    An address unit is 8 bits.  A cell is 4 address units, 32 bits; a
    character is 1.  Characters are 8-bit (ISO Latin-1 at a VT2xx
    terminal).

Number representation
    Two's complement.  Arithmetic overflow wraps around (integer
    overflow traps are off).  n: -2147483648 to 2147483647; +n: 0 to
    2147483647; u: 0 to 4294967295; d: -2**63 to 2**63-1; +d: 0 to
    2**63-1; ud: 0 to 2**64-1.

Division
    Symmetric (rounded toward zero) for ``/``, ``MOD``, ``/MOD``,
    ``*/`` and ``*/MOD``.  ``FM/MOD`` and ``SM/REM`` do what they say.
    Division by zero is ``THROW -10``.

``STATE``
    -1 when compiling.

``EMIT`` and ``TYPE``
    Characters are sent as they are, except that at a terminal LF is
    sent as CR LF.  When ``SYS$OUTPUT`` is not a terminal, each line
    (ended by LF, i.e. ``CR``) becomes a record.

``ACCEPT`` and the input line
    At a terminal, lines are read by ``SMG$READ_COMPOSED_LINE``: VMS
    line editing, with recall of the last 20 lines.  Return ends the
    line; the cursor goes to the next line.  From a file, each record
    is a line.  The keyboard input buffer holds 1024 characters.

``KEY`` and ``EKEY``
    ``KEY`` reads one character without echo; every character,
    including control characters, is returned.  ``EKEY`` decodes the
    VT100/VT220 escape sequences for the arrow keys, the editing
    keypad, PF1-PF4 (as ``K-F1``-``K-F4``) and F5-F12, with xterm-style
    modifiers.

Delimiters
    When parsing with a space delimiter (``PARSE-NAME``, ``WORD`` with
    ``BL``, the text interpreter), every character with a code of 32 or
    less matches the delimiter.

Control-flow stack
    The data stack.  An orig or dest is one cell (an address); ``DO``
    and ``?DO`` push two.

Digits beyond 35
    Not converted.  Letters of either case are digits 10-35.

Names
    Up to 127 characters, any characters but space and control
    characters; finding names ignores case (ASCII letters only).
    Longer names are ``THROW -19``.

Strings
    A counted string holds up to 255 characters.  A parsed string can
    be as long as the input buffer: 1024 characters from the terminal
    or a file.  ``ENVIRONMENT?`` strings can be any length.

Buffers
    ``WORD``: 258 bytes.  Pictured numeric output: 256 bytes.
    ``PAD``: 1024 bytes, used only by programs.  ``S"`` and ``S\"``
    when interpreting: four 1024-byte buffers, used in turn.

``ABORT"``
    Displays the message after the error location, like any uncaught
    ``THROW``, then does ``ABORT``.

Prompt
    `` ok`` after each line interpreted at the terminal.

User input and output devices
    ``SYS$INPUT`` and ``SYS$OUTPUT``; redefine them with DCL to use
    others.

Dictionary
    Definitions are compiled into a 2 Mbyte data space as VAX code.
    There are no read-only regions.  The current definition can't be
    found until ``;``, even after ``DOES>``.

Block
    Blocks are 1024 bytes, kept in the file ``BLOCKS.FB`` (in the
    default directory) unless ``OPEN-BLOCKS ( c-addr u -- )`` names
    another.  There are 8 block buffers.  ``LIST`` shows 16 lines of
    64 characters.  Lines in a block are 64 characters, as for ``\``.

Double-Number
    As above.

Exception
    ``THROW`` codes -1 to -58 are the standard's.  A VMS condition
    with no standard equivalent is thrown as its VMS status code, and
    an uncaught one is reported with its VMS message.

Facility
    ``MS`` uses ``$SETIMR``.  ``TIME&DATE`` is the local time.
    ``PAGE`` and ``AT-XY`` send VT100 sequences.  ``EKEY?`` is true if a
    character is waiting.

File-Access
    File names are VMS file specifications; ``INCLUDED`` and
    ``REQUIRED`` add ``.FTH`` if no type is given.  File access methods:
    ``R/O`` 1, ``W/O`` 2, ``R/W`` 3, ``BIN`` ors in 4 and changes
    nothing else.  An ior is 0 or a VMS (RMS) status code.  Line
    terminators: LF, with a CR before it dropped.  At most 1024
    characters of a line are read.  ``FILE-STATUS`` returns 0 and an ior
    of 0 if the file exists and can be read.  ``INCLUDE-FILE``
    nests as deeply as the return stack allows.

Floating-Point
    VAX G_floating: 64 bits, 53-bit fraction, about 15.9 decimal
    digits, range about 0.56E-308 to 8.98E307.  There are no
    infinities, NaNs or minus zero.  Rounding is to nearest.  Overflow
    is ``THROW -43``, division by zero ``THROW -42``, a reserved
    operand ``THROW -46``, and a domain error in a math library routine
    (for example ``-1E FSQRT``) ``THROW -46``; underflow gives 0.
    ``DFLOAT``\s are G_floating too; ``SFLOAT``\s are F_floating (32
    bits).  ``REPRESENT`` is exact, rounding ties to even; ``F.``,
    ``FE.`` and ``FS.`` show ``PRECISION`` (initially 15, at most 36)
    significant digits.  ``>FLOAT`` takes the standard syntax, with E,
    e, D or d before the exponent; a string of blanks is zero.  The
    text interpreter recognizes floats only when ``BASE`` is decimal.
    The floating-point stack holds 4096 numbers, and is separate.

Locals
    Up to 32 locals in a definition.

Memory-Allocation
    ``ALLOCATE`` and ``RESIZE`` use ``LIB$GET_VM``; the ior is 0 or a
    VMS status code.

Programming-Tools
    ``SEE`` shows a colon definition's code, naming the words it calls
    and showing literals and strings; other code is shown as bytes in
    hex.  ``ASSEMBLER`` and ``EDITOR`` name empty word lists.  ``CS-PICK``
    and ``CS-ROLL`` work on the data stack.  ``FORGET`` and ``MARKER``
    restore the dictionary and the word lists.

Search-Order
    The search order can have 16 word lists.  ``WORDLIST`` makes as many
    as there is room for.

Ambiguous conditions
--------------------

VFORTH takes one of these actions:

* An undefined word, or one that is not a number:
  ``THROW -13``.
* Stack overflow and underflow of the data, return and floating-point
  stacks are caught by guard pages: ``THROW -3``, ``-4``, ``-5``,
  ``-6``, ``-44`` or ``-45``.  Underflow is caught only when the memory
  beyond the stack is touched, so ``DROP`` on an empty stack is not an
  error until the next item is read.
* Dictionary overflow: ``THROW -8``.
* Division by zero: ``THROW -10`` (``-42`` for floats).
* Addressing memory that isn't there: ``THROW -9``.
* Interpreting a compile-only word: ``THROW -14``.  ``'`` and ``FIND``
  of such a word return its xt, which does its compilation semantics.
* A zero-length name where one is needed: ``THROW -16``.
* Pictured numeric output overflow: ``THROW -17``.  Parsed string
  overflow (more than 255 characters for ``WORD``): ``THROW -18``.
* A name too long: ``THROW -19``.
* Results out of range (``*``, ``*/``, and so on) wrap around.
  ``UM/MOD``, ``SM/REM`` and ``FM/MOD`` with a quotient out of range
  give a meaningless quotient and remainder, without an error.
* ``TO`` before a name not defined by ``VALUE``, ``2VALUE``, ``FVALUE``
  or as a local: ``THROW -32``.
* ``>BODY`` or ``DOES>`` of a word not made by ``CREATE``: they act on
  the bytes after its first 6 bytes of code.
* Executing a word made by ``DEFER`` before it is given an xt:
  ``THROW -21``.
* ``\x`` without two hex digits in ``S\"`` takes what digits there are;
  an unknown escape gives the character after the ``\``.
* Others: the result is undefined; most likely an access violation,
  ``THROW -9``.

Other system documentation
--------------------------

* Non-standard words that use ``PAD``: none.
* Terminal facilities: a VT100-compatible terminal; line editing and
  recall at the prompt; Ctrl/C interrupts.
* Data space available: 2 Mbytes, less a 4 Kbyte margin; ``UNUSED``
  tells.
* Return stack: 65536 cells.  Data stack: 16384 cells.  Floating-point
  stack: 4096 floats.
* The system's own dictionary, code and headers, takes 28,285 bytes,
  outside the 2 Mbyte data space; its variables and buffers take
  another 23,764 bytes.


Non-standard words
==================

``BYE``, ``SEE``, ``WORDS``, ``DUMP`` and the like are standard.  The
others are ``COMPILE-ONLY`` (makes the latest word compile-only) and
``OPEN-BLOCKS ( c-addr u -- )`` (use another block file).
