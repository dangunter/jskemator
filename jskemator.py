"""
Take JSON data and generate a skeleton for the JSON schema which represents it

Revised from https://github.com/gonvaled/jskemator
"""
import simplejson as json
import pprint
import sys
import optparse

pp = pprint.PrettyPrinter(indent=4)

_SCALARS = set((str, int, long, float))

def _scalars(x):
    """Return True if the list `x` is only composed
    of scalars, otherwise false. 
    """
    return all(map(lambda y: type(y) in _SCALARS, x))

class JSkemator:
    def __init__(self, json=None, schema=None, simple_lists=False):
        self.obj, self.s = json, schema
        self._skip_list_scalars = not simple_lists

    def set_defaults (self, s):
        default = { }
        if s != None:
            default['description'] = s.get('description','None')
            default['additionalProperties'] = (
                s.get('additionalProperties', False))
            default['required'] = s.get('required', True)
        else:
            default['description'] = 'Dummy description'
            default['additionalProperties'] = False
            default['required'] = True
        return default

    def skemate(self):
        return self._skemate(self.obj, self.s)

    def _skemate(self, o, s=None):
        if isinstance(o, (list, tuple)):
            return self._skemateList(o, s)
        if isinstance(o, dict):
            return self._skemateDict(o, s)
        if isinstance(o, str):
            return self._skemateStr(o, s)
        if isinstance(o, int):
            return self._skemateInt(o, s)
        if isinstance(o, long):
            return self._skemateLong(o, s)
        if isinstance(o, float):
            return self._skemateFloat(o, s)
        if o == None:
            return self._skemateNone(o, s)
        if o == False:
            return self._skemateFalse(o, s)
        if o == True:
            return self._skemateTrue(o, s)
        raise ValueError("Unrecognized value for {}".format(o))

    def _skemateDict(self, d, s):
        "Process dict."
        skema=self.set_defaults(s)
        skema['type'] = 'object'
        skema['properties'] = { }
        for key, value in d.items ():
            #print "key > ", key
            if s is None:
                new_s = None
            else:
                # match properties in schema, but default to None
                new_s = s['properties'].get(key, None)
            skema['properties'][key] = self._skemate(value, new_s)
        return skema

    def _skemateList(self, l, s):
        #print "_skemateList"
        skema=self.set_defaults(s)
        skema['type'] = 'array'
        if self._skip_list_scalars and _scalars(l):
            return skema
        skema['properties'] = [ ]
        for value in l:
            skema['properties'].append(self._skemate(value)) 
        return skema

    def _skemateStr(self, strval, s):
        #print "_skemateStr"
        res=self.set_defaults(s)
        res['type'] = 'string'
        res['pattern'] = ''
        res['value'] = strval
        return res

    def _skemateInt(self, i, s):
        #print "_skemateInt"
        res=self.set_defaults(s)
        res['type'] = 'integer'
        res['pattern'] = ''
        res['value'] = i
        return res

    def _skemateFloat(self, f, s):
        #print "_skemateFloat"
        res=self.set_defaults(s)
        res['type'] = 'float'
        res['pattern'] = ''
        res['value'] = f
        return res
        
def main(argv):
    """Process command-line options and run.
    """
    # Process options
    desc = __doc__
    parser = optparse.OptionParser(usage="%prog [options] [file]",
                                    description=desc)
    parser.add_option("-s", "--schema", dest="sname", metavar="FILE",
                      help="Read schema from FILE")
    options, args = parser.parse_args()
    if len(args) == 0:
        infile = sys.stdin
    else:
        fname = args[0]
        try:
            infile = open(fname)
        except IOError, err:
            parser.error("Cannot open file {f}: {e}".format(f=fname, e=err))
    if options.sname:
        try:
            sfile = open(options.sname)
        except IOError, err:
            parser.error("Cannot open schema file {f}: {e}".format(
                         f=options.sname, e=err))
    # Run
    try:
        json_obj = json.load(infile)
    except json.JSONDecodeError:
        if infile is sys.stdin:
            infile = "<stdin>"
        parser.error("Could not decode input file {f}".format(f=infile))
    if infile is not sys.stdin:
        infile.close()
    if sfile:
        try:
            schema_obj = json.load(sfile)
        except json.JSONDecodeError:
            parser.error("Could not decode schema file {f}".format(f=sfile))
    else:
        schema_obj = None
    jskemator = JSkemator(json=json_obj, schema=schema_obj)
    skema = jskemator.skemate()
    print(json.dumps(skema, indent=4))
    return 0
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
