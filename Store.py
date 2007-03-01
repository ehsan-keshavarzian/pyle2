import pickle
import os

class Store:
    def probe_kind(self):
	return 'txt'

    def has_key(self, title):
	subClassResponsibility()

    def getitem(self, title, kind, defaultvalue, is_binary = False):
	subClassResponsibility()

    def setitem(self, title, kind, value, is_binary = False):
	subClassResponsibility()

    def getpickle(self, title, kind, defaultvalue):
	p = self.getitem(title, kind, None, True)
	if p:
	    return pickle.loads(p)
	else:
	    return defaultvalue

    def setpickle(self, title, kind, value):
	self.setitem(title, kind, pickle.dumps(value), True)

    def page(self, title, createIfAbsent = False):
	if has_key(self, title) or createIfAbsent:
	    return Page(self, title)
	else:
	    raise KeyError(title)

    def __get__(self, title):
	return self.page(title)

class FileStore(Store):
    def __init__(self, dirname):
	self.dirname = dirname

    def path_(self, title, kind):
	p = os.path.join(self.dirname, title)
	if kind is not None:
	    p = p + '.' + kind
	return p

    def has_key(self, title):
	return os.path.exists(self.path_(title, self.probe_kind()))

    def file_open_mode_(self, base, is_binary):
        if is_binary:
            return base + 'b'
        else:
            return base

    def getitem(self, title, kind, defaultvalue, is_binary = False):
	try:
	    f = open(self.path_(title, kind), self.file_open_mode_('r', is_binary))
	    content = f.read()
	    f.close()
	    return content
	except IOError:
	    return defaultvalue

    def setitem(self, title, kind, value, is_binary = False):
	f = open(self.path_(title, kind), self.file_open_mode_('w', is_binary))
	f.write(value)
	f.close()

    def commit(self):
	pass
