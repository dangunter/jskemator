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

def is_scalar(x):
    return type(x) in _SCALARS
    
def _scalars(x):
    """Return True if the list `x` is only composed
    of scalars, otherwise false. 
    """
    return all(map(is_scalar, x))

class Schema(dict):
    # If True, do not generate schema items
    # for each value in a list of scalars.
    simple_lists = False

    def __init__(self, json, schema={}):
        """Create new schema skeleton.
        
        Args:
            - `json` = JSON object, a dictionary.
            - `schema` = Optional schema, a dictionary
        """
        obj = self._skemate(json, schema)
        dict.__init__(self, obj)

    def _skemate(self, obj, old_schema={}):
        """Dispatch to appropriate processing function for the
        type of the object `obj`, pulling default values from the
        existing schema `old_schema`.
        """
        typestr = '_' + obj.__class__.__name__
        if not hasattr(self, typestr):
            raise ValueError("Unrecognized type for {}".format(typestr))
        # set defaults
        schema = { 'description' : "",
                   'additionalProperties' : False,
                   'required' : True }
        # copy values from old_schema
        for k in schema.keys():
            if k in old_schema:
                schema[k] = old_schema[k]
        # add properties for obj
        schema.update(getattr(self, typestr)(obj, old_schema))
        return schema

    def _dict(self, d, s):
        "Process a dict."
        skema = { 'type' : 'object', 'properties' : { } }
        sprops = s.get('properties', { })
        for key, value in d.items():
            old_props = sprops.get(key, { })
            skema['properties'][key] = self._skemate(value, old_props)
        return skema

    def _list(self, items, s):
        """Process a list.
        
        If `simple_lists` was False in the constructor, then
        do not recurse into lists that have only scalar values.
        """
        skema['type'] = 'array'
        if not self.simple_lists and _scalars(items):
            return skema # no properties
        skema['properties'] = [ ]
        for v in items:
            skema['properties'].append(self._skemate(v)) 
        return skema

    _tuple = _list
    
    def _str(self, v, s):
        "Process a string."
        return self._scalar("string", v, s)

    def _int(self, v, s):
        "Process an integer"
        return self._scalar("integer", v, s)

    def _float(self, v, s):
        "Process a float"
        return self._scalar("float", v, s)
        
    def _scalar(self, typename, val, schema):
        return {'type' : typename,
                'pattern' : '',
                'value' : val # XXX: is this really useful?
        }

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
    sk = Schema(json=json_obj, schema=schema_obj)
    print(json.dumps(sk, indent=4))
    return 0
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
