import os
import pandas
import shutil
from difflib import SequenceMatcher
import jellyfish
# not using jellyfish or shutil, but on here in case needed in future

# ask user what organization needs to be done
organizer = input('What files do you need to organize?\n')
# this variable is the folder that contains all the similar files
comp_folder = f'/Users/nickfreij/Desktop/{organizer}'
directory = f'/Users/nickfreij/Desktop/'
if not os.path.exists(comp_folder):
    os.makedirs(comp_folder)
for path, directories, files in os.walk(directory):
    # checking which files match the user query
    for file in files:
        # checks string differences, rates from 0 to 1
        seq = (SequenceMatcher(None, organizer, file)).ratio()
        if (organizer in file or seq > .75) and ".py" not in file:
            # moving files that match what we care about
            shutil.move(os.path.join(path,file), os.path.join(comp_folder,file)) 
