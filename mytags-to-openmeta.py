import os 

# get a list of files, and paths to files, that have been tagged
def get_mytagged_files():
    # current tags are denoted with &
    command = """ mdfind "kMDItemFinderComment = '*&*'" """
    stdout_handle = os.popen(command, "r")
    text = stdout_handle.read()
    #
    files = text.split("\n")[:-1] # chop the last item as it's a blank line
    return files

# get the tags for one file
def get_tags_from_file(file):
    command = 'mdls ' + '"' + file + '"'
    stdout_handle = os.popen(command, "r")
    file_md = stdout_handle.read()
    #
    md_items =  file_md.split("\n") 
    tags = []
    for md_item in md_items:
        if md_item.find("kMDItemFinderComment") > -1:
            tagline = md_item.split("=")[1]
            tagline = tagline.replace('"','')
            tags = tagline.split()
    return tags


files = get_mytagged_files()
for file in files:
    newfile = file.replace(" ","\ ")
    file_tags = get_tags_from_file(file)
    for tag in file_tags:
        command = "/Users/ian/personal/python/my-utilities/system-tagging/openmeta -a " + "'" + tag + "'" + " -p " + newfile 
        try:
            os.system(command)
            print "done " + command
        except:
            continue