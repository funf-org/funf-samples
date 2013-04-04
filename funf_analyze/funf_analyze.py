#!/usr/bin/env python
#
# Acknowledgments: Alan Gardner and Cody Sumter
# Contact: funf@media.mit.edu
#
# You can redistribute this and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
# 
# This is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License. If not, see <http://www.gnu.org/licenses/>.
# 
import dbdecrypt
import decrypt
import dbmerge
import viz_gen
import zipfile
from optparse import OptionParser
import sys, os, glob
import shutil

_data_folder = "databases"
_default_merged_file = "merged_data.db"

def unzip_to_folder(zip_files, folder):
    print "Unzipping " + str(zip_files)
    for zip_file in zip_files:
        zip_file_obj = zipfile.ZipFile(zip_file, "r")
        zip_file_obj.extractall(path=folder)

def decrypt_all(files, key=None, password=None):
    key = key or decrypt.key_from_password(password or decrypt.prompt_for_password())
    
    print "Decrypting files"
    failed_files = []
    for file_name in files:
        success = dbdecrypt.decrypt_if_not_db_file(file_name, key, options.extension)
        if not success:
            failed_files.append(file_name)
    if failed_files:
        print "\n\n\nWARNING: Some of the files failed to decrypt!  \nType another password to attempt to decrypt these files, \nor leave blank to continue without decrypting the remaining files.\n"
        another_password = decrypt.prompt_for_password()
        if another_password:
            decrypt_all(failed_files, password=another_password)
            


if __name__ == '__main__':
    usage = "%prog [options] [sqlite_file1.db [sqlite_file2.db...]]"
    description = "Run visualiztion on files contained in zip files. "
    parser = OptionParser(usage="%s\n\n%s" % (usage, description))
    parser.add_option("-i", "--inplace", dest="extension", default=None,
                      help="The extension to rename the original file to.  Will not overwrite file if it already exists. Defaults to '%s'." % decrypt.default_extension,)
    parser.add_option("-k", "--key", dest="key", default=None,
                      help="The DES key used to decrypt the files.  Uses the default hard coded one if one is not supplied.",)
    parser.add_option("-o", "--output", dest="file", default=None,
                      help="Filename to merge all files into.  Will not overwrite a file if it already exists.", metavar="FILE")
    (options, args) = parser.parse_args()
    path = os.path.abspath(os.path.join(sys.argv[0], os.path.pardir))
    merged_data_path = os.path.join(path, options.file or _default_merged_file)
    
    # Default to all zip files in script directory
    zip_files = args
    if len(args) == 0:
        zip_files = glob.glob( os.path.join(path, '*.zip') )
        
    if len(zip_files) == 0:
        print "Missing zip file..."
    else:
        os.chdir(path)
        subfolder = os.path.join(path, _data_folder)
        unzip_to_folder(zip_files, subfolder)
        db_files = glob.glob( os.path.join(subfolder, '*.db') )
        print "Funf data files are encrypted.  Please enter the password you entered on the device to decrypt them."
        decrypt_all(db_files, key=options.key)
        dbmerge.merge(db_files, merged_data_path, overwrite=True)
            
        viz_gen.main()
            
        
        shutil.rmtree(subfolder)
        try:
            shutil.rmtree('kmz')
        except:
            print "No location data"
        files_to_remove = ['bw.png', 'classic.png', 'most_visited.kml']
        
        for file in files_to_remove:
            try:
                os.remove(file)
            except:
                pass
    
    
    # run visualization on merged db file
    