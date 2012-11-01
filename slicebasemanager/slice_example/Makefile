CURL?= $(shell if test -f /usr/bin/curl ; then \
		echo "curl -s -H Pragma: -O -R -S --fail --show-error" ; fi)
CLIENT?= $(CURL)
AWK= awk
MD5SUM= md5sum
SED= sed

PWD=$(shell pwd)

define get_sources_md5
$(shell cat sources 2>/dev/null | \
	awk 'gensub("^.*/", "", 1, $$2) == "$@" { print $$1; exit; }')
endef
define get_sources_url
$(shell cat sources 2>/dev/null | \
	awk 'gensub("^.*/", "", 1, $$2) == "$@" { print $$2; exit; }')
endef

SOURCEFILES := $(shell cat sources 2>/dev/null | \
			awk '{ print gensub("^.*/", "", 1, $$2) }')

BINS=bin/pathchirp_rcv bin/pathchirp_run bin/pathchirp_snd
all: $(BINS)

sources: $(SOURCEFILES) $(TARGETS)

$(SOURCEFILES): #FORCE
	@if [ ! -e "$@" ] ; then \
		echo "$(CLIENT) $(get_sources_url)" ; \
		$(CLIENT) $(get_sources_url) ; \
	 fi
	@if [ ! -e "$@" ] ; then \
		echo "Could not download source file: $@ does not exist" ; \
		exit 1 ; \
	 fi
	@if test "$$(md5sum $@ | awk '{print $$1}')" != "$(get_sources_md5)" ; \
	 then \
		echo -n "md5sum of the downloaded $@ does not match the one " \
		echo "from 'sources' file" ; \
		echo "Local copy: $$(md5sum $@)" ; \
		echo "In sources: $$(grep $@ sources)" ; \
		exit 1 ; \
	else \
		ls -l $@ ; \
	fi

download-sources:
	@for i in $(SOURCES); do \
		if [ ! -e "$${i##*/}" ]; then \
			echo "$(CLIENT) $$i"; \
			$(CLIENT) $$i; \
		fi; \
	done

TARGET ?= $(shell uname -m)
$(BINS): sources
	tar -zxf pathchirp-2.4.1.tar.gz 
	cd pathchirp-2.4.1; \
	./configure ; \
	make
	mkdir -p ./bin/
	cp pathchirp-2.4.1/Bin/$(TARGET)/pathchirp_rcv ./bin/
	cp pathchirp-2.4.1/Bin/$(TARGET)/pathchirp_run ./bin/
	cp pathchirp-2.4.1/Bin/$(TARGET)/pathchirp_snd ./bin/

clean:
	rm -rf bin/* pathchirp-2.4.1*
