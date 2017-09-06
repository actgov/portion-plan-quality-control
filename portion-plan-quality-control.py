import numpy
import cv2
import os
import ctypes
import shutil
import subprocess
from subprocess import Popen, PIPE
import stat
import shlex
import cv2
from cv2 import cv
import random
import sets


INPUT_PATH = 'C:\Users\control\Documents\Parishes'
OUTPUT_PATH = 'C:\Users\control\Documents\Output'

# FUNCTIONS
def errexit(err, str):
    sys.stderr.write("%s\n" % str)
    sys.exit(err)
    return # actually never return

# http://stackoverflow.com/questions/7853628/how-do-i-find-an-image-contained-within-an-image
# Checks to see if image 1 exists within image 2
# if found, a red box is drawn on image 2 and output jpeg written to JPEG directory
# a confidence is also returned, as to whether or not image 1 was found

def find_image_and_write_jpeg(small_image_path, large_image_path, output_image_path, method_id):
            
            if(method_id==1):
                method = cv.CV_TM_SQDIFF_NORMED
                method_string = 'CV_TM_SQDIFF_NORMED'
            
            # Read the images from the file
            small_image = cv2.imread(small_image_path)
            large_image = cv2.imread(large_image_path)
            
            result = cv2.matchTemplate(small_image, large_image, method)
            
            # We want the minimum squared difference
            mn,_,mnLoc,_ = cv2.minMaxLoc(result)
            
            # Draw the rectangle:
            # Extract the coordinates of our best match
            MPx,MPy = mnLoc
            results_file_object.write(portion_plan + ',' + str(mn) + ',' + method_string + '\n')
            
            # Step 2: Get the size of the template. This is the same size as the match.
            trows,tcols = small_image.shape[:2]
            
            # Step 3: Draw the rectangle on large_image
            cv2.rectangle(large_image, (MPx,MPy),(MPx+tcols,MPy+trows),(0,0,255),2)
            
            cv2.imwrite(output_image_path,large_image)

# Check input path exists
if (os.path.isdir(INPUT_PATH) is False):
    errexit(1, "Specified path: %s not found" % INPUT_PATH)

# Check output directory exists, create if not
if os.path.exists(OUTPUT_PATH):
    os.chmod(OUTPUT_PATH,stat.S_IWRITE)
    shutil.rmtree(OUTPUT_PATH, ignore_errors=True)
os.mkdir(OUTPUT_PATH)

# Check working directory exists, create if not.
working_path = OUTPUT_PATH.replace('Output','Working')  # Has to be a better way to do this.

if os.path.exists(working_path):
    os.chmod(working_path,stat.S_IWRITE)
    shutil.rmtree(working_path, ignore_errors=True)
os.mkdir(working_path)

