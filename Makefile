all: executable index.cgi

run: executable
	./pyle.cgi 127.0.0.1

index.cgi:
	ln -s pyle.cgi index.cgi

executable:
	chmod a+x pyle.cgi
	chmod a+x sublanguages/sequence-helper.sh

clean:
	rm -f $$(find . -name '*.pyc')
	rm -f pyledb_cache/*
