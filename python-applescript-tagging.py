#!/usr/bin/env python


## Copyright (c) 2009 Tim Scheffler
## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the
## "Software"), to deal in the Software without restriction, including
## without limitation the rights to use, copy, modify, merge, publish,
## distribute, sublicense, and/or sell copies of the Software, and to
## permit persons to whom the Software is furnished to do so, subject to
## the following conditions:

## The above copyright notice and this permission notice shall be
## included in all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
## NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
## LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
## OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
## WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import sys
import types
from itertools import chain
from subprocess import Popen, PIPE

class ParseError(Exception):
    pass

def eat_whitespace(stream):
    x = stream.next()
    while x.isspace():
        x = stream.next()
    return x

def words(txt):
    """Return the words contained in a string.

    Works similar to string.split() but can handle quotation marks.
    (Inside quotation marks the string is not splitted)
    """
    def parse_quote(stream):
        inner = ""
        try:
            while True:
                x = stream.next()
                if x == "\\": # escape sequence
                    inner += stream.next()
                elif x == '"':
                    return inner
                else:
                    inner += x
        except StopIteration:
            return inner
        
    def parse(stream):
        x = eat_whitespace(stream)
        current = ""
        try:
            while True:
                if x.isspace():
                    yield current

                    current = ""
                    x = eat_whitespace(stream)
                    continue
                
                if x == "\\": # escape sequence
                    current += stream.next()
                elif x == '"':
                    inner = parse_quote(stream)
                    current += inner
                else:
                    current += x

                x = stream.next()
                    
        except StopIteration:
            if current:
                yield current

    return list(parse(iter(txt)))

def parse_AS(text):
    """Parse an AppleScript result.

    Input is a text of AS list or string. Lists can be nested.
    Output are python lists or strings.
    """

    def parse(stream):
        x = str(eat_whitespace(stream))
        if x == "{":
            return parse_list(stream)
        elif x == '"':
            return parse_string(stream)
        else:
            raise ParseError("illegal character '%s'" % x)

    def parse_string(stream):
        s = ""
        while True:
            x = str(stream.next())
            if x == "\\":  # escape sequence
                s += str(stream.next())
            elif x == '"':  # end of string
                return s
            else:
                s += x

    def parse_list(stream):
        elems = []
        while True:
            x = str(eat_whitespace(stream))
            if x == ",":
                if not elems:
                    raise ParseError("Illegal ',' in List")
                continue
            elif x == "}":
                return elems
            else:
                elem = parse(chain(x, stream))
                elems.append(elem)

    # ----------------------------------------
    try:
        return parse(iter(text))
    except StopIteration:
        raise ParseError("Unexpected end of input: %s" % text[-40:])


def to_AS(x):
    """Extremely primitive, can only handle strings and lists"""
    if isinstance(x, types.StringType):
        return '"%s"' % escape(x)
    elif isinstance(x, types.ListType):
        return "{%s}" % ",".join(to_AS(y) for y in x)
    else:
        raise RuntimeError('Can not convert "%s" of type "%s" to AppleScript' %
                           (x, str(type(x))))
    
def simple_test():
    test_list = [["moin", "tach"], "auch"]
    if test_list == parse_AS(to_AS(test_list)):
        print "Test ok"
    else:
        print "Test failed"
        

def run_AppleScript(source):
    proc = Popen(["osascript", "-ss", "-"], stdout=PIPE, stdin=PIPE)
    output = proc.communicate(source)

    out = output[0]
    return out
    
def get_spotlightcomments(paths):
    """Return the spotlight comments for the files
    in paths as an array
    """
    ascript = '''
    to GetSpotlightComment(anItem)
            -- return the Spotlight Comment for anItem

            tell application "Finder"
                    try
                            set this_comment to comment of anItem
                    on error
                            set this_comment to ""
                    end try
            end tell
            return this_comment
    end GetSpotlightComment

    set my_files to %s
    set my_res to {}
    repeat with x in my_files
        try
            set y to alias POSIX file x
            set z to GetSpotlightComment(y)
            set end of my_res to {x as String, z}
        on error
        end try
    end repeat

    my_res -- return the final array
    ''' % to_AS(paths)

    return run_AppleScript(ascript)


def set_tags(paths_and_tags):
    ascript = '''
    set nb_errors to {}
    repeat with t in %s
	set thisPath to item 1 of t
	set theTags to item 2 of t
	if length of theTags > 0 then
		tell application "Nifty Box"
			set x to add path thisPath
			try
				x add tags named theTags
			on error
				set end of nb_errors to thisPath
			end try
		end tell
	end if
    end repeat

    nb_errors
    ''' % to_AS(list(paths_and_tags))

    return run_AppleScript(ascript)



def escape(x):
    x = x.replace("\\", "\\\\")
    x = x.replace('"', '\\"')
    return x

# http://code.activestate.com/recipes/105873/
def dirwalk(dir):
    "walk a directory tree, using a generator"
    print 'Entering folder "%s"' % dir
    sys.stdout.flush()
    for f in os.listdir(dir):
        fullpath = os.path.join(dir,f)
        if os.path.isdir(fullpath) and not os.path.islink(fullpath) \
               and not is_bundle(fullpath):
            for x in dirwalk(fullpath):  # recurse into subdir
                yield x
        else:
            yield fullpath

def is_bundle(path):
    return os.path.isdir(path) and "." in os.path.basename(path)

def tags_from_string(txt, tag_prefix):
    for word in words(txt):
        if tag_prefix == "(none)":
            yield word
        else:
            if word.startswith(tag_prefix):
                word = word[len(tag_prefix):]
                yield word


if __name__ == "__main__":
    base_dir, include_subfolders, tag_prefix = sys.argv[1:]

    simple_test()

    dir_func = os.listdir
    print 'Importing from "%s"' % base_dir,
    if include_subfolders == "YES":
        print "including subfolders",
        dir_func = dirwalk
        
    if tag_prefix != "(none)":
        print 'with tag prefix "%s"' % tag_prefix,
    print
    print
    sys.stdout.flush()
    

    array = [os.path.join(base_dir, x) for x in dir_func(base_dir)]

    out = get_spotlightcomments(array)
    pl = parse_AS(out)

    # find tags in the spotlight comment
    tags_for_files = [[path, list(tags_from_string(x, tag_prefix))]
                      for path, x in pl]
    tags_for_files = [[path, [escape(tag) for tag in tags]]
                      for path, tags in tags_for_files
                      if tags != []]

    print "tags_for_files"
    for path, tags in tags_for_files:
        print "path:", path
        print "tags:", ", ".join(tags)

    file_dict = dict(tags_for_files)
    result = set_tags(tags_for_files)
    errors = parse_AS(result)

    retry = 0
    while errors and retry < 3:
        print "There were", len(errors), "errors. Re-trying..."

        rest_files = [[path, file_dict[path]] for path in errors]
        errors = parse_AS(set_tags(rest_files))
        retry += 1

    if retry < 3:
        print "Succesfully imported", len(tags_for_files), "files."
    else:
        print "Incomplete import. There were still", len(errors), "errors:"
        for error in errors:
            print error

    # Raises exceptions:
    #parse_AS("{")
    #parse_AS("{,""}")