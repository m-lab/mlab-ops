CURL?= $(shell if test -f /usr/bin/curl ; then echo "curl -s -H Pragma: -O -R -S --fail --show-error" ; fi)
CLIENT?= $(CURL)
AWK= awk
MD5SUM= md5sum
SED= sed

SPECFILE = kernel-2.6.spec

# Thierry - when called from within the build, PWD is /build
PWD=$(shell pwd)

define get_sources_md5
$(shell cat sources 2>/dev/null | awk 'gensub("^.*/", "", 1, $$2) == "$@" { print $$1; exit; }')
endef
define get_sources_url
$(shell cat sources 2>/dev/null | awk 'gensub("^.*/", "", 1, $$2) == "$@" { print $$2; exit; }')
endef

SOURCEFILES := $(shell cat sources 2>/dev/null | awk '{ print gensub("^.*/", "", 1, $$2) }')

all: pathchirp

sources: $(SOURCEFILES) $(TARGETS)

$(SOURCEFILES): #FORCE
	@if [ ! -e "$@" ] ; then echo "$(CLIENT) $(get_sources_url)" ; $(CLIENT) $(get_sources_url) ; fi
	@if [ ! -e "$@" ] ; then echo "Could not download source file: $@ does not exist" ; exit 1 ; fi
	@if test "$$(md5sum $@ | awk '{print $$1}')" != "$(get_sources_md5)" ; then \
		echo "md5sum of the downloaded $@ does not match the one from 'sources' file" ; \
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

replace-sources:
	rm -f sources
	@$(MAKE) new-sources

new-sources: download-sources
	@for i in $(SOURCES); do \
		echo "$(MD5SUM) $$i >> sources"; \
		$(MD5SUM) $${i##*/} | $(AWK) '{ printf "%s  %s\n", $$1, "'"$$i"'" }' >> sources; \
	done

TARGET ?= $(shell uname -m)
#PREPARCH ?= noarch
#RPMDIRDEFS = --define "_sourcedir $(PWD)" --define "_builddir $(PWD)" --define "_srcrpmdir $(PWD)" --define "_rpmdir $(PWD)"
pathchirp: sources
	@echo "what is this?"
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
