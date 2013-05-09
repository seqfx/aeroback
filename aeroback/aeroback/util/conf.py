import re
#-----------------------------------------------------------------------


#-----------------------------------------------------------------------
class ConfigPreparser:
    """
    Preparses configuration file to make it digestible
    for standrad ConfigParser:

    Leading tabs and spaces are stipped for lines that have '='
    """

    def __init__(self, fp):
        self.fp = fp
        self.i = 0

    def readline(self):
        line = self.fp.readline()
        if line.find('=') != -1:
            line = line.lstrip(' \t')
        #print "{} : {}".format(self.i, line)
        self.i += 1
        return line


#-----------------------------------------------------------------------
class ConfigParserDict(dict):
    """
    Allows standard parser to use same name sections
    by appending a unique ID to each section.
    First section presernves its name, all other duplicates
    will have the format:
        section[N]
    """

    def __init__(self):
        self._sections = {}

    def __setitem__(self, key, val):
        if isinstance(val, dict):
            if key in self._sections:
                sid = self._sections[key]
                self._sections[key] = sid + 1
                key = "{}[{}]".format(key, sid)

            else:
                self._sections[key] = 1
                key = "{}[0]".format(key)

        dict.__setitem__(self, key, val)


#-----------------------------------------------------------------------
def parse_section_name(section):
    """
    Extract section name and corresponding id
        my_name[12] ---> { 'section': my_name, 'id': 12 }
    Regex used:
        anything except for [], followed by [0-9]
    """

    regex = re.compile(r'(?P<section>[^\[\]]*)\[(?P<id>\d+)\]')
    return regex.search(section).groupdict()


#-----------------------------------------------------------------------
class Parser:

    def __init__(self, parser):
        self._parser = parser

    #-------------------------------------------------------------------
    def sections(self):
        '''
        Return set of unique section names
        '''
        sections = set()
        sgs = self._parser.sections()
        for s in sgs:
            sd = parse_section_name(s)
            sname = sd.get('section', None)
            if sname:
                sections.add(sname)
        return sections

    #-------------------------------------------------------------------
    def section_groups(self):
        '''
        Return dictionary of section names and list of ids:
            { sectionA: [0], sectionB: [0, 1, 2], ...}
        '''
        sections = {}
        sgs = self._parser.sections()
        for s in sgs:
            sd = parse_section_name(s)
            sname = sd.get('section', None)
            sid = sd.get('id', None)
            if sname and sid:
                sg = sections.get(sname, None)
                if sg:
                    sections[sname].append(int(sid))
                else:
                    sections[sname] = [int(sid)]
        return sections

    #-------------------------------------------------------------------
    def has_section(self, section, sid = None):
        if sid:
            return self._parser.has_section("{}[{}]".format(section, sid))
        else:
            return self._parser.has_section("{}[0]".format(section))

    #-------------------------------------------------------------------
    def has_option(self, section, option, sid = None):
        if sid:
            return self._parser.has_option("{}[{}]".format(section, sid), option)
        else:
            return self._parser.has_option("{}[0]".format(section), option)

    #-------------------------------------------------------------------
    def validate(self, model):
        '''
        Check config matches model
        Sections must at least have base section like:
            section_name[0]
        '''
        err = 0
        msg = []
        for s in model:
            if not self.has_section(s):
                err = 1
                msg.append("Config has absent section: {}".format(s))
                continue
            for o in model.get(s):
                if not self.has_option(s, o):
                    err = 1
                    msg.append("Config has absent section/option: {}/{}".format(s, o))

        return err, '\n'.join(msg)

    #-------------------------------------------------------------------
    def validate_section(self, model, section, sid = None):
        """
        Check config mathces model at the level of a specific section
        """
        err = 0
        msg = []
        for o in model:
            if not self.has_option(section, o, sid):
                err = 1
                msg.append("Missing section option = {}.{}".format(section, o))

        return err, msg

    #-------------------------------------------------------------------
    def get(self, section, option, sid = None):
        if sid:
            return self._parser.get("{}[{}]".format(section, sid), option)
        else:
            return self._parser.get("{}[0]".format(section), option)

    #-------------------------------------------------------------------
    def getint(self, section, option, sid = None):
        if sid:
            return self._parser.getint("{}[{}]".format(section, sid), option)
        else:
            return self._parser.getint("{}[0]".format(section), option)

    #-------------------------------------------------------------------
    def getfloat(self, section, option, sid = None):
        if sid:
            return self._parser.getfloat("{}[{}]".format(section, sid), option)
        else:
            return self._parser.getfloat("{}[0]".format(section), option)

    #-------------------------------------------------------------------
    def getboolean(self, section, option, sid = None):
        if sid:
            return self._parser.getboolean("{}[{}]".format(section, sid), option)
        else:
            return self._parser.getboolean("{}[0]".format(section), option)


#-----------------------------------------------------------------------
def config_parser_improved(filepath):
    """
    Uses improved config syntax parsing
    """
    parser = None
    err = None
    msg = None

    try:
        with open(filepath) as fp:
            from ConfigParser import SafeConfigParser
            parser = SafeConfigParser(None, ConfigParserDict)
            try:
                parser.readfp(ConfigPreparser(fp))

            except:
                # Critical exception happened
                import sys
                import traceback
                (exc_type, exc_value, exc_traceback) = sys.exc_info()
                traceback.print_exc(file=sys.stdout)

                err = 1
                msg = "Config parser doesn't understand file structure"
    except:
        err = 1
        msg = "Can't open file: {}".format(filepath)

    finally:
        return Parser(parser), err, msg


#-----------------------------------------------------------------------
def UNUSED_preparse_config(filepath, hx):
    """
    Preparses configuration file to make it digestible
    for standrad ConfigParser
    """
    try:
        with open(filepath) as f:
            parsed = []
            line = f.readline()
            while line:
                parsed.append(line)
                line = f.readline()

            ''' Another option via iterator
            for line in iter(f):
                parsed.append(line)
            '''

            return '\n'.join(parsed)

    except:
        hx.err_add("Can't open file", 'filepath', filepath)


#-----------------------------------------------------------------------
