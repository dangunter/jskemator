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

class Skema:
    def __init__(self, json, schema=None, simple_lists=False):
        """Create new schema skeleton.
        
        Args:
            - `json` = JSON object, a dictionary.
            - `schema` = Optional schema, a dictionary
            - `simple_lists` = If True, do not generate schema items
                               for each value in a list of scalars.
        """
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
        """Dispatch to appropriate processing function for the
        type of the object `o`, pulling default values from the
        existing schema `s`.
        """
        typestr = '_' + o.__class__.__name__
        if not hasattr(self, typestr):
            raise ValueError("Unrecognized type for {}".format(o))
        return getattr(self, typestr)(o, s)

    def _dict(self, d, s):
        "Process a dict."
        skema = self.set_defaults(s)
        skema['type'] = 'object'
        skema['properties'] = { }
        for key, value in d.items ():
            if s is None:
                new_s = None
            else:
                # match properties in schema, but default to None
                new_s = s['properties'].get(key, None)
            skema['properties'][key] = self._skemate(value, new_s)
        return skema

    def _list(self, l, s):
        """Process a list.
        
        If `simple_lists` was False in the constructor, then
        do not recurse into lists that have only scalar values.
        """
        skema=self.set_defaults(s)
        skema['type'] = 'array'
        if self._skip_list_scalars and _scalars(l):
            return skema
        skema['properties'] = [ ]
        for value in l:
            skema['properties'].append(self._skemate(value)) 
        return skema

    _tuple = _list
    
    def _str(self, v, s):
        "Process a string."
        return _scalar("string", v, s)

    def _int(self, v, s):
        "Process an integer"
        return _scalar("integer", v, s)

    def _float(self, v, s):
        "Process a float"
        return _scalar("float", v, s)
        
    def _scalar(self, typename, val, schema):
        res = self.set_defaults(schema)
        res['type'] = typename
        res['pattern'] = ''
        res['value'] = val
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
