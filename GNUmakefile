# GNUmakefile -- packages the VFORTH sources in a zip file for the VAX.
#
#   make            makes vforth.zip
#   make clean      deletes it
#
# On the VAX, UNZIP -a VFORTH.ZIP unpacks it, turning the text files
# into VMS text files, and MMS builds VFORTH there.

ZIP = vforth.zip

SRCS = descrip.mms $(sort $(wildcard vf*.mar)) README.rst AGENTS.md \
	$(wildcard tests/*.fth tests/*.out)

.PHONY: all clean

all: $(ZIP)

# Made afresh each time, so a file that has gone from the tree goes
# from the zip file too.
$(ZIP): $(SRCS) GNUmakefile
	rm -f $@
	zip -X $@ $(SRCS)

clean:
	rm -f $(ZIP)
