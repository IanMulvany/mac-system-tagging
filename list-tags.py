import os

tag_delimiter = '&'

def run_and_retrieve_command(command):
    stdout_handle = os.popen(command, "r")
    text = stdout_handle.read()
    return text

def do_mdfind_query(query_term):
    command = """ mdfind "kMDItemFinderComment = '*%s*'" """ % query_term
    result = run_and_retrieve_command(command)
    return result

def do_mdls_query(file):
    command = 'mdls ' + '"' + file + '"'
    result = run_and_retrieve_command(command)
    return result

def get_tagged_files(tag_delimiter):
    text = do_mdfind_query(tag_delimiter)
    files = text.split("\n")
    return files

def get_tags_from_file(file):
    file_md = do_mdls_query(file)
    md_items =  file_md.split("\n") 
    tags = []
    for md_item in md_items:
        if md_item.find("kMDItemFinderComment") > -1:
            tagline = md_item.split("=")[1]
            tagline = tagline.replace('"','')
            tags = tagline.split()
    return tags

def get_files_with_tag(tag):
    result = do_mdfind_query(tag)
    return result

def get_all_tags(tag_delimiter):
    tagged_files = get_tagged_files(tag_delimiter)
    all_tags = []
    for file in tagged_files:
        file_tags = get_tags_from_file(file)
        for tag in file_tags:
            if tag not in all_tags:
                all_tags.append(tag)
    return all_tags

all_tags = get_all_tags(tag_delimiter)
all_tags.sort()
for tag in all_tags:
    print tag, 

result = get_files_with_tag(all_tags[-1])
print result