# Walk directory, Create directory path/name/ext dict
for dirName,subdirList,parish_list in os.walk(INPUT_PATH):
    print('Found directory: %s' % dirName)
    # Make output directory
    parish_string = dirName.split('\\')[len(dirName.split('\\'))-1]
    # Make output directories
    os.mkdir(OUTPUT_PATH + '\\' + parish_string)
    os.mkdir(OUTPUT_PATH + '\\' + parish_string + '\\TIF')
    os.mkdir(OUTPUT_PATH + '\\' + parish_string + '\\JPEG')
    os.mkdir(OUTPUT_PATH + '\\' + parish_string + '\\THRESH')
    results_file_name = OUTPUT_PATH + '\\' + parish_string + '\\' + parish_string + '_log.txt'
    results_file_object = open(results_file_name, 'w+')
    
    for portion_plan in parish_list:
        if ('pdf' in portion_plan):
            print(parish_string + ' ' + portion_plan)
            out_portion_plan_path = OUTPUT_PATH + '\\' + parish_string + '\\TIF\\' + portion_plan
            in_portion_plan_path = INPUT_PATH + '\\' + parish_string + '\\' + portion_plan
            out_portion_plan_path_tif = out_portion_plan_path.replace('.pdf', '.tif').replace(' ','').replace('&','and')
            
            # Extract metadata from the image using gdal
            subprocess.call( ['C:\Program Files (x86)\GDAL\gdalinfo.exe',       \
                              in_portion_plan_path,                             \
                              '>', working_path + "\gdalinfo_output.txt" ], shell=True)
            gdalinfo = open(working_path + "\\gdalinfo_output.txt", 'r').readlines()

            # Exract image size from metadata
            for metadata_line in gdalinfo:
                if ('Size' in metadata_line):
                    size_str = metadata_line
            size = size_str.replace('Size is ','').replace('\n','').replace(' ','').split(',')
            nCols = int(size[0])
            nRows = int(size[1])
            print('Size: ' + str(nCols) + ', ' + str(nRows))

            # Determine scanned DPI for foolscap standard size
            # Standard portion plan dimensions are: (216mm wide x 346mm high) or (8.503937007874017inches wide x 13.622047244094489 high)
            # 1 inch = 25.4mm
            # Standard size: 1754px, 2480px
            # therefore DPI = 1754px/8.503937007874017inches = 1754/(216/25.4) = 206.25740740740738 DPI = 200DPI
            # NB: Stamp size 80mm w x 21mmm h
                        
            # ImageMagik command to covert pdf to tif
            # http://www.imagemagick.org/script/convert.php
            subprocess.call( ['convert',                \
                              '-colorspace', 'rgb',     \
                              '-density', '500',        \
                              in_portion_plan_path,     \
                              '-trim',                  \
                              '-resize', '25%',         \
                              out_portion_plan_path_tif], shell=True)
            
            # ImageMagik command to resize image to orriginal dimensions
            # http://www.imagemagick.org/script/convert.php
            out_portion_plan_path_tif_resize = out_portion_plan_path_tif.replace('.tif', '_resize.tif')
            resize_str = str(nCols) + 'x' + str(nRows)
            z = r'%s!' % resize_str
            
            subprocess.call( ['convert',                        \
                              out_portion_plan_path_tif,        \
                              '-resize',  z,                    \
                              out_portion_plan_path_tif_resize], shell=True)
            
            # import resized image as is. This allows the image type (RGB or Gray) to be determined
            img = cv2.imread(out_portion_plan_path_tif_resize,  \
                             cv2.CV_LOAD_IMAGE_COLOR |          \
                             cv2.CV_LOAD_IMAGE_UNCHANGED) # load image in colour
            
            # Process image based on type
            # Gray
            if(img.dtype == 'uint8'):
                method_id = 1
                small_image_path = 'C:\\PortionPlanQC\\Aaron Portion Plans\\CERTIFY6.tif'
                large_image_path = out_portion_plan_path_tif_resize
                output_image_path = out_portion_plan_path.replace('TIF', 'JPEG').replace('.pdf', '.jpeg')
                find_image_and_write_jpeg(small_image_path, large_image_path, output_image_path, method_id)
            # RGB
            elif(img.dtype == 'uint16'):
                # Delete tif & resized color image, as it was only needed to determine image type
                os.remove(out_portion_plan_path_tif_resize)
                os.remove(out_portion_plan_path_tif)
                # Recreate RGB tif at higher resolution
                subprocess.call( ['convert',                \
                                  '-colorspace', 'rgb',     \
                                  '-density', '500',        \
                                  in_portion_plan_path,     \
                                  '-trim',                  \
                                  '-resize', '50%',         \
                                  out_portion_plan_path_tif], shell=True)
                # Convert to Gray and create threshold image, which is used as mask
                img2 = cv2.imread(out_portion_plan_path_tif,0) # 0 flg loads image in greyscale
                ret,thresh = cv2.threshold(img2,125,255,cv2.THRESH_BINARY)
                #output_image_path = out_portion_plan_path.replace('TIF', 'THRESH').replace('.pdf', '.jpeg')
                #cv2.imwrite(output_image_path,thresh)
                # Load image as RGB into cv2
                img3 = cv2.imread(out_portion_plan_path_tif,         \
                                  cv2.CV_LOAD_IMAGE_COLOR |          \
                                  cv2.CV_LOAD_IMAGE_UNCHANGED)
                # Create mask
                # Iterate through thresh and make all values less than 35 zero.
                row_index = 0
                for row_list_i in thresh:
                    index = 0
                    for value_i in row_list_i:
                        if (value_i > 220):
                            img3[row_index][index][0] = 65535
                            img3[row_index][index][1] = 65535
                            img3[row_index][index][2] = 65535
                            index = index + 1
                        else:
                            index = index + 1
                    row_index = row_index + 1
                
                output_image_path = out_portion_plan_path.replace('TIF', 'THRESH').replace('.pdf', '.tif')
                cv2.imwrite(output_image_path,img3)

                # Analyse blue band for presence of stamp.
                method_id = 1
                small_image_path = 'C:\\PortionPlanQC\\Aaron Portion Plans\\CERTIFY20.tif'
                large_image_path = output_image_path
                output_image_path = out_portion_plan_path.replace('TIF', 'JPEG').replace('.pdf', '.jpeg')
                find_image_and_write_jpeg(small_image_path, large_image_path, output_image_path, method_id)
    results_file_object.close()
















