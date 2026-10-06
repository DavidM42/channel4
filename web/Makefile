all : execute_reflash page.mpfs push 

IP?=192.168.4.1

mfsmaker : mfsmaker.c
	gcc -o $@ $^

page.mpfs : mfsmaker page
#	cat to_compress/*.js | gzip -9 > page/compressed.js.gz
	./mfsmaker page page.mpfs

pushtodev : pushtodev.c
	gcc -o $@ $^

# The firmware updater is a Python script.  "make netburn" expects a program of this name.
execute_reflash : execute_reflash.py
	cp $< $@
	chmod +x $@

push : pushtodev page.mpfs
	./pushtodev $(IP) 524288 page.mpfs

clean :
	rm -rf mfsmaker page.mpfs pushtodev execute_reflash
