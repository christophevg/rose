all: libmul.dylib

lib%.dylib: %.c
	@echo "*** building $@"
	@${CC} -dynamiclib -o $@ $<
	@strip $@
	@ls -l $@

clean:
	@rm -f *.dylib *.o *.out