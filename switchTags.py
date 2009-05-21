import os

# My tag delimiters
old_delimiter = '#'
new_delimiter = '&'

# Generate a piece of applescript that will take a POSIX file name
# and add spotlight tags to this. 
# We will run this script using the osascript command in Mac OS X.
def gen_add_comment_script(file,new_tags):
    temp_file = '"' + file + '"'
    osa_comment =  '"' + " ".join(new_tags) + '"'
    osascript = """osascript<<END
 tell application "Finder"
	set filePath to POSIX file %s
	set fileComment to %s
	set the_File to filePath as alias
	set comment of the_File to fileComment
end tell 
END""" % (temp_file, osa_comment) 

    return osascript

# get a list of files that include Spotlight comments that
# have the old tag delimiter in them. Split the files into a list
cmd = """ mdfind "kMDItemFinderComment = '*%s*'" """ % old_delimiter
stdout_handle = os.popen(cmd, "r") # redirect stdout
text = stdout_handle.read() # read stdout
files = text.split("\n")

# Run through the list of files.
# for each file do a mdls command and parse out the Spotlight comment as tags.
# In each place where there is a tag with the old delimiter create a tag with the new delimiter.
# Run the applescript to add these new tags to the file.
for file in files:
    cmd = 'mdls ' + '"' + file + '"'
    stdout_handle = os.popen(cmd, "r")
    file_md = stdout_handle.read()
    md_items =  file_md.split("\n")
    print file
    for md_item in md_items:
        if md_item.find("kMDItemFinderComment") > -1:
            tagline = md_item.split("=")[1]
            tagline = tagline.replace('"','')
            new_tagline = tagline.replace(old_delimiter,new_delimiter)
            old_tags = tagline.split()
            new_tags = new_tagline.split()
            script = gen_add_comment_script(file,new_tags)
            os.system(script)
